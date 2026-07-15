#!/usr/bin/env python3
"""
Offline documentation builder and live validator for MEXC and NONKYC exchanges.

Fetches official API documentation, validates live REST/WS behavior, and generates
an offline engineering reference bundle with per-endpoint documented vs observed schemas.

Capabilities:
  * Fetches NonKYC OpenAPI spec + official MEXC docs pages and mirrors
  * Tests public and private REST endpoints with response capture and schema inference
  * Tests representative WS channels (NonKYC: full coverage; MEXC: partial/smoke)
  * Generates per-exchange Markdown docs with request/response field tables
  * Captures live response examples (redacted for sensitive data)
  * Surfaces documented-vs-observed discrepancies and upstream source issues
  * Discovers undocumented response fields from live validation

Coverage notes:
  * NonKYC REST: ~90% live-tested; WS: 12/12 methods tested
  * MEXC Spot REST: ~70% live-tested; WS: limited (protobuf decode not yet implemented)
  * MEXC Futures REST: ~60% live-tested; WS: limited (smoke tests only)
  * Mutating endpoints (order placement, cancellation) are documented from source, not tested live

Goal: An engineer should be able to read the output and program against
the API or WS with minimal need to visit exchange websites.

Usage
-----
python scrape_exchange_docs.py
python scrape_exchange_docs.py --output-dir ./documents
python scrape_exchange_docs.py --skip-validate
python scrape_exchange_docs.py --skip-private-validation
python scrape_exchange_docs.py --strict-quality
python scrape_exchange_docs.py --skip-scrape          # validation only

Environment variables / .env
-----------------------------
NONKYC_API_KEY=...
NONKYC_API_SECRET=...
MEXC_API_KEY=...
MEXC_API_SECRET=...

Optional overrides:
MEXC_SPOT_API_KEY / MEXC_SPOT_API_SECRET
MEXC_FUTURES_API_KEY / MEXC_FUTURES_API_SECRET
NONKYC_ACCESS_KEY / NONKYC_SECRET_KEY

Optional symbols:
MEXC_SPOT_SYMBOL=BTCUSDT
MEXC_FUTURES_SYMBOL=BTC_USDT
NONKYC_SYMBOL=BTC_USDT
NONKYC_WS_SYMBOL=BTC/USDT
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import base64
import contextlib
import copy
import datetime as dt
import hashlib
import hmac
import json
import os
import random
import re
import string
import sys
import textwrap
import time
import traceback
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union
from urllib.parse import quote, urlencode, urlparse

try:
    import httpx
except ImportError as exc:
    raise SystemExit("Missing dependency 'httpx'. pip install httpx") from exc

try:
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit("Missing dependency 'beautifulsoup4'. pip install beautifulsoup4 lxml") from exc

try:
    from markdownify import markdownify as html_to_markdown
except ImportError as exc:
    raise SystemExit("Missing dependency 'markdownify'. pip install markdownify") from exc

try:
    import websockets
except ImportError as exc:
    raise SystemExit("Missing dependency 'websockets'. pip install websockets") from exc

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "4.14.0"
WS_TIMEOUT = 8.0
WS_SUBSCRIBE_WAIT = 5.0
HTTP_TIMEOUT = 30.0
MAX_SAMPLE_SIZE = 500_000  # max bytes for a saved sample

# NonKYC
NONKYC_REST_BASE = "https://api.nonkyc.io/api/v2"
NONKYC_WS_BASE = "wss://api.nonkyc.io"
NONKYC_OPENAPI_URL = "https://api.nonkyc.io/openapi.json"

# MEXC
MEXC_SPOT_REST_BASE = "https://api.mexc.com"
MEXC_SPOT_WS_BASE = "wss://wbs-api.mexc.com/ws"
MEXC_FUTURES_REST_BASE = "https://api.mexc.com"
MEXC_FUTURES_REST_BASE_ALT = "https://contract.mexc.com"
MEXC_FUTURES_WS_BASE = "wss://contract.mexc.com/edge"

# Source URLs
SOURCES = {
    "mexc_spot_v3": [
        {"url": "https://mexcdevelop.github.io/apidocs/spot_v3_en/", "kind": "html"},
        # Official pages — primary source for newer content
        {"url": "https://www.mexc.com/api-docs/spot-v3/introduction", "kind": "html", "tag": "introduction"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/change-log", "kind": "html", "tag": "changelog"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/general-info", "kind": "html", "tag": "general_info"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/market-data-endpoints", "kind": "html", "tag": "market_data"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/subaccount-endpoints", "kind": "html", "tag": "subaccount"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/spot-account-trade", "kind": "html", "tag": "account_trade"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/wallet-endpoints", "kind": "html", "tag": "wallet"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/websocket-market-streams", "kind": "html", "tag": "ws_market"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/websocket-user-data-streams", "kind": "html", "tag": "ws_userdata"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/rebate-endpoints", "kind": "html", "tag": "rebate"},
        {"url": "https://www.mexc.com/api-docs/spot-v3/public-api-definitions", "kind": "html", "tag": "definitions"},
    ],
    "mexc_futures": [
        {"url": "https://mexcdevelop.github.io/apidocs/contract_v1_en/", "kind": "html"},
        {"url": "https://www.mexc.com/api-docs/futures/integration-guide", "kind": "html", "tag": "integration_guide"},
        {"url": "https://www.mexc.com/api-docs/futures/update-log", "kind": "html", "tag": "update_log"},
        {"url": "https://www.mexc.com/api-docs/futures/market-endpoints", "kind": "html", "tag": "market_endpoints"},
        {"url": "https://www.mexc.com/api-docs/futures/account-and-trading-endpoints", "kind": "html", "tag": "account_trading"},
        {"url": "https://www.mexc.com/api-docs/futures/websocket-api", "kind": "html", "tag": "ws_api"},
        {"url": "https://www.mexc.com/api-docs/futures/error-code", "kind": "html", "tag": "error_code"},
    ],
    "nonkyc": [
        {"url": NONKYC_OPENAPI_URL, "kind": "json", "tag": "openapi"},
        {"url": "https://nonkyc.io/", "kind": "html", "tag": "home"},
        {"url": "https://raw.githubusercontent.com/NonKYCExchange/NonKycPythonApiClient/main/nonkyc.py", "kind": "python", "tag": "client_py"},
        {"url": "https://raw.githubusercontent.com/NonKYCExchange/nonkycapinodehmac/main/xApiHmac.js", "kind": "js", "tag": "node_hmac"},
        {"url": "https://raw.githubusercontent.com/NonKYCExchange/websocketapiexample-main/main/wsapiClass.js", "kind": "js", "tag": "ws_example"},
    ],
}

# ---------------------------------------------------------------------------
# Webscrape file mapping: browser-scraped HTML files in ./webscrape/
# Maps (subfolder/filename) -> (exchange_key, tag) for source integration.
# These supplement HTTP-fetched sources with browser-rendered content that
# may include JS-rendered sections blocked by anti-bot on plain HTTP fetches.
# ---------------------------------------------------------------------------

WEBSCRAPE_MAP = {
    # MEXC Spot — maps to same tags as SOURCES entries above
    "mexc/mexc_spot_introduction.html":              ("mexc_spot_v3", "introduction_ws"),
    "mexc/mexc_spot_change_log.html":                ("mexc_spot_v3", "changelog_ws"),
    "mexc/mexc_spot_general_info.html":              ("mexc_spot_v3", "general_info_ws"),
    "mexc/mexc_spot_market_data_endpoints.html":     ("mexc_spot_v3", "market_data_ws"),
    "mexc/mexc_spot_subaccount_endpoints.html":      ("mexc_spot_v3", "subaccount_ws"),
    "mexc/mexc_spot_spot_account_trade.html":        ("mexc_spot_v3", "account_trade_ws"),
    "mexc/mexc_spot_wallet_endpoints.html":          ("mexc_spot_v3", "wallet_ws"),
    "mexc/mexc_spot_websocket_market_streams.html":  ("mexc_spot_v3", "ws_market_ws"),
    "mexc/mexc_spot_websocket_user_data_streams.html": ("mexc_spot_v3", "ws_userdata_ws"),
    "mexc/mexc_spot_rebate_endpoints.html":          ("mexc_spot_v3", "rebate_ws"),
    "mexc/mexc_spot_public_api_definitions.html":    ("mexc_spot_v3", "definitions_ws"),
    "mexc/mexc_spot_faqs.html":                      ("mexc_spot_v3", "faqs_ws"),
    "mexc/mexc_spot_api_intro.html":                 ("mexc_spot_v3", "api_intro_ws"),
    "mexc/mexc_market_data.html":                    ("mexc_spot_v3", "market_overview_ws"),
    "mexc/mexc_ws_streams.html":                     ("mexc_spot_v3", "ws_streams_ws"),
    # NonKYC
    "nonkyc/nonkyc_home.html":                       ("nonkyc", "home_ws"),
    "nonkyc/nonkyc_wsapi.html":                      ("nonkyc", "wsapi_ws"),
    "nonkyc/nonkyc_api_root.html":                   ("nonkyc", "api_root_ws"),
}

# NonKYC REST endpoints — comprehensive list from OpenAPI + project docs + source code
NONKYC_PUBLIC_REST_ENDPOINTS = [
    # Asset endpoints
    {"method": "GET", "path": "/asset/getlist", "tag": "Asset", "summary": "Get list of all assets"},
    {"method": "GET", "path": "/asset/getbyid/{asset_id}", "tag": "Asset", "summary": "Get asset by internal ID", "needs_dynamic_id": "asset"},
    {"method": "GET", "path": "/asset/getbyticker/{ticker}", "tag": "Asset", "summary": "Get asset by ticker symbol", "test_param": "BTC"},
    {"method": "GET", "path": "/asset/info", "tag": "Asset", "summary": "Get asset info (OpenAPI)", "query_params": {"ticker": "BTC"}},
    # Market endpoints
    {"method": "GET", "path": "/market/getlist", "tag": "Market", "summary": "Get list of all markets"},
    {"method": "GET", "path": "/market/getbyid/{market_id}", "tag": "Market", "summary": "Get market by internal ID", "test_param": "643bfeeb5e07bba23a98a981"},
    {"method": "GET", "path": "/market/getbysymbol/{symbol}", "tag": "Market", "summary": "Get market by symbol (e.g. BTC_USDT)", "test_param": "BTC_USDT"},
    {"method": "GET", "path": "/market/getorderbookbysymbol/{symbol}", "tag": "Market", "summary": "Get orderbook by market symbol", "test_param": "BTC_USDT"},
    {"method": "GET", "path": "/market/getorderbookbymarketid/{market_id}", "tag": "Market", "summary": "Get orderbook by market ID", "test_param": "643bfeeb5e07bba23a98a981"},
    {"method": "GET", "path": "/market/info", "tag": "Market", "summary": "Get single market info (OpenAPI)", "query_params": {"symbol": "BTC_USDT"}},
    {"method": "GET", "path": "/market/orderbook", "tag": "Market", "summary": "Get market orderbook (OpenAPI)", "query_params": {"symbol": "BTC_USDT"}},
    {"method": "GET", "path": "/market/trades", "tag": "Market", "summary": "List market trades (OpenAPI)", "query_params": {"symbol": "BTC_USDT"}},
    {"method": "GET", "path": "/market/candles", "tag": "Market", "summary": "Get market candles (OpenAPI)", "query_params": {"symbol": "BTC_USDT", "period": "30"}},
    # Pool endpoints
    {"method": "GET", "path": "/pool/getlist", "tag": "Pool", "summary": "Get list of liquidity pools"},
    {"method": "GET", "path": "/pool/getbyid/{pool_id}", "tag": "Pool", "summary": "Get pool by internal ID", "needs_dynamic_id": "pool"},
    {"method": "GET", "path": "/pool/getbysymbol/{pool_symbol}", "tag": "Pool", "summary": "Get pool by symbol", "needs_dynamic_id": "pool_symbol"},
    {"method": "GET", "path": "/pool/info", "tag": "Pool", "summary": "Get single pool info (OpenAPI)", "query_params": {"symbol": "NKYC_BTC"}},
    {"method": "GET", "path": "/pool/trades", "tag": "Pool", "summary": "List pool trades (OpenAPI)", "query_params": {"symbol": "NKYC_BTC"}},
    # CoinGecko datafeed format
    {"method": "GET", "path": "/tickers", "tag": "CoinGecko", "summary": "Get 24h stats for all markets (CoinGecko format)"},
    {"method": "GET", "path": "/ticker/{symbol}", "tag": "CoinGecko", "summary": "Get 24h stats for single market", "test_param": "BTC_USDT"},
    {"method": "GET", "path": "/pairs", "tag": "CoinGecko", "summary": "Get trading pairs list"},
    {"method": "GET", "path": "/orderbook", "tag": "CoinGecko", "summary": "Get orderbook (CoinGecko format)", "query_params": {"ticker_id": "BTC_USDT", "depth": "10"}},
    {"method": "GET", "path": "/orderbook/snapshot", "tag": "CoinGecko", "summary": "Get orderbook snapshot (Nomics format)", "query_params": {"market": "BTC_USDT"}},
    {"method": "GET", "path": "/historical_trades", "tag": "CoinGecko", "summary": "Get historical spot trades", "query_params": {"ticker_id": "BTC_USDT", "limit": "5"}},
    {"method": "GET", "path": "/historical_pooltrades", "tag": "CoinGecko", "summary": "Get historical pool trades", "query_params": {"ticker_id": "BTC_USDT", "limit": "5"}},
    # CMC datafeed format
    {"method": "GET", "path": "/summary", "tag": "CMC", "summary": "Market summary (CMC format)"},
    {"method": "GET", "path": "/cmcassets", "tag": "CMC", "summary": "CMC asset list"},
    {"method": "GET", "path": "/cmctickers", "tag": "CMC", "summary": "CMC ticker data"},
    {"method": "GET", "path": "/cmcorderbook/{symbol}", "tag": "CMC", "summary": "CMC orderbook by symbol", "test_param": "BTC_USDT"},
    {"method": "GET", "path": "/cmctrades/{symbol}", "tag": "CMC", "summary": "CMC trades by symbol", "test_param": "BTC_USDT"},
    # Nomics format
    {"method": "GET", "path": "/info", "tag": "Nomics", "summary": "Exchange info (Nomics format)"},
    {"method": "GET", "path": "/markets", "tag": "Nomics", "summary": "Markets list (Nomics format)"},
    {"method": "GET", "path": "/trades", "tag": "Nomics", "summary": "Trades (Nomics format)", "query_params": {"market": "BTC_USDT"}},
    # Utility
    {"method": "GET", "path": "/time", "tag": "Utility", "summary": "Get server time"},
]

NONKYC_PRIVATE_REST_ENDPOINTS = [
    {"method": "GET", "path": "/balances", "tag": "Account", "summary": "Get all account balances"},
    {"method": "GET", "path": "/getdepositaddress/{ticker}", "tag": "Account", "summary": "Get deposit address for asset", "test_param": "BTC-MAIN"},
    {"method": "GET", "path": "/getdeposits", "tag": "Account", "summary": "Get deposit history"},
    {"method": "GET", "path": "/getwithdrawals", "tag": "Account", "summary": "Get withdrawal history"},
    {"method": "GET", "path": "/getorder/{order_id}", "tag": "Account", "summary": "Get order by ID"},
    {"method": "GET", "path": "/getorders", "tag": "Account", "summary": "Get orders list", "query_params": {"limit": "5"}},
    {"method": "GET", "path": "/account/orders", "tag": "Account", "summary": "List account orders (OpenAPI alias for /getorders)", "query_params": {"limit": "5"}},
    {"method": "GET", "path": "/gettrades", "tag": "Account", "summary": "Get trade history", "query_params": {"limit": "5"}},
    {"method": "GET", "path": "/account/trades", "tag": "Account", "summary": "List account trades (OpenAPI alias for /gettrades)", "query_params": {"limit": "5"}},
    {"method": "GET", "path": "/gettradessince", "tag": "Account", "summary": "Get trades since timestamp", "query_params": {"since": "0", "limit": "5"}},
    {"method": "GET", "path": "/getpooltrades", "tag": "Account", "summary": "Get pool trade history", "query_params": {"limit": "5"}},
    {"method": "GET", "path": "/getpooltradessince", "tag": "Account", "summary": "Get pool trades since timestamp", "query_params": {"since": "0", "limit": "5"}},
    # POST endpoints - not tested with live orders to avoid placing real trades
    # but documented with request/response schemas from OpenAPI
]

NONKYC_POST_ENDPOINTS_SCHEMA_ONLY = [
    {"method": "POST", "path": "/createorder", "tag": "Account", "summary": "Create a new order",
     "request_body": {
         "userProvidedId": {"type": "string", "required": False, "description": "Optional user-defined ID (UUIDv4 generated if omitted)"},
         "symbol": {"type": "string", "required": True, "description": "Market symbol, two tickers joined with '_'. e.g. 'XRG_LTC'"},
         "side": {"type": "string", "required": True, "description": "Order side: 'sell' or 'buy'", "enum": ["sell", "buy"]},
         "type": {"type": "string", "required": False, "description": "Order type: 'limit' or 'market'", "enum": ["limit", "market"], "default": "limit"},
         "quantity": {"type": "string", "required": True, "description": "Quantity of the base asset (string precision)"},
         "price": {"type": "string", "required": False, "description": "Price in quote asset. Required for limit orders"},
         "strictValidate": {"type": "boolean", "required": False, "description": "If true, reject if precision exceeds allowed decimals instead of truncating", "default": False},
     }},
    {"method": "POST", "path": "/cancelorder", "tag": "Account", "summary": "Cancel an open order",
     "request_body": {
         "id": {"type": "string", "required": True, "description": "NonKYC order ID to cancel"},
     }},
    {"method": "POST", "path": "/cancelallorders", "tag": "Account", "summary": "Cancel all open orders in a market",
     "request_body": {
         "symbol": {"type": "string", "required": True, "description": "Market symbol, e.g. 'BTC_USDT'"},
         "side": {"type": "string", "required": False, "description": "Filter by side: 'sell', 'buy', or 'all'", "enum": ["sell", "buy", "all"], "default": "all"},
     }},
    {"method": "POST", "path": "/createwithdrawal", "tag": "Account", "summary": "Create a withdrawal request",
     "request_body": {
         "ticker": {"type": "string", "required": True, "description": "Asset ticker to withdraw"},
         "address": {"type": "string", "required": True, "description": "Destination address"},
         "paymentId": {"type": "string", "required": False, "description": "Payment ID / memo if required by network"},
         "amount": {"type": "string", "required": True, "description": "Amount to withdraw (string precision)"},
         "includeFee": {"type": "boolean", "required": False, "description": "If true, fee is deducted from amount", "default": False},
     }},
]

# NonKYC WS channels to test
NONKYC_WS_PUBLIC_CHANNELS = [
    {"method": "getMarket", "params": {"symbol": "BTC/USDT"}, "description": "Get single market info", "expect_result": True},
    {"method": "getMarkets", "params": {}, "description": "Get all markets list", "expect_result": True},
    {"method": "getAsset", "params": {"ticker": "BTC"}, "description": "Get single asset info", "expect_result": True},
    {"method": "getAssets", "params": {}, "description": "Get all assets list", "expect_result": True},
    {"method": "getTrades", "params": {"symbol": "BTC/USDT", "limit": 5, "sort": "DESC"}, "description": "Get trade history", "expect_result": True},
]

NONKYC_WS_SUBSCRIPTIONS = [
    {"subscribe": "subscribeTicker", "params": {"symbol": "BTC/USDT"}, "notification_methods": ["ticker"],
     "unsubscribe": "unsubscribeTicker", "description": "Real-time ticker updates"},
    {"subscribe": "subscribeOrderbook", "params": {"symbol": "BTC/USDT", "limit": 10}, "notification_methods": ["snapshotOrderbook", "updateOrderbook"],
     "unsubscribe": "unsubscribeOrderbook", "description": "Orderbook snapshot + incremental updates"},
    {"subscribe": "subscribeTrades", "params": {"symbol": "BTC/USDT"}, "notification_methods": ["snapshotTrades", "updateTrades"],
     "unsubscribe": "unsubscribeTrades", "description": "Trade snapshot + live trade updates"},
    {"subscribe": "subscribeCandles", "params": {"symbol": "BTC/USDT", "period": 30}, "notification_methods": ["snapshotCandles", "updateCandles"],
     "unsubscribe": "unsubscribeCandles", "description": "Candlestick snapshot + updates"},
]

NONKYC_WS_PRIVATE_CHANNELS = [
    {"method": "getTradingBalance", "params": {}, "description": "Get all account balances", "expect_result": True},
    {"method": "getOrders", "params": {}, "description": "Get active orders", "expect_result": True},
]

NONKYC_WS_PRIVATE_SUBSCRIPTIONS = [
    {"subscribe": "subscribeReports", "params": {}, "notification_methods": ["activeOrders", "report"],
     "description": "Order lifecycle events (new, filled, cancelled)"},
]

# Known NonKYC error codes (from WS docs + observations)
NONKYC_ERROR_CODES = {
    20001: "Insufficient funds",
    20002: "Order not found",
    20003: "Invalid symbol",
    20004: "Market paused",
    20005: "Below minimum quantity",
    20006: "Below minimum quote value",
    20007: "Price exceeds allowed range",
    20008: "Strict validation failed (precision)",
    20010: "Must use more specific ticker (e.g. BTC-MAIN instead of BTC)",
    500: "Internal Server Error",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_START_TIME = time.monotonic()
_LOG_LINES: list[str] = []

DOTENV_VALUES: dict[str, str] = {}
DOTENV_PATH: Optional[Path] = None
ENV_BOOTSTRAP_LOGS: list[str] = []


def log(message: str) -> None:
    elapsed = time.monotonic() - _START_TIME
    line = f"[{dt.datetime.now():%H:%M:%S} + {elapsed:7.1f}s] {message}"
    _LOG_LINES.append(line)
    print(line, flush=True)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("_") or "index"


def make_test_id(exchange: str, transport: str, permission: str, method: str, path: str) -> str:
    """Generate globally unique test IDs from the full path, not just last segment."""
    # Normalize path: strip common prefixes (longest first to avoid partial matches)
    clean = re.sub(r"^/api/v[0-9]+/private/|^/api/v[0-9]+/contract/|^/api/v[0-9]+/", "", path)
    clean = clean.strip("/")
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", clean).strip("_").lower()
    return f"{exchange}_{transport}_{permission}_{clean}"


def pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, default=str)


def truncate_str(text: str, limit: int = 500) -> str:
    text = text.replace("\r", "")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def truncate_json_for_display(data: Any, max_array_items: int = 3) -> Any:
    """Recursively truncate arrays in JSON data for documentation display."""
    if isinstance(data, list):
        items = [truncate_json_for_display(item, max_array_items) for item in data[:max_array_items]]
        if len(data) > max_array_items:
            items.append(f"... ({len(data) - max_array_items} more items, {len(data)} total)")
        return items
    elif isinstance(data, dict):
        return {k: truncate_json_for_display(v, max_array_items) for k, v in data.items()}
    return data


def normalize_blank_lines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(data), encoding="utf-8")


def looks_like_html(text: str) -> bool:
    prefix = text[:500].lower()
    return "<html" in prefix or "<!doctype html" in prefix or "<body" in prefix


def now_ms() -> int:
    return int(time.time() * 1000)


# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------

def parse_dotenv_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] in {'"', "'"} and value[-1:] == value[0]:
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value).strip()
        values[key] = value
    return values


def initialize_env_source(explicit: str = "") -> Optional[Path]:
    global DOTENV_VALUES, DOTENV_PATH
    if DOTENV_PATH is not None:
        return DOTENV_PATH
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    else:
        candidates.append(Path.cwd() / ".env")
        candidates.append(Path(__file__).resolve().parent / ".env")
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.is_file():
            try:
                text = candidate.read_text(encoding="utf-8")
                DOTENV_VALUES = parse_dotenv_text(text)
                DOTENV_PATH = candidate
                ENV_BOOTSTRAP_LOGS.append(f"Loaded .env file: {candidate}")
                return DOTENV_PATH
            except Exception as exc:
                ENV_BOOTSTRAP_LOGS.append(f"Failed to read .env file {candidate}: {exc}")
    ENV_BOOTSTRAP_LOGS.append("No .env file found; using inherited environment variables only")
    return None


def env(name: str, fallback: str = "") -> str:
    if name in DOTENV_VALUES:
        return DOTENV_VALUES[name].strip()
    return os.getenv(name, fallback).strip()


def env_has_value(name: str) -> bool:
    return bool(env(name))


# ---------------------------------------------------------------------------
# Schema inference
# ---------------------------------------------------------------------------

def infer_json_schema(value: Any, path: str = "$", depth: int = 0, max_depth: int = 6) -> dict:
    """Infer a JSON schema from a sample value, with types and examples."""
    if depth > max_depth:
        return {"type": "any", "example": "..."}

    if value is None:
        return {"type": "null", "example": None}
    elif isinstance(value, bool):
        return {"type": "boolean", "example": value}
    elif isinstance(value, int):
        return {"type": "integer", "example": value}
    elif isinstance(value, float):
        return {"type": "number", "example": value}
    elif isinstance(value, str):
        # Detect string subtypes
        if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
            return {"type": "string (ISO8601 datetime)", "example": value}
        elif re.match(r"^-?\d+\.\d+$", value):
            return {"type": "string (decimal number)", "example": value}
        elif re.match(r"^[0-9a-f]{24}$", value):
            return {"type": "string (ObjectId)", "example": value}
        elif re.match(r"^[0-9a-f]{8}-", value):
            return {"type": "string (UUID)", "example": value}
        elif len(value) > 200:
            return {"type": "string", "example": value[:80] + "..."}
        return {"type": "string", "example": value}
    elif isinstance(value, list):
        if len(value) == 0:
            return {"type": "array", "items": {"type": "unknown"}, "example": []}
        # Union schema across first few items to capture optional fields
        sample_items = value[:min(5, len(value))]
        base_schema = infer_json_schema(sample_items[0], f"{path}[0]", depth + 1, max_depth)
        if base_schema.get("type") == "object" and "properties" in base_schema:
            for idx, item in enumerate(sample_items[1:], 1):
                extra = infer_json_schema(item, f"{path}[{idx}]", depth + 1, max_depth)
                if extra.get("type") == "object" and "properties" in extra:
                    for k, v in extra["properties"].items():
                        if k not in base_schema["properties"]:
                            base_schema["properties"][k] = v
        return {"type": "array", "items": base_schema, "length": len(value)}
    elif isinstance(value, dict):
        properties = {}
        for k, v in value.items():
            properties[k] = infer_json_schema(v, f"{path}.{k}", depth + 1, max_depth)
        return {"type": "object", "properties": properties}
    else:
        return {"type": str(type(value).__name__), "example": str(value)}


def render_schema_markdown(schema: dict, indent: int = 0, max_properties: int = 60) -> str:
    """Render an inferred JSON schema as markdown documentation."""
    lines = []
    prefix = "  " * indent

    if schema.get("type") == "object" and "properties" in schema:
        props = schema["properties"]
        count = 0
        for name, prop in props.items():
            if count >= max_properties:
                lines.append(f"{prefix}| ... | ... | ({len(props) - count} more fields) |")
                break
            prop_type = prop.get("type", "unknown")
            example = prop.get("example", "")
            if prop_type == "object" and "properties" in prop:
                nested_count = len(prop["properties"])
                lines.append(f"{prefix}| `{name}` | object ({nested_count} fields) | see below |")
            elif prop_type == "array":
                item_type = prop.get("items", {}).get("type", "unknown")
                length = prop.get("length", "?")
                lines.append(f"{prefix}| `{name}` | array of {item_type} | {length} items |")
            else:
                ex_str = str(example) if example is not None else "null"
                # Redact sensitive field examples
                if name.lower() in SENSITIVE_KEYS or name.lower() in ACCOUNT_SENSITIVE_KEYS:
                    ex_str = "<redacted>"
                if len(ex_str) > 60:
                    ex_str = ex_str[:57] + "..."
                # Escape pipes in markdown
                ex_str = ex_str.replace("|", "\\|")
                lines.append(f"{prefix}| `{name}` | {prop_type} | `{ex_str}` |")
            count += 1

        # Recursively render nested objects
        for name, prop in props.items():
            if prop.get("type") == "object" and "properties" in prop:
                lines.append(f"\n{prefix}**`{name}`** (nested object):\n")
                lines.append(f"{prefix}| Field | Type | Example |")
                lines.append(f"{prefix}| --- | --- | --- |")
                lines.append(render_schema_markdown(prop, indent + 1))
            elif prop.get("type") == "array" and prop.get("items", {}).get("type") == "object":
                lines.append(f"\n{prefix}**`{name}[]`** (array item schema):\n")
                lines.append(f"{prefix}| Field | Type | Example |")
                lines.append(f"{prefix}| --- | --- | --- |")
                lines.append(render_schema_markdown(prop["items"], indent + 1))

    return "\n".join(lines)


def collect_field_names(value: Any, out: Optional[set] = None) -> set:
    if out is None:
        out = set()
    if isinstance(value, dict):
        for k, v in value.items():
            out.add(k)
            collect_field_names(v, out)
    elif isinstance(value, list):
        for item in value:
            collect_field_names(item, out)
    return out


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    name: str
    status: str  # pass, fail, warn, skip
    transport: str  # rest, ws
    auth_method: str = ""
    http_status: int = 0
    latency_ms: int = 0
    target: str = ""
    details: str = ""
    sample_path: str = ""
    observed_fields: set = field(default_factory=set)
    response_schema: dict = field(default_factory=dict)
    response_example: Any = None


@dataclass
class EndpointDoc:
    """Complete documentation for a single REST endpoint."""
    method: str
    path: str
    full_url: str
    tag: str
    summary: str
    permission: str  # "public" or "private"
    request_params: list = field(default_factory=list)
    request_body: dict = field(default_factory=dict)
    response_schema: dict = field(default_factory=dict)
    response_example: Any = None
    response_example_truncated: Any = None
    error_schema: dict = field(default_factory=dict)
    # Source-documented response (from official docs, not live test)
    documented_response_fields: list = field(default_factory=list)  # [{name, type, description}]
    documented_response_example: str = ""  # JSON string from source docs
    # Observed error when live test returned non-success
    observed_error: Any = None
    notes: list = field(default_factory=list)
    explicit_no_params: bool = False
    tested: bool = False
    test_status: str = ""
    test_latency_ms: int = 0
    http_status: int = 0


@dataclass
class WsMethodDoc:
    """Documentation for a single WS method or subscription."""
    method_name: str
    kind: str  # "request", "subscription", "notification"
    permission: str  # "public" or "private"
    description: str
    params: dict = field(default_factory=dict)
    subscribe_method: str = ""
    unsubscribe_method: str = ""
    notification_methods: list = field(default_factory=list)
    response_schema: dict = field(default_factory=dict)
    response_example: Any = None
    notification_schemas: dict = field(default_factory=dict)
    notification_examples: dict = field(default_factory=dict)
    tested: bool = False
    test_status: str = ""
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@dataclass
class SpotAuth:
    api_key: str
    api_secret: str
    source: str = ""

@dataclass
class FuturesAuth:
    api_key: str
    api_secret: str
    source: str = ""

@dataclass
class NonKycAuth:
    api_key: str
    api_secret: str
    source: str = ""

@dataclass
class AuthConfig:
    mexc_spot: Optional[SpotAuth]
    mexc_futures: Optional[FuturesAuth]
    nonkyc: Optional[NonKycAuth]
    notes: list[str] = field(default_factory=list)


def resolve_credential_pair(
    section_label: str,
    primary_key_name: str,
    primary_secret_name: str,
    fallback_key_name: str = "",
    fallback_secret_name: str = "",
) -> tuple[Optional[str], Optional[str], str, list[str]]:
    notes = []
    primary_key = env(primary_key_name)
    primary_secret = env(primary_secret_name)
    if primary_key and primary_secret:
        return primary_key, primary_secret, f"{primary_key_name}/{primary_secret_name}", notes
    if primary_key or primary_secret:
        missing = primary_secret_name if primary_key else primary_key_name
        notes.append(f"{section_label}: disabled because {missing} is missing")
        return None, None, "", notes
    if fallback_key_name:
        fb_key = env(fallback_key_name)
        fb_secret = env(fallback_secret_name)
        if fb_key and fb_secret:
            return fb_key, fb_secret, f"{fallback_key_name}/{fallback_secret_name}", notes
        if fb_key or fb_secret:
            missing = fallback_secret_name if fb_key else fallback_key_name
            notes.append(f"{section_label}: disabled because {missing} is missing")
    return None, None, "", notes


def load_auth_config() -> AuthConfig:
    notes = []
    # MEXC Spot
    spot_key, spot_secret, spot_src, spot_notes = resolve_credential_pair(
        "MEXC spot", "MEXC_SPOT_API_KEY", "MEXC_SPOT_API_SECRET", "MEXC_API_KEY", "MEXC_API_SECRET"
    )
    notes.extend(spot_notes)
    spot_auth = SpotAuth(spot_key, spot_secret, spot_src) if spot_key else None

    # MEXC Futures
    fut_key, fut_secret, fut_src, fut_notes = resolve_credential_pair(
        "MEXC futures", "MEXC_FUTURES_API_KEY", "MEXC_FUTURES_API_SECRET", "MEXC_API_KEY", "MEXC_API_SECRET"
    )
    notes.extend(fut_notes)
    fut_auth = FuturesAuth(fut_key, fut_secret, fut_src) if fut_key else None

    # NonKYC
    nk_key, nk_secret, nk_src, nk_notes = resolve_credential_pair(
        "NonKYC", "NONKYC_API_KEY", "NONKYC_API_SECRET", "NONKYC_ACCESS_KEY", "NONKYC_SECRET_KEY"
    )
    notes.extend(nk_notes)
    nk_auth = NonKycAuth(nk_key, nk_secret, nk_src) if nk_key else None

    return AuthConfig(mexc_spot=spot_auth, mexc_futures=fut_auth, nonkyc=nk_auth, notes=notes)


# ---------------------------------------------------------------------------
# Signing functions
# ---------------------------------------------------------------------------

def sign_mexc_spot(secret: str, params: dict) -> str:
    query_string = urlencode(params)
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()


def mexc_spot_signed_params(extra: Optional[dict], secret: str) -> dict:
    params = dict(extra or {})
    params["timestamp"] = now_ms()
    params["recvWindow"] = 10000
    params["signature"] = sign_mexc_spot(secret, params)
    return params


def mexc_spot_header(api_key: str) -> dict:
    return {"X-MEXC-APIKEY": api_key, "Content-Type": "application/json"}


def sign_mexc_futures(secret: str, api_key: str, req_time: str, request_param: str) -> str:
    sign_str = api_key + req_time + request_param
    return hmac.new(secret.encode(), sign_str.encode(), hashlib.sha256).hexdigest()


def mexc_futures_headers(auth: FuturesAuth, params: Optional[dict] = None) -> dict:
    req_time = str(now_ms())
    request_param = ""
    if params:
        sorted_items = sorted(params.items(), key=lambda x: x[0])
        request_param = "&".join(f"{k}={v}" for k, v in sorted_items)
    sig = sign_mexc_futures(auth.api_secret, auth.api_key, req_time, request_param)
    return {
        "ApiKey": auth.api_key,
        "Request-Time": req_time,
        "Signature": sig,
        "Content-Type": "application/json",
    }


def sign_nonkyc(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def nonkyc_rest_headers(auth: NonKycAuth, url: str, body: str = "") -> dict:
    nonce = str(now_ms())
    payload = auth.api_key + url + body + nonce
    sig = sign_nonkyc(auth.api_secret, payload)
    return {
        "X-API-KEY": auth.api_key,
        "X-API-NONCE": nonce,
        "X-API-SIGN": sig,
        "Content-Type": "application/json",
    }


def nonkyc_ws_login_message(auth: NonKycAuth, request_id: int = 100) -> dict:
    nonce = "".join(random.choices(string.ascii_letters + string.digits, k=15))
    sig = hmac.new(auth.api_secret.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return {
        "method": "login",
        "params": {
            "algo": "HS256",
            "pKey": auth.api_key,
            "nonce": nonce,
            "signature": sig,
        },
        "id": request_id,
    }


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
    timeout: float = HTTP_TIMEOUT,
) -> tuple[int, Any, int, str]:
    """Returns (http_status, parsed_data, latency_ms, error_str)."""
    log_msg = f"HTTP request: {method} {url}"
    if headers and ("X-API-KEY" in headers or "X-MEXC-APIKEY" in headers or "ApiKey" in headers):
        log_msg += " (auth=yes)"
    log(log_msg)
    t0 = time.monotonic()
    try:
        response = await client.request(
            method, url, headers=headers, params=params, json=json_body, timeout=timeout
        )
        latency = int((time.monotonic() - t0) * 1000)
        log(f"HTTP response: {method} {url} -> status={response.status_code}, latency={latency}ms")

        text = response.text
        if not text.strip():
            return response.status_code, None, latency, ""
        try:
            data = response.json()
        except Exception:
            data = text
        return response.status_code, data, latency, ""
    except Exception as exc:
        latency = int((time.monotonic() - t0) * 1000)
        return 0, None, latency, str(exc)


# ---------------------------------------------------------------------------
# Sensitive data redaction
# ---------------------------------------------------------------------------

SENSITIVE_KEYS = {
    # Secrets and credentials
    "listenkey", "apikey", "secretkey", "signature",
    # Wallet addresses
    "address", "addresstag", "memo", "depositaddress", "withdrawaddress", "coin_address",
    # Account-sensitive data (IDs)
    "uid", "userprovidedid", "clientorderid", "newclientorderid", "origclientorderid",
}

# Fields where we redact the VALUE but keep the key visible (for schema documentation)
ACCOUNT_SENSITIVE_KEYS = {
    "free", "locked", "balance", "available", "availablebalance", "frozenbalance",
    "cashbalance", "equity", "unrealized", "bonus", "positionmargin",
    "amount", "quantity", "vol", "holdvol", "frozenvol", "closevol",
    "transactionid", "txid", "tranid", "orderid", "id",
    "availablecash", "availableopen", "debtamount",
    # Missing from prior versions — confirmed leaking
    "fee", "held", "pending", "frozen", "confirmationnumber",
}

SENSITIVE_URL_PARAMS = {"listenKey", "apiKey", "secretKey", "signature"}


def redact_value(data: Any) -> Any:
    """Recursively redact sensitive fields from data structures. Case-insensitive key matching."""
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            k_lower = k.lower()
            if k_lower in SENSITIVE_KEYS:
                out[k] = "<redacted>"
            elif k_lower in ACCOUNT_SENSITIVE_KEYS and isinstance(v, (str, int, float)):
                out[k] = "<redacted>"
            else:
                out[k] = redact_value(v)
        return out
    if isinstance(data, list):
        return [redact_value(item) for item in data]
    return data


def redact_url(url: str) -> str:
    """Redact sensitive query parameters from URLs."""
    for param in SENSITIVE_URL_PARAMS:
        url = re.sub(rf'({param})=[^&\s]+', rf'\1=<redacted>', url)
    return url


def save_sample(output_dir: Path, name: str, payload: Any, suffix: str = ".json") -> str:
    sample_dir = output_dir / "_raw" / "response_samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    path = sample_dir / f"{name}{suffix}"
    # Redact sensitive fields before persisting
    redacted = redact_value(payload) if not isinstance(payload, str) else payload
    text = pretty_json(redacted) if not isinstance(redacted, str) else redacted
    if len(text) > MAX_SAMPLE_SIZE:
        text = text[:MAX_SAMPLE_SIZE] + "\n... (truncated)\n"
    path.write_text(text, encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# WebSocket helpers
# ---------------------------------------------------------------------------

async def ws_recv_text(ws, timeout: float = WS_TIMEOUT) -> Optional[str]:
    try:
        msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
        if isinstance(msg, bytes):
            try:
                return msg.decode("utf-8")
            except Exception:
                return None
        return msg
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


async def ws_collect_messages(ws, duration: float, max_messages: int = 50) -> list[dict]:
    """Collect WS messages for a duration, parsing JSON."""
    messages = []
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline and len(messages) < max_messages:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        raw = await ws_recv_text(ws, timeout=min(remaining, 2.0))
        if raw is None:
            continue
        try:
            msg = json.loads(raw)
            messages.append(msg)
        except json.JSONDecodeError:
            messages.append({"_raw": raw})
    return messages


# ---------------------------------------------------------------------------
# Source fetching
# ---------------------------------------------------------------------------

async def fetch_sources(client: httpx.AsyncClient, output_dir: Path) -> dict:
    """Fetch all documentation sources and save raw copies."""
    manifest = {}
    sources_dir = output_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    for exchange, source_list in SOURCES.items():
        manifest[exchange] = []
        for src in source_list:
            url = src["url"]
            kind = src["kind"]
            tag = src.get("tag", slugify(url.split("/")[-1]))
            log(f"Fetching source for {exchange}/{tag}: {url}")

            try:
                response = await client.get(url, timeout=HTTP_TIMEOUT, follow_redirects=True)
                status = response.status_code
                text = response.text
                fetched_at = dt.datetime.utcnow().isoformat() + "Z"

                if status == 200 and text.strip():
                    # Save raw source
                    if kind == "json":
                        fname = f"{exchange}_{tag}.json"
                        save_text(sources_dir / fname, text)
                    elif kind == "html":
                        fname = f"{exchange}_{tag}.md"
                        # Convert HTML to markdown
                        md = html_to_markdown(text) if looks_like_html(text) else text
                        save_text(sources_dir / fname, f"_Source: {url}_\n\n_Fetched: {fetched_at}_\n\n{md}")
                    else:
                        fname = f"{exchange}_{tag}.{'py' if kind == 'python' else kind}"
                        save_text(sources_dir / fname, text)

                    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    manifest[exchange].append({
                        "url": url, "kind": kind, "tag": tag, "status": status,
                        "fetched_at": fetched_at, "file": fname, "size": len(text),
                        "sha256": content_hash,
                    })
                    log(f"  OK: {len(text)} bytes -> {fname}")
                else:
                    log(f"  WARN: status={status}, empty={not text.strip()}")
                    manifest[exchange].append({
                        "url": url, "kind": kind, "tag": tag, "status": status,
                        "fetched_at": dt.datetime.utcnow().isoformat() + "Z", "error": f"status {status}",
                    })
            except Exception as exc:
                log(f"  ERROR: {exc}")
                manifest[exchange].append({
                    "url": url, "kind": kind, "tag": tag, "status": 0,
                    "error": str(exc),
                })

    return manifest


def load_webscrape_sources(webscrape_dir: Path, output_dir: Path, manifest: dict) -> dict:
    """Load browser-scraped HTML/JSON files from ./webscrape as supplementary sources.

    These files are produced by an external browser-based scraper and contain
    JS-rendered content that plain HTTP fetches may miss due to anti-bot protection.
    They are added ALONGSIDE existing HTTP-fetched sources, not replacing them.
    """
    if not webscrape_dir.exists():
        log(f"No webscrape directory found at {webscrape_dir} — skipping browser-scraped sources")
        return manifest

    sources_dir = output_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    loaded_count = 0

    for rel_path, (exchange, tag) in WEBSCRAPE_MAP.items():
        fpath = webscrape_dir / rel_path
        if not fpath.exists():
            continue

        try:
            raw = fpath.read_text(encoding="utf-8", errors="replace")
            if not raw.strip():
                log(f"  SKIP (empty): webscrape/{rel_path}")
                continue

            fetched_at = dt.datetime.utcnow().isoformat() + "Z"
            content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

            # Convert HTML to markdown (same as HTTP-fetched sources)
            if fpath.suffix.lower() in (".html", ".htm"):
                md = html_to_markdown(raw) if looks_like_html(raw) else raw
                fname = f"{exchange}_{tag}.md"
                save_text(sources_dir / fname,
                          f"_Source: webscrape/{rel_path} (browser-rendered)_\n\n"
                          f"_Loaded: {fetched_at}_\n\n{md}")
            elif fpath.suffix.lower() == ".json":
                fname = f"{exchange}_{tag}.json"
                save_text(sources_dir / fname, raw)
            else:
                fname = f"{exchange}_{tag}{fpath.suffix}"
                save_text(sources_dir / fname, raw)

            # Add to manifest under the correct exchange
            if exchange not in manifest:
                manifest[exchange] = []
            manifest[exchange].append({
                "url": f"webscrape/{rel_path}",
                "kind": "html" if fpath.suffix.lower() in (".html", ".htm") else fpath.suffix.lstrip("."),
                "tag": tag,
                "status": 200,
                "fetched_at": fetched_at,
                "file": fname,
                "size": len(raw),
                "sha256": content_hash,
                "provenance": "webscrape",
            })
            loaded_count += 1
            log(f"  OK (webscrape): {len(raw)} bytes -> {fname}")

        except Exception as exc:
            log(f"  ERROR loading webscrape/{rel_path}: {exc}")

    # Also load any JSON files in webscrape subdirs not in the map
    for json_file in sorted(webscrape_dir.rglob("*.json")):
        rel = str(json_file.relative_to(webscrape_dir))
        if rel in WEBSCRAPE_MAP:
            continue  # already handled
        # Infer exchange from parent directory
        parent = json_file.parent.name.lower()
        if "mexc" in parent:
            exchange = "mexc_spot_v3"
        elif "nonkyc" in parent:
            exchange = "nonkyc"
        else:
            continue
        tag = f"json_{json_file.stem}"
        try:
            raw = json_file.read_text(encoding="utf-8")
            fname = f"{exchange}_{tag}.json"
            save_text(sources_dir / fname, raw)
            fetched_at = dt.datetime.utcnow().isoformat() + "Z"
            if exchange not in manifest:
                manifest[exchange] = []
            manifest[exchange].append({
                "url": f"webscrape/{rel}",
                "kind": "json", "tag": tag, "status": 200,
                "fetched_at": fetched_at, "file": fname,
                "size": len(raw),
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "provenance": "webscrape",
            })
            loaded_count += 1
            log(f"  OK (webscrape json): {len(raw)} bytes -> {fname}")
        except Exception as exc:
            log(f"  ERROR loading webscrape json {rel}: {exc}")

    log(f"Loaded {loaded_count} webscrape source(s) from {webscrape_dir}")
    return manifest

def parse_nonkyc_openapi(spec: dict) -> list[dict]:
    """Parse NonKYC OpenAPI spec into endpoint documentation."""
    endpoints = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ("get", "post", "put", "delete", "patch"):
                ep = {
                    "method": method.upper(),
                    "path": path,
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tag": details.get("tags", ["Unknown"])[0] if details.get("tags") else "Unknown",
                    "parameters": details.get("parameters", []),
                    "request_body_schema": {},
                    "response_schemas": {},
                    "security": details.get("security", []),
                }
                # Extract request body schema
                rb = details.get("requestBody", {})
                if rb:
                    content = rb.get("content", {})
                    for ct, ct_detail in content.items():
                        if "schema" in ct_detail:
                            ep["request_body_schema"] = ct_detail["schema"]
                            break

                # Extract response schemas
                for status_code, resp in details.get("responses", {}).items():
                    content = resp.get("content", {})
                    for ct, ct_detail in content.items():
                        if "schema" in ct_detail:
                            ep["response_schemas"][status_code] = {
                                "description": resp.get("description", ""),
                                "schema": ct_detail["schema"],
                            }
                            break

                endpoints.append(ep)
    return endpoints


# ---------------------------------------------------------------------------
# Python client AST extraction (NonKYC)
# ---------------------------------------------------------------------------

def extract_nonkyc_from_python_client(py_source: str) -> dict:
    """Parse the NonKYC Python client to extract method signatures, URLs, auth patterns."""
    info = {
        "rest_base": "",
        "ws_base": "",
        "auth_headers": [],
        "auth_sign_pattern": "",
        "ws_login_fields": [],
        "rest_methods": [],
        "ws_methods": [],
    }

    try:
        tree = ast.parse(py_source)
    except SyntaxError:
        return info

    for node in ast.walk(tree):
        # Look for class assignments for base URL
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in ("base_url", "BASE_URL", "baseUrl"):
                        if isinstance(node.value, ast.Constant):
                            info["rest_base"] = str(node.value.value)
                    elif target.id in ("ws_url", "WS_URL", "wsUrl"):
                        if isinstance(node.value, ast.Constant):
                            info["ws_base"] = str(node.value.value)

    return info


# ---------------------------------------------------------------------------
# MEXC endpoint extraction from HTML docs
# ---------------------------------------------------------------------------

def extract_mexc_endpoints(markdown: str, title: str) -> list[dict]:
    """Extract MEXC REST endpoints from the markdown-converted docs."""
    endpoints = []
    current_section = ""

    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Track sections
        if line.startswith("# ") and not line.startswith("## "):
            current_section = line[2:].strip()
        elif line.startswith("## "):
            current_section = line[3:].strip()

        # Find endpoint patterns like: GET /api/v3/ping or **GET** `/api/v3/ping`
        endpoint_match = re.match(
            r"(?:\*\*)?(GET|POST|PUT|DELETE|PATCH)(?:\*\*)?\s+[`]?(/api/\S+)[`]?",
            line, re.IGNORECASE
        )
        if not endpoint_match:
            # Try heading-style: ### GET /api/v3/ping
            endpoint_match = re.match(
                r"#{1,4}\s+(?:\*\*)?(GET|POST|PUT|DELETE|PATCH)(?:\*\*)?\s+[`]?(/api/\S+)[`]?",
                line, re.IGNORECASE
            )

        if endpoint_match:
            method = endpoint_match.group(1).upper()
            path = endpoint_match.group(2).rstrip("`").rstrip("*")

            # Gather the next lines for summary, params, response
            ep = {
                "method": method,
                "path": path,
                "section": current_section,
                "summary": "",
                "params": [],
                "response_example": "",
            }

            # Look ahead for summary, parameters, response
            j = i + 1
            in_response = False
            response_lines = []
            while j < len(lines) and j < i + 200:
                next_line = lines[j].strip()
                # Break on next endpoint
                if re.match(r"(?:#{1,4}\s+)?(?:\*\*)?(GET|POST|PUT|DELETE|PATCH)", next_line, re.IGNORECASE):
                    if j > i + 1:
                        break

                if "**Response**" in next_line or "Response:" in next_line:
                    in_response = True
                elif in_response and next_line.startswith("```"):
                    # Start of code block
                    k = j + 1
                    code_lines = []
                    while k < len(lines):
                        if lines[k].strip().startswith("```"):
                            break
                        code_lines.append(lines[k])
                        k += 1
                    if code_lines:
                        ep["response_example"] = "\n".join(code_lines)
                    in_response = False
                    j = k
                j += 1

            endpoints.append(ep)
        i += 1

    return endpoints


# ---------------------------------------------------------------------------
# MEXC source doc response schema parser
# ---------------------------------------------------------------------------

def parse_mexc_source_response_schemas(markdown: str) -> dict:
    """Parse MEXC source markdown to extract documented request params and response schemas.

    Returns dict mapping path -> {
        "method": str,
        "response_example": str (JSON from docs),
        "response_fields": [{"name": str, "type": str, "description": str}],
        "request_params": [{"name": str, "type": str, "mandatory": str, "description": str}],
    }
    """
    schemas: dict = {}
    lines = markdown.splitlines()
    i = 0

    def _parse_table(start_line: int, end_line: int) -> list[dict]:
        """Parse a markdown table into list of dicts, normalizing column names."""
        rows = []
        header = None
        # Column name normalization: MEXC Spot uses "Name", MEXC Futures uses "Parameter"
        col_aliases = {
            "parameter": "name",
            "data_type": "type",
            "date_type": "type",  # typo in some MEXC docs
        }
        for idx in range(start_line, min(end_line, len(lines))):
            row = lines[idx].strip()
            if not row.startswith("|"):
                if header is not None:
                    break
                continue
            if "---" in row and "|" in row:
                continue  # separator row
            parts = [p.strip() for p in row.split("|")[1:-1]]
            if header is None:
                header = [col_aliases.get(h.lower().replace(" ", "_"), h.lower().replace(" ", "_")) for h in parts]
            else:
                entry = {}
                for ci, col in enumerate(parts):
                    if ci < len(header):
                        entry[header[ci]] = col
                if entry:
                    rows.append(entry)
        return rows

    while i < len(lines):
        line = lines[i].strip()

        # Match: * **METHOD** `path` or **METHOD** `/path`
        ep_match = re.match(r'\*?\s*\*\*(GET|POST|PUT|DELETE)\*\*\s*`([^`]+)`', line)
        if ep_match:
            method = ep_match.group(1)
            raw_path = ep_match.group(2).strip()
            path = raw_path if raw_path.startswith("/") else "/" + raw_path

            entry: dict = {"method": method, "response_example": "", "response_fields": [], "request_params": []}

            # Find section boundary above this endpoint line (heading or --- separator)
            section_start = max(0, i - 60)
            for back in range(i - 1, section_start - 1, -1):
                bline = lines[back].strip()
                # Section heading patterns: "## Heading" or "Heading\n---"
                if bline.startswith("## "):
                    section_start = back
                    break
                if re.match(r'^-{3,}$', bline) and back > 0:
                    section_start = back - 1
                    break

            # Find the LAST "> Response" / "> response" code block within this section
            # (between section_start and the endpoint line i)
            # This ensures we get THIS endpoint's response, not the previous one's
            last_response_example = ""
            scan_from = section_start
            for back in range(scan_from, i):
                bline = lines[back].strip().lower()
                if bline in ("> response", "**response**"):
                    # Find the code block after this marker
                    for k in range(back + 1, min(i + 5, len(lines))):
                        if lines[k].strip().startswith("```"):
                            code_lines = []
                            for m in range(k + 1, min(k + 80, len(lines))):
                                if lines[m].strip().startswith("```"):
                                    break
                                code_lines.append(lines[m])
                            candidate = "\n".join(code_lines).strip()
                            # Validate: reject if it looks like a request line
                            if candidate and not re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+', candidate):
                                last_response_example = candidate
                            break
            entry["response_example"] = last_response_example

            # Scan forward for parameter/response tables
            scan_end = min(i + 120, len(lines))
            for j in range(i + 1, scan_end):
                fwd = lines[j].strip()
                # Stop at next endpoint definition
                if re.match(r'\*?\s*\*\*(GET|POST|PUT|DELETE)\*\*\s*`', fwd):
                    break
                # Stop at next major section heading or horizontal rule
                if fwd.startswith("## ") or fwd.startswith("### "):
                    break
                if re.match(r'^-{3,}$', fwd):
                    break

                fwd_lower = fwd.lower()

                # Detect parameter inheritance: "equaled POST /api/v3/order" etc.
                inherit_match = re.match(r'equaled\s+(GET|POST|PUT|DELETE)\s+(/\S+)', fwd, re.IGNORECASE)
                if inherit_match and not entry["request_params"]:
                    entry["_inherit_from"] = f"{inherit_match.group(1).upper()} {inherit_match.group(2)}"

                # Request parameter table — must NOT match "response parameters" or table rows
                is_req_trigger = (
                    not fwd.startswith("|") and  # exclude table data rows
                    (("parameter" in fwd_lower and "response" not in fwd_lower) or fwd_lower.startswith("**request"))
                )
                if is_req_trigger and not entry["request_params"]:
                    # Check if the next non-blank line is "None" or a table
                    next_content = ""
                    for peek in range(j + 1, min(j + 4, len(lines))):
                        pline = lines[peek].strip()
                        if pline:
                            next_content = pline.lower()
                            break
                    if next_content == "none":
                        entry["_explicit_no_params"] = True
                    elif next_content.startswith("|"):
                        rows = _parse_table(j + 1, j + 40)
                        if rows and len(rows) > 0:
                            entry["request_params"] = rows

                # Response field table — match "Response Parameters" or "Response:" etc
                is_resp_trigger = (
                    not fwd.startswith("|") and
                    "response" in fwd_lower and
                    (fwd_lower.startswith("response") or fwd_lower.startswith("**response"))
                )
                if is_resp_trigger and not entry["response_fields"]:
                    rows = _parse_table(j + 1, j + 60)
                    if rows and len(rows) > 0:
                        entry["response_fields"] = rows

            schemas[f"{method} {path}"] = entry
            norm = re.sub(r'/BTC_USDT|/USDT|/BTC|/\d+', '/{param}', path)
            if norm != path:
                schemas[f"{method} {norm}"] = entry

        i += 1

    # Post-processing: resolve parameter inheritance (e.g. "equaled POST /api/v3/order")
    for key, entry in schemas.items():
        inherit_ref = entry.pop("_inherit_from", None)
        if inherit_ref and not entry["request_params"]:
            source = schemas.get(inherit_ref)
            if source and source.get("request_params"):
                entry["request_params"] = list(source["request_params"])

    return schemas


# ---------------------------------------------------------------------------
# NonKYC: Comprehensive REST validation
# ---------------------------------------------------------------------------

async def validate_nonkyc_rest(
    client: httpx.AsyncClient,
    output_dir: Path,
    auth: Optional[NonKycAuth],
    skip_private: bool = False,
) -> tuple[list[ValidationResult], list[EndpointDoc]]:
    """Test all NonKYC REST endpoints and build documentation."""
    results = []
    endpoint_docs = []

    # ---- Resolve dynamic IDs by pre-fetching list endpoints ----
    dynamic_ids = {}
    # Get a real asset ID
    try:
        _, asset_list, _, _ = await request_json(client, "GET", f"{NONKYC_REST_BASE}/asset/getlist")
        if isinstance(asset_list, list) and asset_list:
            # Find BTC or first asset with an 'id' field
            for asset in asset_list:
                if isinstance(asset, dict) and asset.get("ticker") == "BTC":
                    asset_id = asset.get("id") or asset.get("_id")
                    if asset_id:
                        dynamic_ids["asset"] = asset_id
                        break
            if "asset" not in dynamic_ids:
                first = asset_list[0]
                if isinstance(first, dict):
                    asset_id = first.get("id") or first.get("_id")
                    if asset_id:
                        dynamic_ids["asset"] = asset_id
            log(f"Dynamic IDs: asset={dynamic_ids.get('asset', 'NOT FOUND')}")
    except Exception as exc:
        log(f"Failed to pre-fetch asset list for dynamic IDs: {exc}")

    # Get a real pool ID and symbol
    try:
        _, pool_list, _, _ = await request_json(client, "GET", f"{NONKYC_REST_BASE}/pool/getlist")
        if isinstance(pool_list, list) and pool_list:
            first_pool = pool_list[0]
            if isinstance(first_pool, dict):
                pool_id = first_pool.get("id") or first_pool.get("_id")
                if pool_id:
                    dynamic_ids["pool"] = pool_id
                if first_pool.get("symbol"):
                    dynamic_ids["pool_symbol"] = first_pool["symbol"]
            log(f"Dynamic IDs: pool={dynamic_ids.get('pool', 'NOT FOUND')}, pool_symbol={dynamic_ids.get('pool_symbol', 'NOT FOUND')}")
    except Exception as exc:
        log(f"Failed to pre-fetch pool list for dynamic IDs: {exc}")

    # ---- PUBLIC ENDPOINTS ----
    for ep in NONKYC_PUBLIC_REST_ENDPOINTS:
        method = ep["method"]
        path_template = ep["path"]
        tag = ep["tag"]
        summary = ep["summary"]

        # Build actual URL
        path = path_template

        # Handle endpoints that need dynamic IDs
        if ep.get("needs_dynamic_id"):
            id_key = ep["needs_dynamic_id"]
            if id_key in dynamic_ids:
                param_name = re.search(r"\{(\w+)\}", path).group(1)
                path = path.replace(f"{{{param_name}}}", dynamic_ids[id_key])
            else:
                # Can't test without a valid ID
                doc = EndpointDoc(
                    method=method, path=path_template,
                    full_url=f"{NONKYC_REST_BASE}{path}",
                    tag=tag, summary=summary, permission="public",
                    tested=False, test_status="skip",
                    notes=[f"Skipped: could not resolve dynamic {id_key} ID from list endpoint"],
                )
                endpoint_docs.append(doc)
                continue
        elif "{" in path and "test_param" in ep:
            # Replace path parameter with static test value
            param_name = re.search(r"\{(\w+)\}", path).group(1)
            path = path.replace(f"{{{param_name}}}", ep["test_param"])

        url = f"{NONKYC_REST_BASE}{path}"
        query_params = ep.get("query_params")

        test_name = f"nonkyc_rest_public_{slugify(path_template.strip('/'))}"

        status, data, latency, error = await request_json(
            client, method, url, params=query_params
        )

        # Classify result — detect Cloudflare WAF blocks and spec/runtime drift as warn, not fail
        is_cloudflare_block = (status == 403 and isinstance(data, str) and "cloudflare" in data.lower())
        is_spec_drift = (status == 404)  # endpoint in OpenAPI but missing at runtime
        if status == 200 and data is not None:
            rst = "pass"
        elif is_cloudflare_block:
            rst = "warn"
        elif is_spec_drift:
            rst = "warn"
        elif isinstance(data, dict) and "error" in data:
            rst = "warn"
        else:
            rst = "fail"

        if is_cloudflare_block:
            detail_msg = "Cloudflare WAF block (403) — endpoint blocked for this IP/pattern"
        elif is_spec_drift:
            detail_msg = f"Spec/runtime drift — endpoint in OpenAPI but returned {status} live"
        else:
            detail_msg = error if error else ""

        result = ValidationResult(
            name=test_name,
            status=rst,
            transport="rest",
            http_status=status,
            latency_ms=latency,
            target=url,
            details=detail_msg,
        )

        doc = EndpointDoc(
            method=method, path=path_template, full_url=url,
            tag=tag, summary=summary, permission="public",
            tested=True, test_status=result.status, test_latency_ms=latency,
            http_status=status,
        )

        if query_params:
            doc.request_params = [{"name": k, "example": v} for k, v in query_params.items()]

        if status == 200 and data is not None:
            result.observed_fields = collect_field_names(data)
            result.response_schema = infer_json_schema(data)
            result.response_example = data

            doc.response_schema = result.response_schema
            doc.response_example = data
            doc.response_example_truncated = truncate_json_for_display(data)

            sample_path = save_sample(output_dir, test_name, data)
            result.sample_path = sample_path
            log(f"PASS | {test_name} | status={status} | latency={latency}ms | fields={len(result.observed_fields)}")
        else:
            if is_cloudflare_block:
                doc.notes.append("Cloudflare WAF returns 403 for this endpoint. Use /asset/getbyticker/{ticker} as alternative.")
            elif is_spec_drift:
                doc.notes.append(f"Spec/runtime drift: endpoint defined in OpenAPI but returned HTTP {status} live. May have been removed or moved.")
            elif data and isinstance(data, dict) and "error" in data:
                doc.error_schema = infer_json_schema(data)
                doc.notes.append(f"Error response (HTTP {status}): {json.dumps(data)}")
                save_sample(output_dir, f"{test_name}_error", data)
            log(f"{'WARN' if rst == 'warn' else 'FAIL'} | {test_name} | status={status} | {detail_msg or 'see response'}")

        results.append(result)
        endpoint_docs.append(doc)

    # ---- PRIVATE ENDPOINTS ----
    if auth and not skip_private:
        for ep in NONKYC_PRIVATE_REST_ENDPOINTS:
            method = ep["method"]
            path_template = ep["path"]
            tag = ep["tag"]
            summary = ep["summary"]

            path = path_template
            # Skip endpoints that need specific IDs we don't have
            if "{order_id}" in path:
                # We'll still document it but mark as not testable without a real order
                doc = EndpointDoc(
                    method=method, path=path_template,
                    full_url=f"{NONKYC_REST_BASE}{path}",
                    tag=tag, summary=summary, permission="private",
                    tested=False, test_status="skip",
                    notes=["Requires a valid order ID to test"],
                )
                endpoint_docs.append(doc)
                continue

            if "{" in path and "test_param" in ep:
                param_name = re.search(r"\{(\w+)\}", path).group(1)
                path = path.replace(f"{{{param_name}}}", ep["test_param"])

            url = f"{NONKYC_REST_BASE}{path}"
            query_params = ep.get("query_params")

            # Build full URL for signing
            sign_url = url
            if query_params:
                sign_url = url + "?" + urlencode(query_params)

            headers = nonkyc_rest_headers(auth, sign_url)

            test_name = f"nonkyc_rest_private_{slugify(path_template.strip('/'))}"

            status, data, latency, error = await request_json(
                client, method, url, headers=headers, params=query_params
            )

            result = ValidationResult(
                name=test_name,
                status="pass" if status == 200 and data is not None else (
                    "warn" if (isinstance(data, dict) and "error" in data) else "fail"
                ),
                transport="rest",
                auth_method="nonkyc_hmac_headers",
                http_status=status,
                latency_ms=latency,
                target=url,
                details=error if error else "",
            )

            doc = EndpointDoc(
                method=method, path=path_template, full_url=url,
                tag=tag, summary=summary, permission="private",
                tested=True, test_status=result.status, test_latency_ms=latency,
                http_status=status,
            )

            if query_params:
                doc.request_params = [{"name": k, "example": v} for k, v in query_params.items()]

            if status == 200 and data is not None:
                result.observed_fields = collect_field_names(data)
                result.response_schema = infer_json_schema(data)
                result.response_example = data

                doc.response_schema = result.response_schema
                doc.response_example = data
                doc.response_example_truncated = truncate_json_for_display(data)

                sample_path = save_sample(output_dir, test_name, data)
                result.sample_path = sample_path
                log(f"PASS | {test_name} | auth=yes | status={status} | latency={latency}ms | fields={len(result.observed_fields)}")
            else:
                if data and isinstance(data, dict) and "error" in data:
                    doc.error_schema = infer_json_schema(data)
                    doc.notes.append(f"Error response: {json.dumps(data)}")
                log(f"{'FAIL' if result.status == 'fail' else 'WARN'} | {test_name} | status={status} | error={error or data}")

            results.append(result)
            endpoint_docs.append(doc)

    elif not auth:
        log("NonKYC private REST: SKIPPED (no credentials)")
        for ep in NONKYC_PRIVATE_REST_ENDPOINTS:
            doc = EndpointDoc(
                method=ep["method"], path=ep["path"],
                full_url=f"{NONKYC_REST_BASE}{ep['path']}",
                tag=ep["tag"], summary=ep["summary"], permission="private",
                tested=False, test_status="skip",
                notes=["Credentials not provided"],
            )
            endpoint_docs.append(doc)

    # Add POST endpoints (schema-only, not tested with real orders)
    for ep in NONKYC_POST_ENDPOINTS_SCHEMA_ONLY:
        doc = EndpointDoc(
            method=ep["method"], path=ep["path"],
            full_url=f"{NONKYC_REST_BASE}{ep['path']}",
            tag=ep["tag"], summary=ep["summary"], permission="private",
            request_body=ep.get("request_body", {}),
            tested=False, test_status="schema_only",
            notes=["Request body documented from OpenAPI spec. Not tested live to avoid placing real orders/withdrawals."],
        )
        endpoint_docs.append(doc)

    return results, endpoint_docs


# ---------------------------------------------------------------------------
# NonKYC: Comprehensive WS validation
# ---------------------------------------------------------------------------

async def validate_nonkyc_ws_public(
    output_dir: Path,
    symbol: str = "BTC/USDT",
) -> tuple[list[ValidationResult], list[WsMethodDoc]]:
    """Test all NonKYC public WS methods and subscriptions."""
    results = []
    ws_docs = []

    try:
        async with websockets.connect(NONKYC_WS_BASE, max_size=10_000_000) as ws:
            log(f"WS connected to {NONKYC_WS_BASE} (public)")

            # ---- Request/response methods ----
            request_id = 1
            for channel in NONKYC_WS_PUBLIC_CHANNELS:
                method_name = channel["method"]
                params = channel["params"]
                description = channel["description"]
                test_name = f"nonkyc_ws_public_{slugify(method_name)}"

                msg = {"method": method_name, "params": params, "id": request_id}
                await ws.send(json.dumps(msg))
                log(f"WS sent: {method_name} (id={request_id})")

                raw = await ws_recv_text(ws, timeout=WS_TIMEOUT)
                result = ValidationResult(
                    name=test_name, status="fail", transport="ws", target=NONKYC_WS_BASE,
                )

                doc = WsMethodDoc(
                    method_name=method_name, kind="request", permission="public",
                    description=description, params=params,
                )

                if raw:
                    try:
                        data = json.loads(raw)
                        if "result" in data:
                            result.status = "pass"
                            result.response_example = data
                            result.response_schema = infer_json_schema(data)
                            result.observed_fields = collect_field_names(data)

                            doc.response_schema = result.response_schema
                            doc.response_example = truncate_json_for_display(data)
                            doc.tested = True
                            doc.test_status = "pass"

                            save_sample(output_dir, test_name, data)
                            log(f"PASS | {test_name} | fields={len(result.observed_fields)}")
                        elif "error" in data:
                            result.status = "warn"
                            result.details = json.dumps(data.get("error", {}))
                            doc.notes.append(f"Error: {result.details}")
                            log(f"WARN | {test_name} | error={result.details}")
                        else:
                            result.status = "warn"
                            result.details = f"Unexpected response: {truncate_str(raw)}"
                            log(f"WARN | {test_name} | unexpected response")
                    except json.JSONDecodeError:
                        result.details = f"Non-JSON response: {truncate_str(raw)}"
                        log(f"FAIL | {test_name} | non-JSON response")
                else:
                    result.details = "No response received"
                    log(f"FAIL | {test_name} | timeout")

                results.append(result)
                ws_docs.append(doc)
                request_id += 1

            # ---- Subscription channels ----
            for sub in NONKYC_WS_SUBSCRIPTIONS:
                subscribe_method = sub["subscribe"]
                params = sub["params"]
                notification_methods = sub["notification_methods"]
                unsubscribe_method = sub["unsubscribe"]
                description = sub["description"]
                test_name = f"nonkyc_ws_sub_{slugify(subscribe_method)}"

                msg = {"method": subscribe_method, "params": params, "id": request_id}
                await ws.send(json.dumps(msg))
                log(f"WS sent: {subscribe_method} (id={request_id})")

                doc = WsMethodDoc(
                    method_name=subscribe_method, kind="subscription", permission="public",
                    description=description, params=params,
                    subscribe_method=subscribe_method,
                    unsubscribe_method=unsubscribe_method,
                    notification_methods=notification_methods,
                )

                result = ValidationResult(
                    name=test_name, status="fail", transport="ws", target=NONKYC_WS_BASE,
                )

                # Collect messages for a few seconds
                messages = await ws_collect_messages(ws, duration=WS_SUBSCRIBE_WAIT, max_messages=20)

                captured_methods = set()
                for msg_data in messages:
                    if isinstance(msg_data, dict):
                        # Check for subscription ACK
                        if msg_data.get("id") == request_id and "result" in msg_data:
                            pass  # ACK received

                        # Check for notifications
                        msg_method = msg_data.get("method", "")
                        if msg_method in notification_methods:
                            captured_methods.add(msg_method)
                            doc.notification_schemas[msg_method] = infer_json_schema(msg_data)
                            doc.notification_examples[msg_method] = truncate_json_for_display(msg_data)
                            save_sample(output_dir, f"{test_name}_{slugify(msg_method)}", msg_data)

                if captured_methods:
                    result.status = "pass"
                    doc.tested = True
                    doc.test_status = "pass"
                    result.observed_fields = set()
                    for msg_data in messages:
                        result.observed_fields.update(collect_field_names(msg_data))
                    log(f"PASS | {test_name} | captured: {', '.join(sorted(captured_methods))}")
                else:
                    # Even if no notifications arrived, the subscription may still be valid
                    # Check if we got an ACK
                    ack = any(m.get("id") == request_id and "result" in m for m in messages if isinstance(m, dict))
                    if ack:
                        result.status = "pass"
                        doc.tested = True
                        doc.test_status = "pass"
                        doc.notes.append("Subscription ACK received but no notifications during test window")
                        log(f"PASS | {test_name} | ACK received, no notifications in {WS_SUBSCRIBE_WAIT}s window")
                    else:
                        result.details = f"No ACK or notifications received in {WS_SUBSCRIBE_WAIT}s"
                        log(f"FAIL | {test_name} | no response")

                results.append(result)
                ws_docs.append(doc)
                request_id += 1

                # Unsubscribe
                unsub_msg = {"method": unsubscribe_method, "params": params, "id": request_id}
                await ws.send(json.dumps(unsub_msg))
                await ws_recv_text(ws, timeout=2.0)  # consume ACK
                request_id += 1

    except Exception as exc:
        log(f"WS public error: {exc}")
        results.append(ValidationResult(
            name="nonkyc_ws_public_connection", status="fail", transport="ws",
            target=NONKYC_WS_BASE, details=str(exc),
        ))

    return results, ws_docs


async def validate_nonkyc_ws_private(
    output_dir: Path,
    auth: NonKycAuth,
) -> tuple[list[ValidationResult], list[WsMethodDoc]]:
    """Test NonKYC private WS methods and subscriptions."""
    results = []
    ws_docs = []

    try:
        async with websockets.connect(NONKYC_WS_BASE, max_size=10_000_000) as ws:
            log(f"WS connected to {NONKYC_WS_BASE} (private)")

            # Login
            login_msg = nonkyc_ws_login_message(auth, request_id=100)
            await ws.send(json.dumps(login_msg))
            raw = await ws_recv_text(ws, timeout=WS_TIMEOUT)
            login_ok = False
            if raw:
                try:
                    data = json.loads(raw)
                    if data.get("result") is True:
                        login_ok = True
                        log("WS login: SUCCESS")
                        save_sample(output_dir, "nonkyc_ws_private_login", data)
                except Exception:
                    pass

            if not login_ok:
                log(f"WS login: FAILED ({raw})")
                results.append(ValidationResult(
                    name="nonkyc_ws_private_login", status="fail", transport="ws",
                    target=NONKYC_WS_BASE, auth_method="nonkyc_ws_hs256",
                    details=f"Login failed: {raw}",
                ))
                return results, ws_docs

            results.append(ValidationResult(
                name="nonkyc_ws_private_login", status="pass", transport="ws",
                target=NONKYC_WS_BASE, auth_method="nonkyc_ws_hs256",
            ))

            request_id = 101

            # ---- Private request/response methods ----
            for channel in NONKYC_WS_PRIVATE_CHANNELS:
                method_name = channel["method"]
                params = channel["params"]
                description = channel["description"]
                test_name = f"nonkyc_ws_private_{slugify(method_name)}"

                msg = {"method": method_name, "params": params, "id": request_id}
                await ws.send(json.dumps(msg))
                log(f"WS sent: {method_name} (id={request_id})")

                raw = await ws_recv_text(ws, timeout=WS_TIMEOUT)
                result = ValidationResult(
                    name=test_name, status="fail", transport="ws",
                    target=NONKYC_WS_BASE, auth_method="nonkyc_ws_hs256",
                )

                doc = WsMethodDoc(
                    method_name=method_name, kind="request", permission="private",
                    description=description, params=params,
                )

                if raw:
                    try:
                        data = json.loads(raw)
                        if "result" in data:
                            result.status = "pass"
                            result.response_schema = infer_json_schema(data)
                            result.response_example = data
                            result.observed_fields = collect_field_names(data)

                            doc.response_schema = result.response_schema
                            doc.response_example = truncate_json_for_display(data)
                            doc.tested = True
                            doc.test_status = "pass"

                            save_sample(output_dir, test_name, data)
                            log(f"PASS | {test_name} | fields={len(result.observed_fields)}")
                        else:
                            result.details = f"Unexpected: {truncate_str(raw)}"
                            log(f"WARN | {test_name} | unexpected")
                    except json.JSONDecodeError:
                        result.details = "Non-JSON"
                        log(f"FAIL | {test_name} | non-JSON")
                else:
                    result.details = "Timeout"
                    log(f"FAIL | {test_name} | timeout")

                results.append(result)
                ws_docs.append(doc)
                request_id += 1

            # ---- Private subscriptions ----
            for sub in NONKYC_WS_PRIVATE_SUBSCRIPTIONS:
                subscribe_method = sub["subscribe"]
                params = sub["params"]
                notification_methods = sub["notification_methods"]
                description = sub["description"]
                test_name = f"nonkyc_ws_sub_{slugify(subscribe_method)}"

                msg = {"method": subscribe_method, "params": params, "id": request_id}
                await ws.send(json.dumps(msg))
                log(f"WS sent: {subscribe_method} (id={request_id})")

                doc = WsMethodDoc(
                    method_name=subscribe_method, kind="subscription", permission="private",
                    description=description, params=params,
                    subscribe_method=subscribe_method,
                    notification_methods=notification_methods,
                )

                result = ValidationResult(
                    name=test_name, status="fail", transport="ws",
                    target=NONKYC_WS_BASE, auth_method="nonkyc_ws_hs256",
                )

                messages = await ws_collect_messages(ws, duration=WS_SUBSCRIBE_WAIT, max_messages=20)
                captured_methods = set()

                for msg_data in messages:
                    if isinstance(msg_data, dict):
                        msg_method = msg_data.get("method", "")
                        if msg_method in notification_methods:
                            captured_methods.add(msg_method)
                            doc.notification_schemas[msg_method] = infer_json_schema(msg_data)
                            doc.notification_examples[msg_method] = truncate_json_for_display(msg_data)
                            save_sample(output_dir, f"{test_name}_{slugify(msg_method)}", msg_data)

                if captured_methods or any(m.get("id") == request_id and "result" in m for m in messages if isinstance(m, dict)):
                    result.status = "pass"
                    doc.tested = True
                    doc.test_status = "pass"
                    if captured_methods:
                        log(f"PASS | {test_name} | captured: {', '.join(sorted(captured_methods))}")
                    else:
                        doc.notes.append("Subscription ACK received; notifications depend on account activity")
                        log(f"PASS | {test_name} | ACK received (no activity during test)")
                else:
                    result.details = "No ACK or notifications"
                    log(f"FAIL | {test_name} | no response")

                results.append(result)
                ws_docs.append(doc)
                request_id += 1

    except Exception as exc:
        log(f"WS private error: {exc}")
        traceback.print_exc()
        results.append(ValidationResult(
            name="nonkyc_ws_private_connection", status="fail", transport="ws",
            target=NONKYC_WS_BASE, details=str(exc),
        ))

    return results, ws_docs
# ---------------------------------------------------------------------------
# MEXC: REST validation (spot + futures)
# ---------------------------------------------------------------------------

MEXC_SPOT_PUBLIC_TESTS = [
    # Market Data Endpoints (all 12)
    {"path": "/api/v3/ping", "summary": "Test connectivity", "section": "Market Data"},
    {"path": "/api/v3/time", "summary": "Server time", "section": "Market Data"},
    {"path": "/api/v3/defaultSymbols", "summary": "API default symbols", "section": "Market Data"},
    {"path": "/api/v3/exchangeInfo", "summary": "Exchange rules and symbol info", "section": "Market Data", "params": {"symbol": "BTCUSDT"}},
    {"path": "/api/v3/depth", "summary": "Order book depth", "section": "Market Data", "params": {"symbol": "BTCUSDT", "limit": "10"}},
    {"path": "/api/v3/trades", "summary": "Recent trades list", "section": "Market Data", "params": {"symbol": "BTCUSDT", "limit": "5"}},
    {"path": "/api/v3/aggTrades", "summary": "Compressed/aggregate trades", "section": "Market Data", "params": {"symbol": "BTCUSDT", "limit": "5"}},
    {"path": "/api/v3/klines", "summary": "Kline/candlestick data", "section": "Market Data", "params": {"symbol": "BTCUSDT", "interval": "60m", "limit": "5"}},
    {"path": "/api/v3/avgPrice", "summary": "Current average price", "section": "Market Data", "params": {"symbol": "BTCUSDT"}},
    {"path": "/api/v3/ticker/24hr", "summary": "24h ticker price change statistics", "section": "Market Data", "params": {"symbol": "BTCUSDT"}},
    {"path": "/api/v3/ticker/price", "summary": "Symbol price ticker", "section": "Market Data", "params": {"symbol": "BTCUSDT"}},
    {"path": "/api/v3/ticker/bookTicker", "summary": "Symbol order book ticker", "section": "Market Data"},
    {"path": "/api/v3/symbol/offline", "summary": "Query offline/delisted symbols", "section": "Market Data"},
]

MEXC_SPOT_PRIVATE_TESTS = [
    # Account/Trade (read-only)
    {"path": "/api/v3/account", "summary": "Account information", "section": "Account/Trade"},
    {"path": "/api/v3/uid", "summary": "Query account UID", "section": "Account/Trade"},
    {"path": "/api/v3/openOrders", "summary": "Current open orders", "section": "Account/Trade"},
    {"path": "/api/v3/allOrders", "summary": "All orders (last 24h)", "section": "Account/Trade", "extra_params": {"symbol": "BTCUSDT", "limit": "5"}},
    {"path": "/api/v3/order", "summary": "Query order (requires orderId or origClientOrderId)", "section": "Account/Trade", "extra_params": {"symbol": "BTCUSDT", "orderId": "0"}, "may_fail": True},
    {"path": "/api/v3/myTrades", "summary": "Account trade list", "section": "Account/Trade", "extra_params": {"symbol": "BTCUSDT", "limit": "5"}},
    {"path": "/api/v3/selfSymbols", "summary": "User API default symbol", "section": "Account/Trade"},
    {"path": "/api/v3/kyc/status", "summary": "Query KYC status", "section": "Account/Trade"},
    {"path": "/api/v3/mxDeduct/enable", "summary": "Query MX deduct status", "section": "Account/Trade", "method": "GET"},
    {"path": "/api/v3/tradeFee", "summary": "Query symbol commission", "section": "Account/Trade", "extra_params": {"symbol": "BTCUSDT"}},
    # Wallet (read-only)
    {"path": "/api/v3/capital/config/getall", "summary": "Query currency information", "section": "Wallet"},
    {"path": "/api/v3/capital/deposit/address", "summary": "Deposit address", "section": "Wallet", "extra_params": {"coin": "BTC"}},
    {"path": "/api/v3/capital/deposit/hisrec", "summary": "Deposit history", "section": "Wallet"},
    {"path": "/api/v3/capital/withdraw/history", "summary": "Withdraw history", "section": "Wallet"},
    {"path": "/api/v3/capital/withdraw/address", "summary": "Withdraw address list", "section": "Wallet"},
    {"path": "/api/v3/capital/transfer", "summary": "Query universal transfer history", "section": "Wallet"},
    {"path": "/api/v3/capital/convert/list", "summary": "Get assets convertible to MX", "section": "Wallet"},
    {"path": "/api/v3/capital/convert", "summary": "Dust transfer log", "section": "Wallet", "method": "GET"},
    {"path": "/api/v3/capital/transfer/internal", "summary": "Internal transfer history", "section": "Wallet", "method": "GET"},
    {"path": "/api/v3/capital/transfer/tranId", "summary": "Transfer history by tranId", "section": "Wallet"},
    # Sub-Account (read-only)
    {"path": "/api/v3/sub-account/asset", "summary": "Query sub-account asset", "section": "Sub-Account", "extra_params": {"email": ""}, "may_fail": True},
    # Listen Key
    {"path": "/api/v3/userDataStream", "summary": "Get valid listen keys", "section": "Listen Key", "method": "GET"},
    # Rebate (read-only)
    {"path": "/api/v3/rebate/taxQuery", "summary": "Rebate history records", "section": "Rebate"},
    {"path": "/api/v3/rebate/detail", "summary": "Rebate records detail", "section": "Rebate"},
    {"path": "/api/v3/rebate/detail/kickback", "summary": "Self rebate records detail", "section": "Rebate"},
    {"path": "/api/v3/rebate/referCode", "summary": "Query refer code", "section": "Rebate"},
    {"path": "/api/v3/rebate/affiliate/commission", "summary": "Affiliate commission record", "section": "Rebate"},
    {"path": "/api/v3/rebate/affiliate/withdraw", "summary": "Affiliate withdraw record", "section": "Rebate"},
    {"path": "/api/v3/rebate/affiliate/commission/detail", "summary": "Affiliate commission detail", "section": "Rebate"},
    {"path": "/api/v3/rebate/affiliate/campaign", "summary": "Affiliate campaign data", "section": "Rebate"},
    {"path": "/api/v3/rebate/affiliate/referral", "summary": "Affiliate referral data", "section": "Rebate"},
    {"path": "/api/v3/rebate/affiliate/subaffiliates", "summary": "Sub-affiliates data", "section": "Rebate"},
]

# Spot endpoints documented from source but NOT safe to live-test (mutating/destructive)
MEXC_SPOT_SCHEMA_ONLY = [
    {"method": "POST", "path": "/api/v3/order/test", "summary": "Test new order (validates without matching)", "section": "Account/Trade"},
    {"method": "POST", "path": "/api/v3/order", "summary": "New order", "section": "Account/Trade"},
    {"method": "POST", "path": "/api/v3/batchOrders", "summary": "Batch orders (max 20)", "section": "Account/Trade"},
    {"method": "DELETE", "path": "/api/v3/order", "summary": "Cancel order", "section": "Account/Trade"},
    {"method": "DELETE", "path": "/api/v3/openOrders", "summary": "Cancel all open orders on symbol", "section": "Account/Trade"},
    {"method": "POST", "path": "/api/v3/mxDeduct/enable", "summary": "Enable/disable MX deduct", "section": "Account/Trade"},
    {"method": "POST", "path": "/api/v3/capital/withdraw", "summary": "Withdraw", "section": "Wallet"},
    {"method": "POST", "path": "/api/v3/capital/withdraw/apply", "summary": "Withdraw (new)", "section": "Wallet"},
    {"method": "DELETE", "path": "/api/v3/capital/withdraw", "summary": "Cancel withdraw", "section": "Wallet"},
    {"method": "POST", "path": "/api/v3/capital/deposit/address", "summary": "Generate deposit address", "section": "Wallet"},
    {"method": "POST", "path": "/api/v3/capital/transfer", "summary": "Universal transfer", "section": "Wallet"},
    {"method": "POST", "path": "/api/v3/capital/convert", "summary": "Dust transfer", "section": "Wallet"},
    {"method": "POST", "path": "/api/v3/capital/transfer/internal", "summary": "Internal transfer", "section": "Wallet"},
    {"method": "POST", "path": "/api/v3/capital/sub-account/universalTransfer", "summary": "Sub-account universal transfer", "section": "Sub-Account"},
    {"method": "POST", "path": "/api/v3/userDataStream", "summary": "Generate listen key", "section": "Listen Key"},
    {"method": "PUT", "path": "/api/v3/userDataStream", "summary": "Extend listen key validity", "section": "Listen Key"},
    {"method": "DELETE", "path": "/api/v3/userDataStream", "summary": "Close listen key", "section": "Listen Key"},
    # STP (Self-Trade Prevention) strategy group endpoints (2025-09-17)
    {"method": "POST", "path": "/api/v3/strategy/group/uid", "summary": "Add UID to STP strategy group", "section": "STP"},
    {"method": "DELETE", "path": "/api/v3/strategy/group/uid", "summary": "Remove UID from STP strategy group", "section": "STP"},
]

MEXC_SPOT_WS_CHANNELS = [
    {"channel": "spot@public.deals.v3.api@BTCUSDT", "summary": "Trade streams", "section": "WS Market Streams"},
    {"channel": "spot@public.kline.v3.api@BTCUSDT@Min60", "summary": "Kline streams", "section": "WS Market Streams"},
    {"channel": "spot@public.increase.depth.v3.api@BTCUSDT", "summary": "Diff depth stream", "section": "WS Market Streams"},
    {"channel": "spot@public.limit.depth.v3.api@BTCUSDT@5", "summary": "Partial book depth", "section": "WS Market Streams"},
    {"channel": "spot@public.bookTicker.v3.api@BTCUSDT", "summary": "Individual book ticker", "section": "WS Market Streams"},
    {"channel": "spot@public.aggre.bookTicker.v3.api@BTCUSDT", "summary": "Book ticker (batch aggregation)", "section": "WS Market Streams"},
    {"channel": "spot@public.aggre.deals.v3.api.pb@BTCUSDT", "summary": "Aggregated deals (protobuf)", "section": "WS Market Streams"},
    {"channel": "spot@public.aggre.depth.v3.api.pb@BTCUSDT", "summary": "Aggregated depth (protobuf)", "section": "WS Market Streams"},
    # MiniTicker channels (2025-08-15)
    {"channel": "spot@public.miniTicker.v3.api@BTCUSDT", "summary": "Individual mini ticker (24h rolling)", "section": "WS Market Streams"},
    {"channel": "spot@public.miniTickers.v3.api", "summary": "All market mini tickers (24h rolling)", "section": "WS Market Streams"},
]

MEXC_SPOT_WS_PRIVATE_CHANNELS = [
    {"channel": "spot@private.deals.v3.api", "summary": "Spot account deals", "section": "WS User Data"},
    {"channel": "spot@private.orders.v3.api", "summary": "Spot account orders", "section": "WS User Data"},
    {"channel": "spot@private.account.v3.api", "summary": "Spot account update", "section": "WS User Data"},
]

MEXC_FUTURES_PUBLIC_TESTS = [
    # All 16 public contract endpoints
    {"path": "/api/v1/contract/ping", "summary": "Futures connectivity test", "section": "Market"},
    {"path": "/api/v1/contract/detail", "summary": "All contract details", "section": "Market"},
    {"path": "/api/v1/contract/support_currencies", "summary": "Supported currencies", "section": "Market"},
    {"path": "/api/v1/contract/depth/BTC_USDT", "summary": "Order book depth", "section": "Market"},
    {"path": "/api/v1/contract/depth_commits/BTC_USDT/5", "summary": "Depth commits (limited)", "section": "Market"},
    {"path": "/api/v1/contract/index_price/BTC_USDT", "summary": "Index price", "section": "Market"},
    {"path": "/api/v1/contract/fair_price/BTC_USDT", "summary": "Fair price", "section": "Market"},
    {"path": "/api/v1/contract/funding_rate/BTC_USDT", "summary": "Current funding rate", "section": "Market"},
    {"path": "/api/v1/contract/funding_rate/history", "summary": "Funding rate history", "section": "Market", "params": {"symbol": "BTC_USDT", "page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/contract/kline/BTC_USDT", "summary": "Kline/candlestick data", "section": "Market", "params": {"interval": "Min60", "limit": "5"}},
    {"path": "/api/v1/contract/kline/index_price/BTC_USDT", "summary": "Index price kline", "section": "Market", "params": {"interval": "Min60", "limit": "5"}},
    {"path": "/api/v1/contract/kline/fair_price/BTC_USDT", "summary": "Fair price kline", "section": "Market", "params": {"interval": "Min60", "limit": "5"}},
    {"path": "/api/v1/contract/deals/BTC_USDT", "summary": "Recent deals/trades", "section": "Market", "params": {"limit": "5"}},
    {"path": "/api/v1/contract/ticker", "summary": "All ticker data", "section": "Market"},
    {"path": "/api/v1/contract/risk_reverse", "summary": "Risk reverse data", "section": "Market"},
    {"path": "/api/v1/contract/risk_reverse/history", "summary": "Risk reverse history", "section": "Market", "params": {"symbol": "BTC_USDT", "page_num": "1", "page_size": "5"}},
]

MEXC_FUTURES_PRIVATE_TESTS = [
    # Read-only private endpoints — Account
    {"path": "/api/v1/private/account/assets", "summary": "Account asset balances", "section": "Account"},
    {"path": "/api/v1/private/account/asset/USDT", "summary": "Single asset balance", "section": "Account"},
    {"path": "/api/v1/private/account/risk_limit", "summary": "Account risk limit", "section": "Account"},
    {"path": "/api/v1/private/account/tiered_fee_rate/v2", "summary": "Tiered fee rate (v2)", "section": "Account", "extra_params": {"symbol": "BTC_USDT"}},
    {"path": "/api/v1/private/account/transfer_record", "summary": "Transfer record", "section": "Account", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/account/profit_rate/1", "summary": "Account profit rate (type=1)", "section": "Account"},
    {"path": "/api/v1/private/account/feeDeductConfigs", "summary": "Fee deduction configs", "section": "Account"},
    {"path": "/api/v1/private/account/contract/fee_rate", "summary": "Contract fee rate", "section": "Account"},
    # Read-only private endpoints — Position
    {"path": "/api/v1/private/position/open_positions", "summary": "Current open positions", "section": "Position"},
    {"path": "/api/v1/private/position/list/history_positions", "summary": "Historical positions", "section": "Position", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/position/funding_records", "summary": "Funding fee records", "section": "Position", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/position/position_mode", "summary": "Position mode (hedge/one-way)", "section": "Position"},
    {"path": "/api/v1/private/position/leverage", "summary": "Current leverage", "section": "Position", "extra_params": {"symbol": "BTC_USDT"}},
    # Read-only private endpoints — Order (canonical paths from official docs)
    {"path": "/api/v1/private/order/list/open_orders", "summary": "Open orders list", "section": "Order", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/order/list/history_orders", "summary": "Historical orders", "section": "Order", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/order/list/order_deals", "summary": "Order deal details", "section": "Order", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/planorder/list/orders", "summary": "Plan/trigger orders", "section": "Order", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/stoporder/list/orders", "summary": "Stop-limit orders", "section": "Order", "extra_params": {"page_num": "1", "page_size": "5"}},
    {"path": "/api/v1/private/stoporder/open_orders", "summary": "Open stop orders", "section": "Order", "extra_params": {"page_num": "1", "page_size": "5"}},
    # STP (Self-Trade Prevention) — read-only
    {"path": "/api/v1/private/market_maker/self_trade/blacklist", "summary": "Get STP blacklist", "section": "STP"},
]

# Futures endpoints documented from source but NOT safe to live-test
MEXC_FUTURES_SCHEMA_ONLY = [
    # Order management
    {"method": "POST", "path": "/api/v1/private/order/submit", "summary": "Submit order", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/order/submit_batch", "summary": "Submit batch orders", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/order/cancel", "summary": "Cancel order", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/order/cancel_all", "summary": "Cancel all orders", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/order/cancel_with_external", "summary": "Cancel by external order ID", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/order/open_order_total_count", "summary": "Query open order total count", "section": "Order"},
    # Plan/trigger orders
    {"method": "POST", "path": "/api/v1/private/planorder/place", "summary": "Place plan/trigger order", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/planorder/cancel", "summary": "Cancel plan order", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/planorder/cancel_all", "summary": "Cancel all plan orders", "section": "Order"},
    # Stop orders
    {"method": "POST", "path": "/api/v1/private/stoporder/cancel", "summary": "Cancel stop order", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/stoporder/cancel_all", "summary": "Cancel all stop orders", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/stoporder/change_price", "summary": "Change stop order price", "section": "Order"},
    {"method": "POST", "path": "/api/v1/private/stoporder/change_plan_price", "summary": "Change plan order trigger price", "section": "Order"},
    # Position management
    {"method": "POST", "path": "/api/v1/private/position/change_leverage", "summary": "Change leverage", "section": "Position"},
    {"method": "POST", "path": "/api/v1/private/position/change_margin", "summary": "Change margin", "section": "Position"},
    {"method": "POST", "path": "/api/v1/private/position/change_position_mode", "summary": "Switch position mode", "section": "Position"},
    {"method": "POST", "path": "/api/v1/private/position/change_auto_add_im", "summary": "Change auto-add margin", "section": "Position"},
    {"method": "POST", "path": "/api/v1/private/position/close_all", "summary": "Close all positions", "section": "Position"},
    # STP (Self-Trade Prevention) — mutating
    {"method": "GET", "path": "/api/v1/private/market_maker/self_trade/blacklist/search", "summary": "Search STP blacklist", "section": "STP"},
    {"method": "POST", "path": "/api/v1/private/market_maker/self_trade/blacklist/create", "summary": "Create STP blacklist entry", "section": "STP"},
    {"method": "POST", "path": "/api/v1/private/market_maker/self_trade/blacklist/update", "summary": "Update STP blacklist entry", "section": "STP"},
    {"method": "POST", "path": "/api/v1/private/market_maker/self_trade/blacklist/delete", "summary": "Delete STP blacklist entry", "section": "STP"},
]

MEXC_FUTURES_WS_CHANNELS = [
    {"method": "sub.ticker", "summary": "Single contract ticker", "section": "WS Public", "param": {"symbol": "BTC_USDT"}},
    {"method": "sub.tickers", "summary": "All contract tickers", "section": "WS Public", "param": {}},
    {"method": "sub.deal", "summary": "Trade/deal stream", "section": "WS Public", "param": {"symbol": "BTC_USDT"}},
    {"method": "sub.depth", "summary": "Full depth stream", "section": "WS Public", "param": {"symbol": "BTC_USDT"}},
    {"method": "sub.depth.step", "summary": "Depth step (aggregated)", "section": "WS Public", "param": {"symbol": "BTC_USDT", "step": "5"}},
    {"method": "sub.kline", "summary": "Kline stream", "section": "WS Public", "param": {"symbol": "BTC_USDT", "interval": "Min60"}},
    {"method": "sub.index.price", "summary": "Index price stream", "section": "WS Public", "param": {"symbol": "BTC_USDT"}},
    {"method": "sub.fair.price", "summary": "Fair price stream", "section": "WS Public", "param": {"symbol": "BTC_USDT"}},
    {"method": "sub.funding.rate", "summary": "Funding rate stream", "section": "WS Public", "param": {"symbol": "BTC_USDT"}},
]


async def validate_mexc_spot_rest(
    client: httpx.AsyncClient, output_dir: Path, auth: Optional[SpotAuth], skip_private: bool,
) -> tuple[list[ValidationResult], list[EndpointDoc]]:
    results = []
    endpoint_docs = []

    for test in MEXC_SPOT_PUBLIC_TESTS:
        path = test["path"]
        params = test.get("params")
        test_name = make_test_id("mexc_spot", "rest", "public", "GET", path)
        url = f"{MEXC_SPOT_REST_BASE}{path}"

        status, data, latency, error = await request_json(client, "GET", url, params=params)
        result = ValidationResult(
            name=test_name, status="pass" if status == 200 else "fail",
            transport="rest", http_status=status, latency_ms=latency, target=url, details=error,
        )
        doc = EndpointDoc(
            method="GET", path=path, full_url=url, tag=test.get("section", "Market Data"),
            summary=test["summary"], permission="public",
            tested=True, test_status=result.status, test_latency_ms=latency, http_status=status,
        )
        if params:
            doc.request_params = [{"name": k, "example": v} for k, v in params.items()]
        if data is not None:
            result.observed_fields = collect_field_names(data)
            result.response_schema = infer_json_schema(data)
            doc.response_schema = result.response_schema
            doc.response_example = data
            doc.response_example_truncated = truncate_json_for_display(data)
            save_sample(output_dir, test_name, data)
        results.append(result)
        endpoint_docs.append(doc)
        log(f"{'PASS' if result.status == 'pass' else 'FAIL'} | {test_name} | status={status} | latency={latency}ms")

    if auth and not skip_private:
        for test in MEXC_SPOT_PRIVATE_TESTS:
            path = test["path"]
            extra = test.get("extra_params", {})
            http_method = test.get("method", "GET")
            test_name = make_test_id("mexc_spot", "rest", "private", http_method, path)
            url = f"{MEXC_SPOT_REST_BASE}{path}"
            headers = mexc_spot_header(auth.api_key)
            params = mexc_spot_signed_params(extra, auth.api_secret)
            status, data, latency, error = await request_json(client, http_method, url, headers=headers, params=params)
            may_fail = test.get("may_fail", False)
            if may_fail and status != 200:
                rst = "warn"
            else:
                rst = "pass" if status == 200 else ("warn" if status in (400, 401) else "fail")
            result = ValidationResult(
                name=test_name, status=rst,
                transport="rest", auth_method="mexc_spot_hmac_query",
                http_status=status, latency_ms=latency, target=url, details=error,
            )
            doc = EndpointDoc(
                method=http_method, path=path, full_url=url,
                tag=test.get("section", "Account/Trade"),
                summary=test["summary"], permission="private",
                tested=True, test_status=rst, test_latency_ms=latency, http_status=status,
            )
            if data is not None:
                result.observed_fields = collect_field_names(data)
                result.response_schema = infer_json_schema(data)
                doc.response_schema = result.response_schema
                doc.response_example = data
                doc.response_example_truncated = truncate_json_for_display(data)
                save_sample(output_dir, test_name, data)
            results.append(result)
            endpoint_docs.append(doc)
            log(f"{'PASS' if rst == 'pass' else 'WARN'} | {test_name} | status={status} | latency={latency}ms")

    return results, endpoint_docs


async def validate_mexc_futures_rest(
    client: httpx.AsyncClient, output_dir: Path, auth: Optional[FuturesAuth], skip_private: bool,
) -> tuple[list[ValidationResult], list[EndpointDoc]]:
    results = []
    endpoint_docs = []

    for test in MEXC_FUTURES_PUBLIC_TESTS:
        path = test["path"]
        params = test.get("params")
        test_name = make_test_id("mexc_futures", "rest", "public", "GET", path)
        url = f"{MEXC_FUTURES_REST_BASE}{path}"
        status, data, latency, error = await request_json(client, "GET", url, params=params)
        result = ValidationResult(
            name=test_name, status="pass" if status == 200 else "fail",
            transport="rest", http_status=status, latency_ms=latency, target=url, details=error,
        )
        doc = EndpointDoc(
            method="GET", path=path, full_url=url, tag=test.get("section", "Market"),
            summary=test["summary"], permission="public",
            tested=True, test_status=result.status, test_latency_ms=latency, http_status=status,
        )
        if params:
            doc.request_params = [{"name": k, "example": v} for k, v in params.items()]
        if data is not None:
            result.observed_fields = collect_field_names(data)
            result.response_schema = infer_json_schema(data)
            doc.response_schema = result.response_schema
            doc.response_example = data
            doc.response_example_truncated = truncate_json_for_display(data)
            save_sample(output_dir, test_name, data)
        results.append(result)
        endpoint_docs.append(doc)
        log(f"{'PASS' if result.status == 'pass' else 'FAIL'} | {test_name} | status={status} | latency={latency}ms")

    if auth and not skip_private:
        for test in MEXC_FUTURES_PRIVATE_TESTS:
            path = test["path"]
            extra = test.get("extra_params", {})
            test_name = make_test_id("mexc_futures", "rest", "private", "GET", path)

            # Futures private: official canonical = api.mexc.com, but observed runtime
            # shows some private endpoints need contract.mexc.com as fallback.
            # Try contract.mexc.com first since it works more reliably for private calls.
            for base in [MEXC_FUTURES_REST_BASE_ALT, MEXC_FUTURES_REST_BASE]:
                url = f"{base}{path}"
                headers = mexc_futures_headers(auth, extra if extra else None)
                status, data, latency, error = await request_json(
                    client, "GET", url, headers=headers, params=extra if extra else None
                )
                if status == 200:
                    rst = "warn" if (isinstance(data, dict) and data.get("success") is False) else "pass"
                    result = ValidationResult(
                        name=test_name, status=rst, transport="rest",
                        auth_method="mexc_futures_hmac_headers",
                        http_status=status, latency_ms=latency, target=url,
                        details=json.dumps(data) if rst == "warn" else "",
                    )
                    doc = EndpointDoc(
                        method="GET", path=path,
                        full_url=f"{MEXC_FUTURES_REST_BASE}{path}",  # canonical base
                        tag=test.get("section", "Account"), summary=test["summary"],
                        permission="private", tested=True, test_status=rst,
                        test_latency_ms=latency, http_status=status,
                    )
                    if base == MEXC_FUTURES_REST_BASE_ALT:
                        doc.notes.append(f"Canonical URL: `{MEXC_FUTURES_REST_BASE}{path}`. Validated via observed fallback: `{url}`")
                    if data is not None:
                        result.observed_fields = collect_field_names(data)
                        result.response_schema = infer_json_schema(data)
                        doc.response_schema = result.response_schema
                        doc.response_example = data
                        doc.response_example_truncated = truncate_json_for_display(data)
                        save_sample(output_dir, test_name, data)
                    results.append(result)
                    endpoint_docs.append(doc)
                    log(f"{'PASS' if rst == 'pass' else 'WARN'} | {test_name} | status={status} | latency={latency}ms")
                    break
                elif base == MEXC_FUTURES_REST_BASE_ALT:
                    # First attempt failed, try alternate base
                    continue
                else:
                    # Both bases failed — check if it's a permission error (warn) vs real failure
                    is_permission_error = False
                    if isinstance(data, dict):
                        err_code = data.get("code") or data.get("success")
                        err_msg = str(data.get("msg", "") or data.get("message", "")).lower()
                        if err_code in (700007, 701, 703) or "permission" in err_msg or "access" in err_msg:
                            is_permission_error = True
                    rst = "warn" if is_permission_error else "fail"
                    result = ValidationResult(
                        name=test_name, status=rst, transport="rest",
                        auth_method="mexc_futures_hmac_headers",
                        http_status=status, latency_ms=latency, target=url,
                        details=error or str(data),
                    )
                    doc = EndpointDoc(
                        method="GET", path=path,
                        full_url=f"{MEXC_FUTURES_REST_BASE}{path}",  # canonical base
                        tag=test.get("section", "Account"), summary=test["summary"],
                        permission="private", tested=True, test_status=rst,
                        test_latency_ms=latency, http_status=status,
                    )
                    if data is not None:
                        result.observed_fields = collect_field_names(data)
                        result.response_schema = infer_json_schema(data)
                        doc.response_schema = result.response_schema
                        doc.response_example = data
                        doc.response_example_truncated = truncate_json_for_display(data)
                        save_sample(output_dir, test_name, data)
                    if is_permission_error:
                        doc.notes.append(f"Permission error (code {data.get('code', '?')}): {data.get('msg', data.get('message', ''))}")
                    results.append(result)
                    endpoint_docs.append(doc)
                    log(f"{'WARN' if rst == 'warn' else 'FAIL'} | {test_name} | status={status} | latency={latency}ms | {'permission error' if is_permission_error else ''}")

    return results, endpoint_docs


# ---------------------------------------------------------------------------
# MEXC: WS validation
# ---------------------------------------------------------------------------

async def validate_mexc_spot_ws(output_dir: Path, symbol: str = "BTCUSDT") -> tuple[list[ValidationResult], list[WsMethodDoc]]:
    results = []
    ws_docs = []
    test_name = "mexc_spot_ws_public_book_ticker"
    try:
        async with websockets.connect(MEXC_SPOT_WS_BASE, max_size=5_000_000) as ws:
            sub_msg = {"method": "SUBSCRIPTION", "params": [f"spot@public.bookTicker.batch.v3.api.pb@{symbol}"]}
            await ws.send(json.dumps(sub_msg))
            await ws.send(json.dumps({"method": "PING"}))
            messages = await ws_collect_messages(ws, duration=3.0, max_messages=5)
            # Distinguish ACK/PONG from real data payloads
            has_error = any(isinstance(m, dict) and m.get("msg") == "PONG" for m in messages)
            real_data = [m for m in messages if isinstance(m, dict)
                         and m.get("msg") not in ("PONG", "pong", None)
                         and "code" not in m]  # ACKs have "code"
            if real_data:
                ws_status = "pass"
            elif messages:
                ws_status = "warn"  # ack_only — connected but no decoded market data
            else:
                ws_status = "fail"
            result = ValidationResult(
                name=test_name, status=ws_status,
                transport="ws", target=MEXC_SPOT_WS_BASE,
            )
            doc = WsMethodDoc(
                method_name="spot@public.bookTicker", kind="subscription", permission="public",
                description="Best bid/ask price stream (protobuf-encoded after ACK)",
                subscribe_method="SUBSCRIPTION", tested=True, test_status=result.status,
            )
            doc.notes.append("MEXC spot WS delivers subscription ACK as JSON, then market data as protobuf/base64 frames.")
            if ws_status == "warn":
                doc.notes.append("Only ACK/PONG received — no decoded market data during test window. Protobuf decoding not yet implemented.")
            if messages:
                result.observed_fields = set()
                for m in messages:
                    result.observed_fields.update(collect_field_names(m))
                save_sample(output_dir, test_name, messages)
                doc.response_example = truncate_json_for_display(messages)
            results.append(result)
            ws_docs.append(doc)
            log(f"{'PASS' if result.status == 'pass' else 'FAIL'} | {test_name} | messages={len(messages)}")
    except Exception as exc:
        results.append(ValidationResult(
            name=test_name, status="fail", transport="ws",
            target=MEXC_SPOT_WS_BASE, details=str(exc),
        ))
        log(f"FAIL | {test_name} | {exc}")
    return results, ws_docs


async def validate_mexc_futures_ws(output_dir: Path, auth: Optional[FuturesAuth]) -> tuple[list[ValidationResult], list[WsMethodDoc]]:
    results = []
    ws_docs = []

    # Public ticker — use sub.ticker with explicit symbol (not empty param)
    test_name = "mexc_futures_ws_public_ticker"
    try:
        async with websockets.connect(MEXC_FUTURES_WS_BASE, max_size=5_000_000) as ws:
            await ws.send(json.dumps({"method": "ping"}))
            await ws.send(json.dumps({"method": "sub.ticker", "param": {"symbol": "BTC_USDT"}}))
            messages = await ws_collect_messages(ws, duration=3.0, max_messages=5)
            # Check for server errors and distinguish real data from pong/ack
            has_error = any(isinstance(m, dict) and m.get("channel") == "rs.error" for m in messages)
            real_data = [m for m in messages if isinstance(m, dict)
                         and m.get("channel", "").startswith("push.")
                         and m.get("data") != "pong"]
            if has_error:
                ws_status = "fail"
            elif real_data:
                ws_status = "pass"
            elif messages:
                ws_status = "warn"  # ack/pong only
            else:
                ws_status = "fail"
            result = ValidationResult(
                name=test_name, status=ws_status,
                transport="ws", target=MEXC_FUTURES_WS_BASE,
            )
            if has_error:
                err_msgs = [m for m in messages if isinstance(m, dict) and m.get("channel") == "rs.error"]
                result.details = f"Server error: {err_msgs[0].get('data', '')}" if err_msgs else "rs.error received"
            doc = WsMethodDoc(
                method_name="sub.ticker", kind="subscription", permission="public",
                description="Futures ticker stream for BTC_USDT",
                subscribe_method="sub.ticker", tested=True, test_status=ws_status,
            )
            if ws_status == "warn":
                doc.notes.append("Only ACK/pong received — no push.ticker data during test window.")
            if ws_status == "fail" and has_error:
                doc.notes.append(f"Server returned rs.error: {result.details}")
            if messages:
                result.observed_fields = set()
                for m in messages:
                    result.observed_fields.update(collect_field_names(m))
                save_sample(output_dir, test_name, messages)
                # Select business payload for example (prefer push.* over pong/ack)
                business_msg = next(
                    (m for m in messages if isinstance(m, dict) and m.get("channel", "").startswith("push.")),
                    messages[0]  # fallback to first if no push found
                )
                doc.response_example = truncate_json_for_display(business_msg)
                doc.response_schema = infer_json_schema(business_msg)
            results.append(result)
            ws_docs.append(doc)
            log(f"{'PASS' if result.status == 'pass' else 'FAIL'} | {test_name}")
    except Exception as exc:
        results.append(ValidationResult(
            name=test_name, status="fail", transport="ws",
            target=MEXC_FUTURES_WS_BASE, details=str(exc),
        ))
        log(f"FAIL | {test_name} | {exc}")

    # Private login
    if auth:
        test_name = "mexc_futures_ws_private_login"
        try:
            async with websockets.connect(MEXC_FUTURES_WS_BASE, max_size=5_000_000) as ws:
                req_time = str(now_ms())
                sig = sign_mexc_futures(auth.api_secret, auth.api_key, req_time, "")
                login_msg = {
                    "method": "login",
                    "param": {"apiKey": auth.api_key, "reqTime": req_time, "signature": sig}
                }
                await ws.send(json.dumps(login_msg))
                messages = await ws_collect_messages(ws, duration=3.0, max_messages=5)
                login_ok = any(
                    m.get("channel") == "rs.login" and m.get("data") == "success"
                    for m in messages if isinstance(m, dict)
                )
                result = ValidationResult(
                    name=test_name, status="pass" if login_ok else "fail",
                    transport="ws", auth_method="mexc_futures_hmac_headers",
                    target=MEXC_FUTURES_WS_BASE,
                )
                doc = WsMethodDoc(
                    method_name="login", kind="request", permission="private",
                    description="Authenticate futures WS session",
                    tested=True, test_status=result.status,
                )
                if messages:
                    save_sample(output_dir, test_name, messages)
                    doc.response_example = truncate_json_for_display(messages[0] if messages else {})
                results.append(result)
                ws_docs.append(doc)
                log(f"{'PASS' if login_ok else 'FAIL'} | {test_name}")
        except Exception as exc:
            results.append(ValidationResult(
                name=test_name, status="fail", transport="ws",
                target=MEXC_FUTURES_WS_BASE, details=str(exc),
            ))
            log(f"FAIL | {test_name} | {exc}")

    return results, ws_docs


# ---------------------------------------------------------------------------
# MEXC: Listen key + spot private WS
# ---------------------------------------------------------------------------

async def create_mexc_spot_listen_key(
    client: httpx.AsyncClient, output_dir: Path, auth: SpotAuth,
) -> tuple[Optional[str], ValidationResult, Optional[EndpointDoc]]:
    test_name = "mexc_spot_rest_private_create_listen_key"
    url = f"{MEXC_SPOT_REST_BASE}/api/v3/userDataStream"
    headers = mexc_spot_header(auth.api_key)
    # Try header-only first
    status, data, latency, error = await request_json(client, "POST", url, headers=headers)
    unsigned_failed = status != 200
    if status != 200 or not (isinstance(data, dict) and data.get("listenKey")):
        params = mexc_spot_signed_params({}, auth.api_secret)
        status, data, latency, error = await request_json(client, "POST", url, headers=headers, params=params)

    doc = EndpointDoc(
        method="POST", path="/api/v3/userDataStream", full_url=url,
        tag="Listen Key", summary="Create user data stream listen key",
        permission="private", tested=True, http_status=status,
    )
    if unsigned_failed:
        doc.notes.append("DISCREPANCY: Docs say 'Parameters: NONE', but unsigned POST returns 400. Signed request with timestamp+signature succeeds.")

    if status == 200 and isinstance(data, dict) and data.get("listenKey"):
        result = ValidationResult(
            name=test_name, status="pass", transport="rest", auth_method="mexc_spot_hmac_query",
            http_status=status, latency_ms=latency, target=url,
        )
        result.observed_fields = collect_field_names(data)
        doc.test_status = "pass"
        doc.test_latency_ms = latency
        doc.response_schema = infer_json_schema(data)
        doc.response_example = data
        doc.response_example_truncated = truncate_json_for_display(data)
        save_sample(output_dir, test_name, data)
        log(f"PASS | {test_name} | status={status} | latency={latency}ms")
        return data["listenKey"], result, doc
    else:
        result = ValidationResult(
            name=test_name, status="fail", transport="rest", auth_method="mexc_spot_hmac_query",
            http_status=status, latency_ms=latency, target=url, details=error or str(data),
        )
        doc.test_status = "fail"
        log(f"FAIL | {test_name} | status={status} | {error or data}")
        return None, result, doc


async def close_mexc_spot_listen_key(
    client: httpx.AsyncClient, auth: SpotAuth, listen_key: str,
) -> ValidationResult:
    test_name = "mexc_spot_rest_private_close_listen_key"
    url = f"{MEXC_SPOT_REST_BASE}/api/v3/userDataStream"
    headers = mexc_spot_header(auth.api_key)
    params = mexc_spot_signed_params({"listenKey": listen_key}, auth.api_secret)
    status, data, latency, error = await request_json(client, "DELETE", url, headers=headers, params=params)
    return ValidationResult(
        name=test_name, status="pass" if status == 200 else "warn",
        transport="rest", auth_method="mexc_spot_hmac_query",
        http_status=status, latency_ms=latency, target=url,
    )


async def validate_mexc_spot_private_ws(
    client: httpx.AsyncClient, output_dir: Path, auth: SpotAuth,
) -> tuple[list[ValidationResult], list[EndpointDoc], list[WsMethodDoc]]:
    results = []
    endpoint_docs = []
    ws_docs = []

    listen_key, create_result, create_doc = await create_mexc_spot_listen_key(client, output_dir, auth)
    results.append(create_result)
    if create_doc:
        endpoint_docs.append(create_doc)

    if listen_key:
        test_name = "mexc_spot_ws_private_account"
        ws_url = f"{MEXC_SPOT_WS_BASE}?listenKey={listen_key}"
        try:
            async with websockets.connect(ws_url, max_size=5_000_000) as ws:
                await ws.send(json.dumps({"method": "PING"}))
                messages = await ws_collect_messages(ws, duration=3.0, max_messages=5)
                # Classify: actual account events vs just PONG
                real_events = [m for m in messages if isinstance(m, dict)
                               and m.get("msg") not in ("PONG", "pong", None)]
                if real_events:
                    ws_status = "pass"
                else:
                    ws_status = "warn"  # authenticated_connected but no account events
                result = ValidationResult(
                    name=test_name, status=ws_status, transport="ws",
                    auth_method="listen_key", target=redact_url(ws_url),
                )
                doc = WsMethodDoc(
                    method_name="userDataStream", kind="subscription", permission="private",
                    description="Account updates via listen key (orders, balances, trades)",
                    tested=True, test_status=ws_status,
                )
                doc.notes.append("Connect with ?listenKey=<key>. Listen keys expire after 60 min; renew with PUT.")
                if ws_status == "warn":
                    doc.notes.append("Authenticated and connected, but no account events observed during test window.")
                if messages:
                    save_sample(output_dir, test_name, messages)
                    result.observed_fields = set()
                    for m in messages:
                        result.observed_fields.update(collect_field_names(m))
                results.append(result)
                ws_docs.append(doc)
                log(f"{'PASS' if ws_status == 'pass' else 'WARN'} | {test_name} | {'account events observed' if real_events else 'authenticated, no events'}")
        except Exception as exc:
            results.append(ValidationResult(
                name=test_name, status="fail", transport="ws",
                target=ws_url, details=str(exc),
            ))
            log(f"FAIL | {test_name} | {exc}")

        close_result = await close_mexc_spot_listen_key(client, auth, listen_key)
        results.append(close_result)

    return results, endpoint_docs, ws_docs
def render_nonkyc_docs(
    endpoint_docs: list[EndpointDoc],
    ws_docs: list[WsMethodDoc],
    openapi_spec: Optional[dict] = None,
) -> str:
    """Render comprehensive NonKYC documentation markdown."""
    parts = []

    parts.append("# NONKYC — Complete Engineering Reference\n\n")
    parts.append(f"_Generated: {dt.datetime.utcnow().isoformat()}Z_\n\n")

    # Overview
    parts.append("## Overview\n\n")
    parts.append(f"* **REST base**: `{NONKYC_REST_BASE}`\n")
    parts.append(f"* **WebSocket base**: `{NONKYC_WS_BASE}`\n")
    parts.append(f"* **OpenAPI spec**: `{NONKYC_OPENAPI_URL}`\n")
    parts.append("* **Auth headers**: `X-API-KEY`, `X-API-NONCE`, `X-API-SIGN`\n")
    parts.append("* **WS protocol**: JSON-RPC 2.0\n\n")

    # Auth documentation
    parts.append("## Authentication\n\n")
    parts.append("### REST API Authentication (HMAC-SHA256)\n\n")
    parts.append("All private endpoints require three headers:\n\n")
    parts.append("| Header | Description |\n")
    parts.append("| --- | --- |\n")
    parts.append("| `X-API-KEY` | Your public API key |\n")
    parts.append("| `X-API-NONCE` | Current timestamp in Unix milliseconds |\n")
    parts.append("| `X-API-SIGN` | HMAC-SHA256 signature |\n\n")

    parts.append("**Signature construction:**\n\n")
    parts.append("* **GET requests**: `HMAC-SHA256(apiSecret, apiKey + requestURL + nonce)`\n")
    parts.append("* **POST requests**: `HMAC-SHA256(apiSecret, apiKey + requestURL + requestBody + nonce)`\n\n")
    parts.append("where `requestURL` is the full URL including query string.\n\n")

    parts.append("### WebSocket Authentication\n\n")
    parts.append("Use the `login` method with HS256 algorithm:\n\n")
    parts.append("```json\n")
    parts.append('{\n  "method": "login",\n  "params": {\n')
    parts.append('    "algo": "HS256",\n    "pKey": "<apiKey>",\n')
    parts.append('    "nonce": "<random_string>",\n')
    parts.append('    "signature": "<HMAC-SHA256(apiSecret, nonce)>"\n  },\n  "id": 100\n}\n')
    parts.append("```\n\n")
    parts.append("Success response: `{\"jsonrpc\": \"2.0\", \"result\": true, \"id\": 100}`\n\n")

    # Data format notes
    parts.append("## Data Format Notes\n\n")
    parts.append("* **Precision**: All financial values (price, quantity, fee) are **string-encoded arbitrary precision** (e.g., `\"9823.23932892\"`) to prevent floating-point issues\n")
    parts.append("* **Timestamps**: ISO8601 UTC strings (e.g., `\"2021-12-01T00:00:00Z\"`) or Unix milliseconds as integers\n")
    parts.append("* **Integers**: Represented as numbers, not strings\n")
    parts.append("* **IDs**: MongoDB ObjectId strings (24 hex chars) or numeric strings\n\n")

    # REST endpoint catalog
    parts.append("## REST API — Endpoint Catalog\n\n")
    parts.append("| Method | Path | Permission | Tag | Summary | Tested |\n")
    parts.append("| --- | --- | --- | --- | --- | --- |\n")
    for doc in endpoint_docs:
        tested_str = "✓" if doc.tested and doc.test_status == "pass" else ("⚠" if doc.test_status == "warn" else ("—" if doc.test_status in ("skip", "schema_only") else "✗"))
        parts.append(f"| {doc.method} | `{doc.path}` | {doc.permission} | {doc.tag} | {doc.summary} | {tested_str} |\n")
    parts.append("\n")

    # REST endpoint details with schemas
    parts.append("## REST API — Endpoint Details\n\n")
    for doc in endpoint_docs:
        parts.append(f"### {doc.method} {doc.path}\n\n")
        parts.append(f"* **Permission**: {doc.permission}\n")
        parts.append(f"* **Tag**: {doc.tag}\n")
        parts.append(f"* **URL**: `{doc.full_url}`\n")
        if doc.tested:
            status_emoji = "✓" if doc.test_status == "pass" else "⚠"
            parts.append(f"* **Test**: {status_emoji} HTTP {doc.http_status} ({doc.test_latency_ms}ms)\n")
        parts.append(f"\n{doc.summary}\n\n")

        # Request parameters
        if doc.request_params:
            parts.append("**Query Parameters:**\n\n")
            parts.append("| Name | Example |\n| --- | --- |\n")
            for p in doc.request_params:
                parts.append(f"| `{p['name']}` | `{p.get('example', '')}` |\n")
            parts.append("\n")

        # Request body (for POST endpoints)
        if doc.request_body:
            parts.append("**Request Body** (`application/json`):\n\n")
            parts.append("| Field | Type | Required | Default | Description |\n")
            parts.append("| --- | --- | --- | --- | --- |\n")
            for fname, finfo in doc.request_body.items():
                req = "✓" if finfo.get("required") else ""
                default = str(finfo.get("default", "")) if "default" in finfo else ""
                desc = finfo.get("description", "")
                if "enum" in finfo:
                    desc += f" Enum: {finfo['enum']}"
                parts.append(f"| `{fname}` | {finfo.get('type', 'string')} | {req} | {default} | {desc} |\n")
            parts.append("\n")

        # Response schema
        if doc.response_schema and doc.response_schema.get("type"):
            parts.append("**Response Schema:**\n\n")
            schema = doc.response_schema
            if schema.get("type") == "array" and schema.get("items", {}).get("type") == "object":
                parts.append(f"Returns an array of objects ({schema.get('items', {}).get('properties', {}).__len__()} fields each):\n\n")
                parts.append("| Field | Type | Example |\n| --- | --- | --- |\n")
                parts.append(render_schema_markdown(schema["items"]))
                parts.append("\n\n")
            elif schema.get("type") == "object":
                parts.append("| Field | Type | Example |\n| --- | --- | --- |\n")
                parts.append(render_schema_markdown(schema))
                parts.append("\n\n")
            else:
                parts.append(f"Type: `{schema.get('type')}`\n\n")

        # Response example (truncated)
        if doc.response_example_truncated is not None:
            parts.append("**Response Example** (truncated):\n\n")
            parts.append("```json\n")
            parts.append(json.dumps(redact_value(doc.response_example_truncated), indent=2, default=str)[:3000])
            parts.append("\n```\n\n")

        # Notes
        for note in doc.notes:
            parts.append(f"> {note}\n\n")

        parts.append("---\n\n")

    # WebSocket documentation
    parts.append("## WebSocket API\n\n")
    parts.append(f"* **Endpoint**: `{NONKYC_WS_BASE}`\n")
    parts.append("* **Protocol**: JSON-RPC 2.0\n")
    parts.append("* **Heartbeat**: Server ping/pong every 60 seconds\n")
    parts.append("* **Sequence numbers**: Each subscription channel has incrementing sequence numbers for gap detection\n\n")

    # WS method catalog
    parts.append("### WebSocket Method Catalog\n\n")
    parts.append("| Method | Kind | Permission | Description | Tested |\n")
    parts.append("| --- | --- | --- | --- | --- |\n")
    for doc in ws_docs:
        tested_str = "✓" if doc.tested and doc.test_status == "pass" else "✗"
        parts.append(f"| `{doc.method_name}` | {doc.kind} | {doc.permission} | {doc.description} | {tested_str} |\n")
    parts.append("\n")

    # WS method details
    parts.append("### WebSocket Method Details\n\n")
    for doc in ws_docs:
        parts.append(f"#### `{doc.method_name}` — {doc.kind} ({doc.permission})\n\n")
        parts.append(f"{doc.description}\n\n")

        if doc.params:
            parts.append("**Parameters:**\n\n")
            parts.append("```json\n")
            parts.append(json.dumps(doc.params, indent=2))
            parts.append("\n```\n\n")

        if doc.kind == "subscription":
            if doc.notification_methods:
                parts.append(f"**Notification methods**: {', '.join(f'`{m}`' for m in doc.notification_methods)}\n\n")
            if doc.unsubscribe_method:
                parts.append(f"**Unsubscribe**: `{doc.unsubscribe_method}`\n\n")

        # Response schema
        if doc.response_schema and doc.response_schema.get("type"):
            parts.append("**Response Schema:**\n\n")
            parts.append("| Field | Type | Example |\n| --- | --- | --- |\n")
            parts.append(render_schema_markdown(doc.response_schema))
            parts.append("\n\n")

        if doc.response_example:
            parts.append("**Response Example:**\n\n```json\n")
            parts.append(json.dumps(redact_value(doc.response_example), indent=2, default=str)[:3000])
            parts.append("\n```\n\n")

        # Notification schemas
        for method_name, schema in doc.notification_schemas.items():
            parts.append(f"**`{method_name}` notification schema:**\n\n")
            parts.append("| Field | Type | Example |\n| --- | --- | --- |\n")
            parts.append(render_schema_markdown(schema))
            parts.append("\n\n")

        for method_name, example in doc.notification_examples.items():
            parts.append(f"**`{method_name}` notification example:**\n\n```json\n")
            parts.append(json.dumps(example, indent=2, default=str)[:3000])
            parts.append("\n```\n\n")

        for note in doc.notes:
            parts.append(f"> {note}\n\n")

        parts.append("---\n\n")

    # Error codes
    parts.append("## Error Codes\n\n")
    parts.append("### REST API Errors\n\n")
    parts.append("Error responses follow this structure:\n\n```json\n")
    parts.append('{\n  "error": {\n    "code": 20001,\n    "message": "Insufficient funds",\n    "description": "Check that the funds are sufficient, given commissions"\n  }\n}\n')
    parts.append("```\n\n")
    parts.append("### WebSocket Errors\n\n")
    parts.append("```json\n")
    parts.append('{\n  "jsonrpc": "2.0",\n  "error": {\n    "code": 20001,\n    "message": "Insufficient funds",\n    "description": "..."\n  },\n  "id": 123\n}\n')
    parts.append("```\n\n")

    parts.append("### Known Error Codes\n\n")
    parts.append("| Code | Message |\n| --- | --- |\n")
    for code, msg in sorted(NONKYC_ERROR_CODES.items()):
        parts.append(f"| {code} | {msg} |\n")
    parts.append("\n")

    # Order lifecycle statuses
    parts.append("## Order Lifecycle\n\n")
    parts.append("Orders progress through these statuses (via `report` WS notifications):\n\n")
    parts.append("| Status | reportType | Description |\n| --- | --- | --- |\n")
    parts.append("| New | `new` | Order accepted and placed on the book |\n")
    parts.append("| Active | `update` | Order modified without a fill |\n")
    parts.append("| Partly Filled | `trade` | Partial fill occurred |\n")
    parts.append("| Filled | `trade` | Fully filled |\n")
    parts.append("| Cancelled | `cancelled` | User-cancelled or system-cancelled |\n\n")

    parts.append("**Order object fields** (from `newOrder` response and `report` notifications):\n\n")
    parts.append("| Field | Type | Description |\n| --- | --- | --- |\n")
    order_fields = [
        ("id", "string", "Exchange-assigned order ID"),
        ("userProvidedId", "string", "User-supplied ID or auto-generated UUID"),
        ("symbol", "string", "Market symbol (e.g., 'ETH/BTC')"),
        ("side", "string", "'buy' or 'sell'"),
        ("type", "string", "'limit' or 'market'"),
        ("price", "string (decimal)", "Order price"),
        ("numberprice", "number", "Price as float (convenience field)"),
        ("quantity", "string (decimal)", "Order quantity"),
        ("executedQuantity", "string (decimal)", "Filled quantity so far"),
        ("remainQuantity", "string (decimal)", "Remaining unfilled quantity"),
        ("remainTotal", "string (decimal)", "Remaining total value"),
        ("remainTotalWithFee", "string (decimal)", "Remaining total including fees"),
        ("lastTradeAt", "integer", "Timestamp of last fill (0 if unfilled)"),
        ("status", "string", "Order status: New, Active, Partly Filled, Filled, Cancelled"),
        ("isActive", "boolean", "Whether order is still active"),
        ("isNew", "boolean", "Whether order was just created"),
        ("createdAt", "integer", "Creation timestamp (Unix ms)"),
        ("updatedAt", "integer", "Last update timestamp (Unix ms)"),
        ("reportType", "string", "Event type: new, trade, cancelled, update, status"),
        ("tradeQuantity", "string (decimal)", "Filled quantity in this trade (only on reportType=trade)"),
        ("tradePrice", "string (decimal)", "Fill price for this trade"),
        ("tradeId", "integer", "Trade ID"),
        ("tradeFee", "string (decimal)", "Fee charged for this trade"),
    ]
    for fname, ftype, fdesc in order_fields:
        parts.append(f"| `{fname}` | {ftype} | {fdesc} |\n")
    parts.append("\n")

    return normalize_blank_lines("".join(parts))


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Documentation rendering — MEXC Spot
# ---------------------------------------------------------------------------

def _render_endpoint_schemas(doc: EndpointDoc, parts: list) -> None:
    """Render request params, documented success schema, live success schema, and/or observed error."""
    has_documented = bool(doc.documented_response_fields or doc.documented_response_example)
    has_live_success = bool(doc.response_schema and doc.response_schema.get("type") and doc.test_status == "pass")
    has_observed_error = doc.observed_error is not None

    # 0. Request parameters (from source docs or test config)
    if doc.request_params:
        # Check if params are dicts with name/type/mandatory/description (from source parser)
        if isinstance(doc.request_params[0], dict) and any(k in doc.request_params[0] for k in ("mandatory", "type", "description")):
            parts.append("**Request Parameters:**\n\n")
            parts.append("| Name | Type | Required | Description |\n| --- | --- | --- | --- |\n")
            for p in doc.request_params:
                name = p.get("name", p.get("parameter", ""))
                ptype = p.get("type", p.get("data_type", ""))
                mand = p.get("mandatory", p.get("required", ""))
                desc = p.get("description", "")
                parts.append(f"| `{name}` | {ptype} | {mand} | {desc} |\n")
            parts.append("\n")
        else:
            # Simple name/example params from test config
            parts.append("**Query Parameters:**\n\n| Name | Example |\n| --- | --- |\n")
            for p in doc.request_params:
                parts.append(f"| `{p.get('name', '')}` | `{p.get('example', '')}` |\n")
            parts.append("\n")

    # 1. Documented success schema (from official source docs)
    if doc.documented_response_fields:
        parts.append("**Documented Response Fields** (from official docs):\n\n")
        # Detect column structure from the parsed data
        has_type_col = any(f.get("type") for f in doc.documented_response_fields)
        if has_type_col:
            parts.append("| Name | Type | Description |\n| --- | --- | --- |\n")
            for f in doc.documented_response_fields:
                parts.append(f"| `{f.get('name', '')}` | {f.get('type', '')} | {f.get('description', '')} |\n")
        else:
            parts.append("| Name | Description |\n| --- | --- |\n")
            for f in doc.documented_response_fields:
                parts.append(f"| `{f.get('name', '')}` | {f.get('description', '')} |\n")
        parts.append("\n")

    if doc.documented_response_example:
        parts.append("**Documented Response Example** (from official docs):\n\n```json\n")
        parts.append(doc.documented_response_example[:2000])
        parts.append("\n```\n\n")

    # 2. Live success schema (from successful test)
    if has_live_success:
        parts.append("**Live Response Schema** (observed):\n\n| Field | Type | Example |\n| --- | --- | --- |\n")
        schema = doc.response_schema
        target = schema["items"] if schema.get("type") == "array" and schema.get("items", {}).get("type") == "object" else schema
        parts.append(render_schema_markdown(target))
        parts.append("\n\n")

    if doc.response_example_truncated is not None and doc.test_status == "pass":
        parts.append("**Live Response Example** (truncated):\n\n```json\n")
        parts.append(json.dumps(redact_value(doc.response_example_truncated), indent=2, default=str)[:2000])
        parts.append("\n```\n\n")

    # 3. If no documented AND no live success, show whatever schema we have (even if error)
    if not has_documented and not has_live_success:
        if doc.response_schema and doc.response_schema.get("type"):
            label = "Observed Error Response" if doc.test_status == "warn" else "Response Schema"
            parts.append(f"**{label}:**\n\n| Field | Type | Example |\n| --- | --- | --- |\n")
            schema = doc.response_schema
            target = schema["items"] if schema.get("type") == "array" and schema.get("items", {}).get("type") == "object" else schema
            parts.append(render_schema_markdown(target))
            parts.append("\n\n")
        if doc.response_example_truncated is not None:
            label = "Observed Error Example" if doc.test_status == "warn" else "Response Example"
            parts.append(f"**{label}** (truncated):\n\n```json\n")
            parts.append(json.dumps(redact_value(doc.response_example_truncated), indent=2, default=str)[:2000])
            parts.append("\n```\n\n")

    # 4. Observed error (when we have documented schema AND a live error)
    if has_observed_error and has_documented:
        parts.append("**Observed Error** (live test returned non-success):\n\n```json\n")
        parts.append(json.dumps(redact_value(truncate_json_for_display(doc.observed_error)), indent=2, default=str)[:1000])
        parts.append("\n```\n\n")


def render_mexc_spot_docs(endpoint_docs: list[EndpointDoc], ws_docs: list[WsMethodDoc]) -> str:
    parts = []
    parts.append("# MEXC Spot V3 — Engineering Reference\n\n")
    parts.append(f"_Generated: {dt.datetime.utcnow().isoformat()}Z_\n\n")

    parts.append("## Overview\n\n")
    parts.append(f"* **REST base**: `{MEXC_SPOT_REST_BASE}`\n")
    parts.append(f"* **WebSocket base**: `{MEXC_SPOT_WS_BASE}`\n")
    parts.append("* **Official docs**: `https://www.mexc.com/api-docs/spot-v3/general-info`\n")
    parts.append("* **Mirror docs**: `https://mexcdevelop.github.io/apidocs/spot_v3_en/`\n\n")

    parts.append("## Authentication\n\n")
    parts.append("### REST API Authentication (HMAC-SHA256)\n\n")
    parts.append("SIGNED endpoints require `timestamp`, optional `recvWindow` (default 5000), and `signature` in the query string or request body.\n\n")
    parts.append("| Header | Description |\n| --- | --- |\n")
    parts.append("| `X-MEXC-APIKEY` | Your public API key |\n")
    parts.append("| `Content-Type` | `application/json` |\n\n")
    parts.append("**Signature construction:**\n\n")
    parts.append("1. Build `totalParams` = query string + request body\n")
    parts.append("2. `signature = HMAC-SHA256(apiSecret, totalParams)`\n")
    parts.append("3. Append `&signature=<hex>` to query string\n\n")

    parts.append("### WebSocket Authentication\n\n")
    parts.append("MEXC spot uses **listen keys** for private WS streams:\n\n")
    parts.append("1. `POST /api/v3/userDataStream` → returns `{\"listenKey\": \"...\"}` (requires signed params in practice)\n")
    parts.append("2. Connect to `wss://wbs-api.mexc.com/ws?listenKey=<key>`\n")
    parts.append("3. Keys expire after 60 minutes. Renew with `PUT /api/v3/userDataStream`\n")
    parts.append("4. Close with `DELETE /api/v3/userDataStream`\n\n")

    parts.append("### Transport Notes\n\n")
    parts.append("* Each public WS connection is valid for up to **24 hours**\n")
    parts.append("* One WS connection supports at most **30 subscriptions**\n")
    parts.append("* Spot WS market data may arrive as **protobuf/base64** frames after the JSON subscription ACK\n\n")

    # Endpoint catalog
    parts.append("## REST API — Endpoint Catalog\n\n")
    parts.append("| Method | Path | Permission | Summary | Tested |\n")
    parts.append("| --- | --- | --- | --- | --- |\n")
    for doc in endpoint_docs:
        t = "✓" if doc.tested and doc.test_status == "pass" else ("⚠" if doc.test_status == "warn" else "✗")
        parts.append(f"| {doc.method} | `{doc.path}` | {doc.permission} | {doc.summary} | {t} |\n")
    parts.append("\n")

    # Endpoint details
    parts.append("## REST API — Endpoint Details\n\n")
    for doc in endpoint_docs:
        parts.append(f"### {doc.method} {doc.path}\n\n")
        parts.append(f"* **Permission**: {doc.permission}\n")
        parts.append(f"* **URL**: `{doc.full_url}`\n")
        if doc.tested:
            e = "✓" if doc.test_status == "pass" else "⚠"
            parts.append(f"* **Test**: {e} HTTP {doc.http_status} ({doc.test_latency_ms}ms)\n")
        parts.append(f"\n{doc.summary}\n\n")
        _render_endpoint_schemas(doc, parts)
        for note in doc.notes:
            parts.append(f"> **Note**: {note}\n\n")
        parts.append("---\n\n")

    # WS details
    if ws_docs:
        parts.append("## WebSocket API\n\n")
        parts.append(f"* **Endpoint**: `{MEXC_SPOT_WS_BASE}`\n\n")
        for doc in ws_docs:
            parts.append(f"### `{doc.method_name}` — {doc.kind} ({doc.permission})\n\n")
            parts.append(f"{doc.description}\n\n")
            if doc.response_example:
                parts.append("**Example:**\n\n```json\n")
                parts.append(json.dumps(redact_value(doc.response_example), indent=2, default=str)[:2000])
                parts.append("\n```\n\n")
            for note in doc.notes:
                parts.append(f"> {note}\n\n")
            parts.append("---\n\n")

    return normalize_blank_lines("".join(parts))


# ---------------------------------------------------------------------------
# Documentation rendering — MEXC Futures
# ---------------------------------------------------------------------------

def render_mexc_futures_docs(endpoint_docs: list[EndpointDoc], ws_docs: list[WsMethodDoc]) -> str:
    parts = []
    parts.append("# MEXC Futures — Engineering Reference\n\n")
    parts.append(f"_Generated: {dt.datetime.utcnow().isoformat()}Z_\n\n")

    parts.append("## Overview\n\n")
    parts.append(f"* **REST base (public)**: `{MEXC_FUTURES_REST_BASE}`\n")
    parts.append(f"* **REST base (canonical)**: `{MEXC_FUTURES_REST_BASE}`\n")
    parts.append(f"* **REST base (private fallback)**: `{MEXC_FUTURES_REST_BASE_ALT}` (see Authentication section)\n")
    parts.append(f"* **WebSocket base**: `{MEXC_FUTURES_WS_BASE}`\n")
    parts.append("* **Official docs**: `https://www.mexc.com/api-docs/futures/integration-guide`\n")
    parts.append("* **Mirror docs**: `https://mexcdevelop.github.io/apidocs/contract_v1_en/`\n\n")

    parts.append("## Authentication\n\n")
    parts.append("Futures uses header-based HMAC-SHA256 authentication.\n\n")
    parts.append("### Required Headers\n\n")
    parts.append("| Header | Description |\n| --- | --- |\n")
    parts.append("| `ApiKey` | Your API key |\n")
    parts.append("| `Request-Time` | Current timestamp in milliseconds |\n")
    parts.append("| `Signature` | HMAC-SHA256 signature (see below) |\n")
    parts.append("| `Content-Type` | `application/json` |\n\n")
    parts.append("Optional: `Recv-Window` (default 5000ms) — reject requests older than this window.\n\n")

    parts.append("### Signing Rules\n\n")
    parts.append("The signature target string is always: `accessKey + timestamp + parameterString`\n\n")
    parts.append("**GET/DELETE requests:**\n")
    parts.append("- `parameterString` = business parameters sorted alphabetically, joined with `&`\n")
    parts.append("- Example: `symbol=BTC_USDT&page_num=1` → sort → `page_num=1&symbol=BTC_USDT`\n")
    parts.append("- Path parameters (e.g. `/{symbol}` in the URL) are **excluded** from the signature\n\n")
    parts.append("**POST requests:**\n")
    parts.append("- `parameterString` = the JSON request body as-is (no dictionary sorting)\n")
    parts.append("- Example: `{\"symbol\":\"BTC_USDT\",\"side\":1,\"vol\":1}`\n\n")
    parts.append("**Signature computation:**\n")
    parts.append("```\nsignature = HMAC-SHA256(apiSecret, apiKey + requestTime + parameterString)\n```\n\n")

    parts.append("### Canonical Base URLs\n\n")
    parts.append("| Context | URL | Source |\n| --- | --- | --- |\n")
    parts.append(f"| Public REST (documented) | `{MEXC_FUTURES_REST_BASE}` | Official docs (2026-01-19 domain change) |\n")
    parts.append(f"| Private REST (observed) | `{MEXC_FUTURES_REST_BASE_ALT}` | Some private endpoints return 400 on api.mexc.com |\n")
    parts.append(f"| WebSocket | `{MEXC_FUTURES_WS_BASE}` | Official docs |\n\n")
    parts.append("> **Discrepancy**: The official docs state `https://api.mexc.com` as the canonical REST base for all endpoints. ")
    parts.append("However, live testing shows some private REST endpoints (`/api/v1/private/*`) fail on `api.mexc.com` and require ")
    parts.append("`contract.mexc.com`. This may be a transitional state. The validator tries `contract.mexc.com` first for private endpoints.\n\n")

    parts.append("### WebSocket Authentication\n\n")
    parts.append("```json\n{\"method\": \"login\", \"param\": {\"apiKey\": \"...\", \"reqTime\": \"...\", \"signature\": \"...\"}}\n```\n")
    parts.append("Success: `{\"channel\": \"rs.login\", \"data\": \"success\"}`\n\n")

    # Catalog
    parts.append("## REST API — Endpoint Catalog\n\n")
    parts.append("| Method | Path | Permission | Summary | Tested |\n")
    parts.append("| --- | --- | --- | --- | --- |\n")
    for doc in endpoint_docs:
        t = "✓" if doc.tested and doc.test_status == "pass" else ("⚠" if doc.test_status == "warn" else "✗")
        parts.append(f"| {doc.method} | `{doc.path}` | {doc.permission} | {doc.summary} | {t} |\n")
    parts.append("\n")

    # Details
    parts.append("## REST API — Endpoint Details\n\n")
    for doc in endpoint_docs:
        parts.append(f"### {doc.method} {doc.path}\n\n")
        parts.append(f"* **Permission**: {doc.permission}\n")
        parts.append(f"* **URL**: `{doc.full_url}`\n")
        if doc.tested:
            e = "✓" if doc.test_status == "pass" else "⚠"
            parts.append(f"* **Test**: {e} HTTP {doc.http_status} ({doc.test_latency_ms}ms)\n")
        parts.append(f"\n{doc.summary}\n\n")
        _render_endpoint_schemas(doc, parts)
        for note in doc.notes:
            parts.append(f"> **Note**: {note}\n\n")
        parts.append("---\n\n")

    # WS
    if ws_docs:
        parts.append("## WebSocket API\n\n")
        parts.append(f"* **Endpoint**: `{MEXC_FUTURES_WS_BASE}`\n\n")
        for doc in ws_docs:
            parts.append(f"### `{doc.method_name}` — {doc.kind} ({doc.permission})\n\n")
            parts.append(f"{doc.description}\n\n")
            if doc.response_schema and doc.response_schema.get("type"):
                parts.append("**Response Schema:**\n\n| Field | Type | Example |\n| --- | --- | --- |\n")
                parts.append(render_schema_markdown(doc.response_schema))
                parts.append("\n\n")
            if doc.response_example:
                parts.append("**Example:**\n\n```json\n")
                parts.append(json.dumps(redact_value(doc.response_example), indent=2, default=str)[:2000])
                parts.append("\n```\n\n")
            for note in doc.notes:
                parts.append(f"> {note}\n\n")
            parts.append("---\n\n")

    return normalize_blank_lines("".join(parts))


# ---------------------------------------------------------------------------
# Source issues report
# ---------------------------------------------------------------------------

def write_source_issues(output_dir: Path) -> None:
    lines = ["# Source and Documentation Issues\n\n"]
    lines.append("Upstream client library bugs and documentation anomalies that engineers should be aware of.\n\n")

    lines.append("## NonKYC Python Client\n\n")
    lines.append("### `ws_unsubscribe_reports` sends `subscribeReports`\n\n")
    lines.append("The official Python client at `NonKYCExchange/NonKycPythonApiClient` defines a method called ")
    lines.append("`ws_unsubscribe_reports` that sends the WS method `subscribeReports` instead of `unsubscribeReports`. ")
    lines.append("This means calling the unsubscribe function will **re-subscribe** instead of unsubscribing.\n\n")
    lines.append("**Impact**: If you copy the official client's unsubscribe logic, report notifications will continue.\n\n")
    lines.append("**Workaround**: Send `{\"method\": \"unsubscribeReports\", \"params\": {}}` directly.\n\n")

    lines.append("### `get_asset_by_id` defined twice with different semantics\n\n")
    lines.append("The Python client defines `get_asset_by_id` for both `/asset/getbyid/{id}` and `/asset/getbyticker/{ticker}`. ")
    lines.append("In Python, the second definition silently shadows the first.\n\n")
    lines.append("**Impact**: Calling `client.get_asset_by_id(some_id)` will actually call `getbyticker`, not `getbyid`.\n\n")
    lines.append("**Workaround**: Call the REST endpoints directly instead of relying on the client wrapper.\n\n")

    lines.append("### NonKYC WebSocket URL mismatch\n\n")
    lines.append("The official WS API docs page references `wss://ws.nonkyc.io` but the Python client uses `wss://api.nonkyc.io`. ")
    lines.append("Live validation confirms `wss://api.nonkyc.io` works. The `ws.nonkyc.io` endpoint may still work but is not tested.\n\n")

    lines.append("### `cancel_order` path drift between Python client and OpenAPI\n\n")
    lines.append("The official Python client uses path `/cancel_order` (with underscore), ")
    lines.append("but the OpenAPI spec documents `/cancelorder` (no underscore). ")
    lines.append("Both may work at runtime, but implementations should use the OpenAPI path `/cancelorder` as canonical.\n\n")
    lines.append("**Impact**: Code derived from the Python client may use the wrong endpoint path.\n\n")
    lines.append("**Workaround**: Use `/cancelorder` as documented in the OpenAPI spec.\n\n")

    lines.append("### `ws_get_asset` sends `getAssets` (plural) instead of `getAsset` (singular)\n\n")
    lines.append("The official Python client method `ws_get_asset(ticker)` sends the WS method `getAssets` (plural) ")
    lines.append("with a `ticker` parameter, rather than `getAsset` (singular). This may work because the server ")
    lines.append("accepts `getAssets` with a ticker filter, but the method name is misleading.\n\n")
    lines.append("**Impact**: The singular `getAsset` WS method may have different behavior or be a separate method entirely.\n\n")
    lines.append("**Workaround**: Test both `getAsset` and `getAssets` with ticker param to confirm server behavior.\n\n")

    lines.append("## MEXC Spot\n\n")
    lines.append("### `POST /api/v3/userDataStream` requires signed parameters despite docs\n\n")
    lines.append("The official MEXC docs state `Parameters: NONE` for creating a listen key. ")
    lines.append("However, live testing shows that a header-only POST returns HTTP 400. ")
    lines.append("A second attempt with signed query parameters (`timestamp`, `recvWindow`, `signature`) succeeds.\n\n")
    lines.append("**Impact**: Implementations that follow the docs literally will fail to create listen keys.\n\n")
    lines.append("**Workaround**: Always sign the request with `timestamp` and `signature` parameters.\n\n")

    lines.append("## MEXC Futures\n\n")
    lines.append("### Private endpoint base URL inconsistency\n\n")
    lines.append("Public futures endpoints work on `https://api.mexc.com/api/v1/contract/...`. ")
    lines.append("Private endpoints under `/api/v1/private/...` may return 400 on `api.mexc.com` and require ")
    lines.append("`https://contract.mexc.com` as the base URL instead.\n\n")
    lines.append("**Impact**: Using a single base URL for all futures endpoints will fail for private calls.\n\n")
    lines.append("**Workaround**: Use `contract.mexc.com` for private futures endpoints, or implement a fallback mechanism.\n\n")

    save_text(output_dir / "source_issues.md", "".join(lines))
    log(f"Wrote source issues: {output_dir / 'source_issues.md'}")


# ---------------------------------------------------------------------------
# Discrepancies report
# ---------------------------------------------------------------------------

def write_discrepancies(output_dir: Path, results: list[ValidationResult]) -> None:
    lines = ["# Documentation vs Live Behavior Discrepancies\n\n"]
    lines.append("Differences between official documentation and actual API behavior observed during live validation.\n\n")

    lines.append("## MEXC Spot\n\n")
    lines.append("### `POST /api/v3/userDataStream` — unsigned request fails\n\n")
    lines.append("| | Documented | Observed |\n| --- | --- | --- |\n")
    lines.append("| Parameters | `NONE` | Requires `timestamp`, `recvWindow`, `signature` |\n")
    lines.append("| Unsigned POST | Should work | Returns HTTP 400 |\n")
    lines.append("| Signed POST | Not mentioned | Returns HTTP 200 with `listenKey` |\n\n")

    lines.append("### Spot WS market data encoding\n\n")
    lines.append("| | Documented | Observed |\n| --- | --- | --- |\n")
    lines.append("| Format | JSON | Subscription ACK is JSON; market data frames are protobuf/base64 |\n\n")
    lines.append("Implementations must decode protobuf frames for actual market data.\n\n")

    lines.append("## MEXC Futures\n\n")
    lines.append("### Private endpoint base URL\n\n")
    lines.append("| | Documented | Observed |\n| --- | --- | --- |\n")
    lines.append("| Base URL | `https://api.mexc.com` | Returns 400 for `/api/v1/private/*` |\n")
    lines.append("| Fallback | Not documented | `https://contract.mexc.com` works |\n\n")

    # Check for the futures API key warning
    for r in results:
        if r.name == "mexc_futures_rest_private_account_assets" and r.status == "warn":
            lines.append("### Account assets endpoint — API key permission\n\n")
            lines.append("| | Expected | Observed |\n| --- | --- | --- |\n")
            lines.append("| Response | Account balances | `{\"code\": 701, \"message\": \"Please enable API Key read access\"}` |\n\n")
            lines.append("This is a credential/permission configuration issue, not a protocol failure. ")
            lines.append("Ensure the API key has 'read' permission enabled for futures.\n\n")

    lines.append("## NonKYC\n\n")
    lines.append("### `/asset/getbyid/{id}` — Cloudflare WAF block\n\n")
    lines.append("| | Documented | Observed |\n| --- | --- | --- |\n")
    lines.append("| Response | Asset object | HTTP 403 Cloudflare block page |\n\n")
    lines.append("This endpoint appears to be blocked by Cloudflare WAF for certain IP ranges/patterns. ")
    lines.append("The alternative `/asset/getbyticker/{ticker}` works and returns the same data.\n\n")

    save_text(output_dir / "discrepancies.md", "".join(lines))
    log(f"Wrote discrepancies: {output_dir / 'discrepancies.md'}")
def write_validation_report(output_dir: Path, results: list[ValidationResult]) -> None:
    lines = ["# Validation Report\n\n"]
    passed = sum(1 for r in results if r.status == "pass")
    warned = sum(1 for r in results if r.status == "warn")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skip")

    lines.append(f"* **Passed**: {passed}\n")
    lines.append(f"* **Warnings**: {warned}\n")
    lines.append(f"* **Failed**: {failed}\n")
    lines.append(f"* **Skipped**: {skipped}\n")
    lines.append(f"* **Total**: {len(results)}\n\n")

    lines.append("| Test | Status | Transport | Auth | HTTP | Latency ms | Target | Details |\n")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    for r in results:
        det = r.details[:100] if r.details else ""
        det = det.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {r.name} | {r.status} | {r.transport} | {r.auth_method or '-'} | "
            f"{r.http_status or '-'} | {r.latency_ms or '-'} | {redact_url(r.target)} | {det} |\n"
        )

    save_text(output_dir / "validation_report.md", "".join(lines))
    log(f"Wrote validation report: {output_dir / 'validation_report.md'}")

def write_observed_schemas(output_dir: Path, results: list[ValidationResult]) -> None:
    lines = ["# Observed Response Schemas\n\n"]
    lines.append("Schemas inferred from live API/WS responses.\n\n")

    for r in results:
        if r.response_schema and r.response_schema.get("type"):
            lines.append(f"## {r.name}\n\n")
            lines.append(f"* Target: `{redact_url(r.target)}`\n")
            lines.append(f"* Status: `{r.status}`\n\n")

            schema = r.response_schema
            if schema.get("type") == "array" and schema.get("items", {}).get("type") == "object":
                lines.append(f"Array of objects ({schema.get('items', {}).get('properties', {}).__len__()} fields):\n\n")
                lines.append("| Field | Type | Example |\n| --- | --- | --- |\n")
                lines.append(render_schema_markdown(schema["items"]))
            elif schema.get("type") == "object":
                lines.append("| Field | Type | Example |\n| --- | --- | --- |\n")
                lines.append(render_schema_markdown(schema))
            else:
                lines.append(f"Type: `{schema.get('type')}`\n")
            lines.append("\n\n")

    save_text(output_dir / "observed_schemas.md", "".join(lines))
    log(f"Wrote observed schemas: {output_dir / 'observed_schemas.md'}")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Quality report — all exchanges
# ---------------------------------------------------------------------------

def write_quality_report(
    output_dir: Path, results: list[ValidationResult],
    nonkyc_endpoint_docs: list[EndpointDoc], nonkyc_ws_docs: list[WsMethodDoc],
    mexc_spot_endpoint_docs: list[EndpointDoc], mexc_spot_ws_docs: list[WsMethodDoc],
    mexc_futures_endpoint_docs: list[EndpointDoc], mexc_futures_ws_docs: list[WsMethodDoc],
) -> list[str]:
    issues = []
    lines = ["# Quality Report\n\n"]
    lines.append(f"* **Script version**: {VERSION}\n")
    lines.append(f"* **Generated**: {dt.datetime.utcnow().isoformat()}Z\n\n")

    def _metrics(label, base, ws_base, ep_docs, ws_docs):
        total_rest = len(ep_docs)
        tested_rest = sum(1 for d in ep_docs if d.tested)
        schema_only = sum(1 for d in ep_docs if d.test_status == "schema_only")
        with_schema = sum(1 for d in ep_docs if d.response_schema)
        with_example = sum(1 for d in ep_docs if d.response_example is not None)
        total_ws = len(ws_docs)
        tested_ws = sum(1 for d in ws_docs if d.tested)
        test_coverage_pct = (tested_rest / total_rest * 100) if total_rest > 0 else 0
        lines.append(f"## {label}\n\n")
        lines.append(f"* REST base: `{base}`\n")
        lines.append(f"* WS base: `{ws_base}`\n")
        lines.append(f"* REST endpoints documented: **{total_rest}** (tested: {tested_rest}, schema-only: {schema_only})\n")
        lines.append(f"* REST test coverage: **{test_coverage_pct:.0f}%** ({tested_rest}/{total_rest})\n")
        lines.append(f"* REST with live response schema: **{with_schema}**\n")
        lines.append(f"* REST with live response example: **{with_example}**\n")
        lines.append(f"* WS methods documented: **{total_ws}** (tested: {tested_ws})\n\n")
        if with_schema == 0 and tested_rest > 0:
            issues.append(f"CRITICAL: {label} has zero response schemas despite {tested_rest} tested endpoints")
        if test_coverage_pct < 50 and total_rest > 5:
            issues.append(f"WARNING: {label} REST test coverage is {test_coverage_pct:.0f}% ({tested_rest}/{total_rest})")
        # Check for placeholder mutating endpoints (no request params)
        placeholders = [d for d in ep_docs if d.test_status == "schema_only"
                        and not d.request_params and not d.request_body
                        and not d.explicit_no_params
                        and d.method in ("POST", "PUT", "DELETE")]
        if placeholders:
            issues.append(f"INFO: {label} has {len(placeholders)} mutating endpoints without request-field tables: "
                         + ", ".join(f"{d.method} {d.path}" for d in placeholders[:5]))
        # Check WS tested coverage
        if total_ws > 5 and tested_ws < 3:
            issues.append(f"INFO: {label} WS coverage low — {tested_ws}/{total_ws} methods tested")

    _metrics("NonKYC", NONKYC_REST_BASE, NONKYC_WS_BASE, nonkyc_endpoint_docs, nonkyc_ws_docs)
    _metrics("MEXC Spot V3", MEXC_SPOT_REST_BASE, MEXC_SPOT_WS_BASE, mexc_spot_endpoint_docs, mexc_spot_ws_docs)
    _metrics("MEXC Futures", MEXC_FUTURES_REST_BASE, MEXC_FUTURES_WS_BASE, mexc_futures_endpoint_docs, mexc_futures_ws_docs)

    # Validation summary by exchange (properly separate mexc_spot and mexc_futures)
    exchanges: dict = {}
    for r in results:
        # Extract exchange key: "mexc_spot" from "mexc_spot_rest_public_ping",
        # "mexc_futures" from "mexc_futures_rest_public_detail", "nonkyc" from "nonkyc_rest_*"
        parts = r.name.split("_")
        if len(parts) >= 2 and parts[0] == "mexc":
            ex = f"{parts[0]}_{parts[1]}"  # "mexc_spot" or "mexc_futures"
        else:
            ex = parts[0]  # "nonkyc"
        if ex not in exchanges:
            exchanges[ex] = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}
        exchanges[ex][r.status] = exchanges[ex].get(r.status, 0) + 1

    lines.append("## Validation Summary\n\n")
    for ex, counts in sorted(exchanges.items()):
        lines.append(f"### {ex}\n\n")
        for status, count in sorted(counts.items()):
            lines.append(f"* {status}: {count}\n")
        lines.append("\n")

    # Duplicate validation ID check
    from collections import Counter
    id_counts = Counter(r.name for r in results)
    dupes = {name: cnt for name, cnt in id_counts.items() if cnt > 1}
    if dupes:
        issues.append(f"Duplicate validation IDs detected: {len(dupes)} IDs are reused")
        lines.append("## Duplicate Validation IDs\n\n")
        lines.append("| ID | Count |\n| --- | --- |\n")
        for name, cnt in sorted(dupes.items(), key=lambda x: -x[1]):
            lines.append(f"| `{name}` | {cnt} |\n")
        lines.append("\n")

    # Hard fail detection
    hard_fails = [r for r in results if r.status == "fail"]
    if hard_fails:
        issues.append(f"WARNING: {len(hard_fails)} hard fail(s) remain: " +
                      ", ".join(f.name for f in hard_fails[:5]))

    if issues:
        lines.append("## Issues\n\n")
        for issue in issues:
            lines.append(f"* {issue}\n")
        lines.append("\n")

    # Source freshness note
    lines.append("## Source Freshness\n\n")
    lines.append("Documentation coverage is bounded by the official source mirrors fetched during the run. ")
    lines.append("If the official docs add new endpoints between fetches, the bundle will lag until re-run.\n\n")
    lines.append("| Exchange | Primary Sources | Freshness Model |\n")
    lines.append("| --- | --- | --- |\n")
    lines.append("| MEXC Spot V3 | Official pages (`mexc.com/api-docs/spot-v3/*`) + GitHub mirror | Fetched live each run |\n")
    lines.append("| MEXC Futures | Official pages (`mexc.com/api-docs/futures/*`) + GitHub mirror | Fetched live each run |\n")
    lines.append("| NonKYC | `api.nonkyc.io/openapi.json` + GitHub clients | Fetched live each run |\n\n")
    lines.append("To check for freshness drift: compare `_raw/catalog.json` endpoint counts against the official docs, ")
    lines.append("or check the fetched `sources/mexc_spot_v3_changelog.md` for items not yet in the endpoint catalog.\n\n")

    save_text(output_dir / "quality_report.md", "".join(lines))
    log(f"Wrote quality report: {output_dir / 'quality_report.md'}")
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    initialize_env_source()
    for msg in ENV_BOOTSTRAP_LOGS:
        log(msg)

    log(f"Script started (v{VERSION})")
    log(f"Options: skip_scrape={args.skip_scrape}, skip_validate={args.skip_validate}, "
        f"skip_private={args.skip_private_validation}, strict={args.strict_quality}")

    auth_config = load_auth_config()
    log(f"Auth: MEXC spot={'enabled' if auth_config.mexc_spot else 'disabled'}, "
        f"MEXC futures={'enabled' if auth_config.mexc_futures else 'disabled'}, "
        f"NonKYC={'enabled' if auth_config.nonkyc else 'disabled'}")

    all_results: list[ValidationResult] = []
    nonkyc_endpoint_docs: list[EndpointDoc] = []
    nonkyc_ws_docs: list[WsMethodDoc] = []
    mexc_spot_endpoint_docs: list[EndpointDoc] = []
    mexc_spot_ws_docs: list[WsMethodDoc] = []
    mexc_futures_endpoint_docs: list[EndpointDoc] = []
    mexc_futures_ws_docs: list[WsMethodDoc] = []
    openapi_spec = None

    async with httpx.AsyncClient(follow_redirects=True) as client:

        # ---- Phase 1: Fetch sources ----
        if not args.skip_scrape:
            log("=== Phase 1: Fetching documentation sources ===")
            manifest = await fetch_sources(client, output_dir)

            # Load browser-scraped sources as supplementary material
            webscrape_dir = Path(args.webscrape_dir)
            log(f"=== Loading webscrape sources from {webscrape_dir} ===")
            manifest = load_webscrape_sources(webscrape_dir, output_dir, manifest)

            save_json(output_dir / "_raw" / "source_manifest.json", manifest)

            openapi_path = output_dir / "sources" / "nonkyc_openapi.json"
            if openapi_path.exists():
                try:
                    openapi_spec = json.loads(openapi_path.read_text())
                    openapi_endpoints = parse_nonkyc_openapi(openapi_spec)
                    log(f"Parsed NonKYC OpenAPI spec: {len(openapi_endpoints)} endpoints")
                    save_json(output_dir / "_raw" / "openapi_parsed.json", openapi_endpoints)
                except Exception as exc:
                    log(f"Failed to parse OpenAPI spec: {exc}")

        # ---- Phase 2: Live validation ----
        if not args.skip_validate:
            log("=== Phase 2: Live REST/WS validation ===")

            # NonKYC REST
            log("--- NonKYC REST ---")
            nk_results, nonkyc_endpoint_docs = await validate_nonkyc_rest(
                client, output_dir, auth_config.nonkyc,
                skip_private=args.skip_private_validation,
            )
            all_results.extend(nk_results)

            # NonKYC WS Public
            log("--- NonKYC WS Public ---")
            nk_ws_results, nk_ws_pub_docs = await validate_nonkyc_ws_public(output_dir)
            all_results.extend(nk_ws_results)
            nonkyc_ws_docs.extend(nk_ws_pub_docs)

            # NonKYC WS Private
            if auth_config.nonkyc and not args.skip_private_validation:
                log("--- NonKYC WS Private ---")
                nk_ws_priv_results, nk_ws_priv_docs = await validate_nonkyc_ws_private(
                    output_dir, auth_config.nonkyc,
                )
                all_results.extend(nk_ws_priv_results)
                nonkyc_ws_docs.extend(nk_ws_priv_docs)

            # MEXC Spot REST
            log("--- MEXC Spot REST ---")
            mexc_spot_results, mexc_spot_endpoint_docs = await validate_mexc_spot_rest(
                client, output_dir, auth_config.mexc_spot,
                skip_private=args.skip_private_validation,
            )
            all_results.extend(mexc_spot_results)

            # MEXC Spot WS
            log("--- MEXC Spot WS ---")
            mexc_spot_ws_results, mexc_spot_ws_pub = await validate_mexc_spot_ws(output_dir)
            all_results.extend(mexc_spot_ws_results)
            mexc_spot_ws_docs.extend(mexc_spot_ws_pub)

            # MEXC Spot Private WS
            if auth_config.mexc_spot and not args.skip_private_validation:
                log("--- MEXC Spot Private WS ---")
                mexc_spot_priv_results, mexc_spot_priv_eps, mexc_spot_priv_ws = await validate_mexc_spot_private_ws(
                    client, output_dir, auth_config.mexc_spot,
                )
                all_results.extend(mexc_spot_priv_results)
                mexc_spot_endpoint_docs.extend(mexc_spot_priv_eps)
                mexc_spot_ws_docs.extend(mexc_spot_priv_ws)

            # MEXC Futures REST
            log("--- MEXC Futures REST ---")
            mexc_fut_results, mexc_futures_endpoint_docs = await validate_mexc_futures_rest(
                client, output_dir, auth_config.mexc_futures,
                skip_private=args.skip_private_validation,
            )
            all_results.extend(mexc_fut_results)

            # MEXC Futures WS
            log("--- MEXC Futures WS ---")
            mexc_fut_ws_results, mexc_futures_ws_pub = await validate_mexc_futures_ws(output_dir, auth_config.mexc_futures)
            all_results.extend(mexc_fut_ws_results)
            mexc_futures_ws_docs.extend(mexc_futures_ws_pub)

    # ---- Phase 3: Generate documentation ----
    log("=== Phase 3: Generating documentation ===")

    # Parse source docs for documented response schemas (used when live test returns errors)
    # Parse source docs for documented response schemas
    # Keys are now "METHOD /path" (e.g. "POST /api/v3/order")
    mexc_spot_source_schemas: dict = {}
    mexc_futures_source_schemas: dict = {}
    sources_dir = output_dir / "sources"
    # Parse ALL fetched MEXC spot source files (mirror + official pages)
    for src_file in sorted(sources_dir.glob("mexc_spot_v3_*.md")):
        parsed = parse_mexc_source_response_schemas(src_file.read_text())
        log(f"Parsed {len(parsed)} schemas from {src_file.name}")
        for key, data in parsed.items():
            if key not in mexc_spot_source_schemas or len(data.get("request_params", [])) > len(mexc_spot_source_schemas.get(key, {}).get("request_params", [])):
                mexc_spot_source_schemas[key] = data
    log(f"Total MEXC Spot source schemas: {len(mexc_spot_source_schemas)}")
    # Parse ALL fetched MEXC futures source files
    for src_file in sorted(sources_dir.glob("mexc_futures_*.md")):
        parsed = parse_mexc_source_response_schemas(src_file.read_text())
        log(f"Parsed {len(parsed)} schemas from {src_file.name}")
        for key, data in parsed.items():
            if key not in mexc_futures_source_schemas or len(data.get("request_params", [])) > len(mexc_futures_source_schemas.get(key, {}).get("request_params", [])):
                mexc_futures_source_schemas[key] = data
    log(f"Total MEXC Futures source schemas: {len(mexc_futures_source_schemas)}")

    # Enrich endpoint docs with source-documented schemas (especially for warn/error endpoints)
    def _enrich_docs(docs: list, source_schemas: dict) -> None:
        for doc in docs:
            path = doc.path
            method = doc.method
            # Try method+path match first, then path-only fallback, then normalized
            key = f"{method} {path}"
            src = source_schemas.get(key)
            if not src:
                norm = re.sub(r'/BTC_USDT|/USDT|/BTC|/\d+', '/{param}', path)
                src = source_schemas.get(f"{method} {norm}")
            if not src:
                # Fallback: try any method at this path (for backward compat)
                for sk, sv in source_schemas.items():
                    if sk.endswith(f" {path}"):
                        src = sv
                        break
            if src:
                if src.get("response_fields"):
                    doc.documented_response_fields = src["response_fields"]
                if src.get("response_example"):
                    doc.documented_response_example = src["response_example"]
                # Enrich request params for schema-only endpoints
                if src.get("request_params") and not doc.request_params:
                    doc.request_params = src["request_params"]
                # Mark endpoints where source explicitly says "Parameters: NONE"
                if src.get("_explicit_no_params"):
                    doc.explicit_no_params = True
            # If test returned warn/error, move live schema to observed_error
            if doc.test_status == "warn" and doc.response_schema:
                doc.observed_error = doc.response_example
                # Only clear live schema if we have a documented one to replace it
                if doc.documented_response_fields or doc.documented_response_example:
                    doc.response_schema = {}
                    doc.response_example = None
                    doc.response_example_truncated = None

    _enrich_docs(mexc_spot_endpoint_docs, mexc_spot_source_schemas)
    _enrich_docs(mexc_futures_endpoint_docs, mexc_futures_source_schemas)

    # Add schema-only (mutating/destructive) endpoints to doc lists
    for ep in MEXC_SPOT_SCHEMA_ONLY:
        mexc_spot_endpoint_docs.append(EndpointDoc(
            method=ep["method"], path=ep["path"],
            full_url=f"{MEXC_SPOT_REST_BASE}{ep['path']}",
            tag=ep.get("section", "Account/Trade"), summary=ep["summary"],
            permission="private", tested=False, test_status="schema_only",
            notes=["Mutating endpoint — documented from source, not tested live."],
        ))
    for ep in MEXC_FUTURES_SCHEMA_ONLY:
        mexc_futures_endpoint_docs.append(EndpointDoc(
            method=ep["method"], path=ep["path"],
            full_url=f"{MEXC_FUTURES_REST_BASE}{ep['path']}",
            tag=ep.get("section", "Order"), summary=ep["summary"],
            permission="private", tested=False, test_status="schema_only",
            notes=["Mutating endpoint — documented from source, not tested live."],
        ))

    # Add schema-only WS channel docs
    for ch in MEXC_SPOT_WS_CHANNELS:
        mexc_spot_ws_docs.append(WsMethodDoc(
            method_name=ch["channel"], kind="subscription", permission="public",
            description=ch["summary"], tested=False, test_status="catalog_only",
        ))
    for ch in MEXC_SPOT_WS_PRIVATE_CHANNELS:
        mexc_spot_ws_docs.append(WsMethodDoc(
            method_name=ch["channel"], kind="subscription", permission="private",
            description=ch["summary"], tested=False, test_status="catalog_only",
            notes=["Requires listen key WS connection."],
        ))
    for ch in MEXC_FUTURES_WS_CHANNELS:
        mexc_futures_ws_docs.append(WsMethodDoc(
            method_name=ch["method"], kind="subscription", permission="public",
            description=ch["summary"], params=ch.get("param", {}),
            tested=False, test_status="catalog_only",
        ))

    # ---- Auto-materialize source-discovered endpoints not yet in doc lists ----
    # This ensures endpoints parsed from official source pages are not silently dropped.
    def _materialize_source_discovered(docs: list, source_schemas: dict, exchange: str, base_url: str) -> int:
        """Add EndpointDoc entries for source-discovered endpoints missing from docs."""
        existing_keys = {(d.method, d.path) for d in docs}
        added = 0
        for key, src in source_schemas.items():
            # Keys are "METHOD /path" format
            parts = key.split(" ", 1)
            if len(parts) != 2:
                continue
            method, path = parts
            # Normalize path: ensure exactly one leading slash, no double slashes
            path = "/" + path.lstrip("/")
            path = re.sub(r'/+', '/', path)
            # Normalize parameterized paths for matching
            norm_path = re.sub(r'/BTC_USDT|/USDT|/BTC|/\d+', '/{param}', path)
            if (method, path) in existing_keys or (method, norm_path) in existing_keys:
                continue
            # Determine permission from path
            perm = "private" if "/private/" in path else "public"
            is_mutating = method in ("POST", "PUT", "DELETE")
            doc = EndpointDoc(
                method=method, path=path,
                full_url=f"{base_url.rstrip('/')}{path}",
                tag="Source-Discovered", summary=f"Discovered from official docs: {method} {path}",
                permission=perm, tested=False, test_status="schema_only",
                notes=["Auto-discovered from official source docs — not in hardcoded test/schema lists."],
            )
            # Attach any parsed fields
            if src.get("response_fields"):
                doc.documented_response_fields = src["response_fields"]
            if src.get("response_example"):
                doc.documented_response_example = src["response_example"]
            if src.get("request_params"):
                doc.request_params = src["request_params"]
            if src.get("_explicit_no_params"):
                doc.explicit_no_params = True
            docs.append(doc)
            existing_keys.add((method, path))
            added += 1
        return added

    spot_added = _materialize_source_discovered(
        mexc_spot_endpoint_docs, mexc_spot_source_schemas, "mexc_spot_v3", MEXC_SPOT_REST_BASE)
    futures_added = _materialize_source_discovered(
        mexc_futures_endpoint_docs, mexc_futures_source_schemas, "mexc_futures", MEXC_FUTURES_REST_BASE)
    if spot_added:
        log(f"  Auto-materialized {spot_added} source-discovered MEXC Spot endpoint(s)")
    if futures_added:
        log(f"  Auto-materialized {futures_added} source-discovered MEXC Futures endpoint(s)")

    # Second enrichment pass — enrich the schema-only endpoints that were just created
    _enrich_docs(mexc_spot_endpoint_docs, mexc_spot_source_schemas)
    _enrich_docs(mexc_futures_endpoint_docs, mexc_futures_source_schemas)

    # Deduplicate endpoint docs by (method, path) — prefer tested over schema-only
    def _dedup_endpoints(docs: list) -> list:
        seen: dict = {}  # key = (method, path)
        for doc in docs:
            key = (doc.method, doc.path)
            if key not in seen:
                seen[key] = doc
            else:
                existing = seen[key]
                # Prefer tested version as base
                if doc.tested and not existing.tested:
                    # Merge documented fields from schema-only into tested
                    if not doc.documented_response_fields and existing.documented_response_fields:
                        doc.documented_response_fields = existing.documented_response_fields
                    if not doc.documented_response_example and existing.documented_response_example:
                        doc.documented_response_example = existing.documented_response_example
                    if not doc.request_params and existing.request_params:
                        doc.request_params = existing.request_params
                    doc.notes.extend(n for n in existing.notes if n not in doc.notes)
                    seen[key] = doc
                elif existing.tested and not doc.tested:
                    # Merge documented fields from schema-only into tested
                    if not existing.documented_response_fields and doc.documented_response_fields:
                        existing.documented_response_fields = doc.documented_response_fields
                    if not existing.documented_response_example and doc.documented_response_example:
                        existing.documented_response_example = doc.documented_response_example
                    if not existing.request_params and doc.request_params:
                        existing.request_params = doc.request_params
                    existing.notes.extend(n for n in doc.notes if n not in existing.notes)
                # else: both tested or both schema-only — keep first
        result = list(seen.values())
        deduped = len(docs) - len(result)
        if deduped:
            log(f"  Deduplicated {deduped} endpoint(s) by (method, path)")
        return result

    mexc_spot_endpoint_docs = _dedup_endpoints(mexc_spot_endpoint_docs)
    mexc_futures_endpoint_docs = _dedup_endpoints(mexc_futures_endpoint_docs)
    nonkyc_endpoint_docs = _dedup_endpoints(nonkyc_endpoint_docs)

    # Parameter inheritance: POST /api/v3/order/test uses same params as POST /api/v3/order
    _inheritance_map = {
        ("POST", "/api/v3/order/test"): ("POST", "/api/v3/order"),
    }
    for docs_list in [mexc_spot_endpoint_docs, mexc_futures_endpoint_docs]:
        by_key = {(d.method, d.path): d for d in docs_list}
        for (child_method, child_path), (parent_method, parent_path) in _inheritance_map.items():
            child = by_key.get((child_method, child_path))
            parent = by_key.get((parent_method, parent_path))
            if child and parent and not child.request_params and parent.request_params:
                child.request_params = parent.request_params
                child.notes.append(f"Request parameters same as `{parent_method} {parent_path}`")

    # NonKYC
    nonkyc_docs_text = render_nonkyc_docs(nonkyc_endpoint_docs, nonkyc_ws_docs, openapi_spec)
    save_text(output_dir / "nonkyc.md", nonkyc_docs_text)
    log(f"Wrote NonKYC docs: {output_dir / 'nonkyc.md'} ({len(nonkyc_docs_text)} chars)")

    # MEXC Spot
    mexc_spot_text = render_mexc_spot_docs(mexc_spot_endpoint_docs, mexc_spot_ws_docs)
    save_text(output_dir / "mexc_spot_v3.md", mexc_spot_text)
    log(f"Wrote MEXC Spot docs: {output_dir / 'mexc_spot_v3.md'} ({len(mexc_spot_text)} chars)")

    # MEXC Futures
    mexc_futures_text = render_mexc_futures_docs(mexc_futures_endpoint_docs, mexc_futures_ws_docs)
    save_text(output_dir / "mexc_futures.md", mexc_futures_text)
    log(f"Wrote MEXC Futures docs: {output_dir / 'mexc_futures.md'} ({len(mexc_futures_text)} chars)")

    # Reports
    if all_results:
        write_validation_report(output_dir, all_results)
        write_observed_schemas(output_dir, all_results)

        # Machine-readable validation results
        validation_json = []
        for r in all_results:
            entry = {
                "id": r.name, "status": r.status, "transport": r.transport,
                "http_status": r.http_status, "latency_ms": r.latency_ms,
                "target": redact_url(r.target), "details": r.details or "",
            }
            if r.auth_method:
                entry["auth_method"] = r.auth_method
            if r.observed_fields:
                entry["observed_field_count"] = len(r.observed_fields)
            if r.sample_path:
                entry["sample_path"] = r.sample_path
            validation_json.append(entry)
        save_json(output_dir / "_raw" / "validation_results.json", validation_json)
        log(f"Wrote {len(validation_json)} validation results to _raw/validation_results.json")

    issues = write_quality_report(
        output_dir, all_results,
        nonkyc_endpoint_docs, nonkyc_ws_docs,
        mexc_spot_endpoint_docs, mexc_spot_ws_docs,
        mexc_futures_endpoint_docs, mexc_futures_ws_docs,
    )

    write_source_issues(output_dir)
    write_discrepancies(output_dir, all_results)

    # ---- Machine-readable catalog ----
    catalog = {
        "version": VERSION,
        "generated": dt.datetime.utcnow().isoformat() + "Z",
        "exchanges": {
            "nonkyc": {
                "rest_base": NONKYC_REST_BASE,
                "ws_base": NONKYC_WS_BASE,
                "endpoints": [
                    {"method": d.method, "path": d.path, "permission": d.permission,
                     "tag": d.tag, "summary": d.summary, "tested": d.tested,
                     "test_status": d.test_status, "http_status": d.http_status}
                    for d in nonkyc_endpoint_docs
                ],
                "ws_methods": [
                    {"method": d.method_name, "kind": d.kind, "permission": d.permission,
                     "description": d.description, "tested": d.tested, "test_status": d.test_status}
                    for d in nonkyc_ws_docs
                ],
            },
            "mexc_spot_v3": {
                "rest_base": MEXC_SPOT_REST_BASE,
                "ws_base": MEXC_SPOT_WS_BASE,
                "endpoints": [
                    {"method": d.method, "path": d.path, "permission": d.permission,
                     "tag": d.tag, "summary": d.summary, "tested": d.tested,
                     "test_status": d.test_status, "http_status": d.http_status}
                    for d in mexc_spot_endpoint_docs
                ],
                "ws_methods": [
                    {"method": d.method_name, "kind": d.kind, "permission": d.permission,
                     "description": d.description, "tested": d.tested, "test_status": d.test_status}
                    for d in mexc_spot_ws_docs
                ],
            },
            "mexc_futures": {
                "rest_base": MEXC_FUTURES_REST_BASE,
                "rest_base_private": MEXC_FUTURES_REST_BASE_ALT,
                "ws_base": MEXC_FUTURES_WS_BASE,
                "endpoints": [
                    {"method": d.method, "path": d.path, "permission": d.permission,
                     "tag": d.tag, "summary": d.summary, "tested": d.tested,
                     "test_status": d.test_status, "http_status": d.http_status}
                    for d in mexc_futures_endpoint_docs
                ],
                "ws_methods": [
                    {"method": d.method_name, "kind": d.kind, "permission": d.permission,
                     "description": d.description, "tested": d.tested, "test_status": d.test_status}
                    for d in mexc_futures_ws_docs
                ],
            },
        },
    }
    save_json(output_dir / "_raw" / "catalog.json", catalog)
    log(f"Wrote machine-readable catalog: {output_dir / '_raw' / 'catalog.json'}")

    # ---- Run manifest ----
    passed = sum(1 for r in all_results if r.status == "pass")
    failed = sum(1 for r in all_results if r.status == "fail")
    warned = sum(1 for r in all_results if r.status == "warn")
    skipped = sum(1 for r in all_results if r.status == "skip")

    run_manifest = {
        "version": VERSION,
        "generated": dt.datetime.utcnow().isoformat() + "Z",
        "options": {
            "skip_scrape": args.skip_scrape,
            "skip_validate": args.skip_validate,
            "skip_private_validation": args.skip_private_validation,
            "strict_quality": args.strict_quality,
        },
        "auth": {
            "mexc_spot": "enabled" if auth_config.mexc_spot else "disabled",
            "mexc_futures": "enabled" if auth_config.mexc_futures else "disabled",
            "nonkyc": "enabled" if auth_config.nonkyc else "disabled",
        },
        "validation": {
            "total": len(all_results),
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "skipped": skipped,
        },
        "documentation": {
            "nonkyc": {"rest_endpoints": len(nonkyc_endpoint_docs), "ws_methods": len(nonkyc_ws_docs)},
            "mexc_spot_v3": {"rest_endpoints": len(mexc_spot_endpoint_docs), "ws_methods": len(mexc_spot_ws_docs)},
            "mexc_futures": {"rest_endpoints": len(mexc_futures_endpoint_docs), "ws_methods": len(mexc_futures_ws_docs)},
        },
        "output_files": [
            "nonkyc.md", "mexc_spot_v3.md", "mexc_futures.md",
            "validation_report.md", "quality_report.md",
            "source_issues.md", "discrepancies.md", "observed_schemas.md",
            "docs_index.md", "_raw/catalog.json", "_raw/run_manifest.json",
        ],
    }
    save_json(output_dir / "_raw" / "run_manifest.json", run_manifest)
    log(f"Wrote run manifest: {output_dir / '_raw' / 'run_manifest.json'}")

    # Write run log
    save_text(output_dir.parent / "run.log", "\n".join(_LOG_LINES) + "\n")

    # Write docs index
    index_lines = ["# Documentation Index\n\n"]
    index_lines.append("| File | Description |\n| --- | --- |\n")
    index_lines.append("| `nonkyc.md` | Complete NonKYC engineering reference (REST + WS + schemas + examples) |\n")
    index_lines.append("| `mexc_spot_v3.md` | Complete MEXC Spot V3 engineering reference (REST + WS + schemas + examples) |\n")
    index_lines.append("| `mexc_futures.md` | Complete MEXC Futures engineering reference (REST + WS + schemas + examples) |\n")
    index_lines.append("| `validation_report.md` | Live test results for all endpoints |\n")
    index_lines.append("| `quality_report.md` | Documentation completeness metrics for all exchanges |\n")
    index_lines.append("| `source_issues.md` | Upstream client library bugs and documentation anomalies |\n")
    index_lines.append("| `discrepancies.md` | Documented behavior vs live-observed behavior differences |\n")
    index_lines.append("| `observed_schemas.md` | Response schemas inferred from live data |\n")
    index_lines.append("| `sources/` | Raw fetched documentation sources |\n")
    index_lines.append("| `_raw/catalog.json` | Machine-readable endpoint catalog for all exchanges |\n")
    index_lines.append("| `_raw/run_manifest.json` | Run metadata, timing, pass/fail counts |\n")
    index_lines.append("| `_raw/response_samples/` | Full response samples from live tests |\n")
    if openapi_spec:
        index_lines.append("| `_raw/openapi_parsed.json` | Parsed NonKYC OpenAPI endpoints |\n")
    save_text(output_dir / "docs_index.md", "".join(index_lines))

    # Summary
    log(f"DONE. Tests: {passed} passed, {warned} warned, {failed} failed, {len(all_results)} total")
    log(f"NonKYC: {len(nonkyc_endpoint_docs)} REST, {len(nonkyc_ws_docs)} WS")
    log(f"MEXC Spot: {len(mexc_spot_endpoint_docs)} REST, {len(mexc_spot_ws_docs)} WS")
    log(f"MEXC Futures: {len(mexc_futures_endpoint_docs)} REST, {len(mexc_futures_ws_docs)} WS")

    if args.strict_quality and issues:
        blocking_issues = [i for i in issues if not i.startswith("INFO:")]
        if blocking_issues:
            log(f"Strict quality: FAILING due to {len(blocking_issues)} blocking issue(s)")
            for bi in blocking_issues:
                log(f"  BLOCKING: {bi}")
            return 1
        else:
            log(f"Strict quality: PASSING ({len(issues)} INFO-level items, no blocking issues)")

    return 0
def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Comprehensive exchange documentation builder and validator"
    )
    parser.add_argument("--output-dir", default="./documents", help="Output directory")
    parser.add_argument("--webscrape-dir", default="./webscrape", help="Directory containing browser-scraped HTML files")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip source fetching")
    parser.add_argument("--skip-validate", action="store_true", help="Skip live validation")
    parser.add_argument("--skip-private-validation", action="store_true", help="Skip private/auth tests")
    parser.add_argument("--strict-quality", action="store_true", help="Exit non-zero on quality issues")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)