"""Public REST screener for NonKYC spot markets."""

from __future__ import annotations

import logging
import math
from typing import Any, Mapping, Optional

import pandas as pd

log = logging.getLogger(__name__)

from pmm_lab.screener.common import (
    PublicExchangeScreener,
    ScreenerConfig,
    compute_candle_metrics,
    compute_orderbook_metrics,
    compute_trade_metrics,
    hb_to_slash_pair,
    records_to_frame,
    safe_float,
    safe_int,
    should_exclude_symbol,
    to_hb_pair,
)


NONKYC_BASE_URL = "https://api.nonkyc.io/api/v2"
NONKYC_INTERVAL_TO_MINUTES = {
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "3h": 180,
    "4h": 240,
    "8h": 480,
    "12h": 720,
    "1d": 1440,
}



def _normalize_nonkyc_symbol(symbol: str) -> str:
    return str(symbol).upper().replace("_", "/")



def default_nonkyc_config() -> ScreenerConfig:
    """Venue-calibrated defaults for public NonKYC screening.

    NonKYC is a thin, wide-spread exchange. The 10bps depth gate is
    disabled because half-spreads routinely exceed 10bps, making
    sym_depth_quote_10bps structurally zero. Touch liquidity
    (top_of_book_quote) is the primary hard gate instead.

    Thresholds derived from quant expert review (2026-03).
    """

    return ScreenerConfig(
        connector="nonkyc",
        quote_asset="*",  # Screen all available quote assets (USDT, XMR, BTC, USDC, etc.)
        interval="5m",
        universe_top_k=80,
        final_top_n=15,
        candle_limit=288,
        depth_limit=200,
        recent_trade_limit=500,
        request_pause_sec=0.20,
        timeout_seconds=30.0,
        max_retries=3,
        retry_backoff=1.8,
        # --- Quant-expert-calibrated thresholds for NonKYC ---
        min_quote_volume_24h=50_000.0,
        max_spread_bps=120.0,
        min_top_of_book_quote=5.0,
        min_depth_10bps_quote=0.0,       # DISABLED — structurally zero on wide-spread venue
        min_depth_50bps_quote=0.0,        # soft rank only for now
        min_depth_1xspread_quote=0.0,     # soft rank only for now
        max_last_trade_age_sec=3600.0,
        min_recent_trade_count=40,
        min_candle_count=220,
        min_candle_coverage_ratio=0.90,
        max_zero_volume_fraction=0.30,
        min_natr_bps=12.0,
        max_natr_bps=400.0,
        natr_soft_min=8.0,
        natr_target_min=20.0,
        natr_target_max=180.0,
        natr_soft_max=350.0,
        efficiency_soft_min=0.00,
        efficiency_target_min=0.05,
        efficiency_target_max=0.45,
        efficiency_soft_max=0.80,
        vol_to_spread_soft_min=1.0,
        vol_to_spread_target_min=3.0,
        vol_to_spread_target_max=25.0,
        vol_to_spread_soft_max=60.0,
        # --- Fallback ranked selection ---
        fallback_if_empty=True,
    )


class NonKYCPublicScreener(PublicExchangeScreener):
    """Screen NonKYC spot pairs using public REST endpoints only."""

    base_url = NONKYC_BASE_URL

    @staticmethod
    def _build_universe_frame(
        market_list: Any,
        tickers: Any,
        config: Optional[ScreenerConfig] = None,
    ) -> pd.DataFrame:
        cfg = config or default_nonkyc_config()

        ticker_list = tickers if isinstance(tickers, list) else [tickers]
        ticker_by_symbol: dict[str, Mapping[str, Any]] = {}
        for item in ticker_list:
            if not isinstance(item, Mapping):
                continue
            if str(item.get("type", "market")).lower() != "market":
                continue
            symbol = _normalize_nonkyc_symbol(item.get("ticker_id") or item.get("symbol") or "")
            if symbol:
                ticker_by_symbol[symbol] = item

        rows: list[dict[str, Any]] = []
        for raw in market_list or []:
            if not isinstance(raw, Mapping):
                continue
            exchange_symbol = _normalize_nonkyc_symbol(raw.get("symbol", ""))
            if not exchange_symbol or "/" not in exchange_symbol:
                continue
            base_asset, quote_asset = exchange_symbol.split("/", 1)
            if not cfg.matches_quote_asset(quote_asset):
                continue
            if should_exclude_symbol(base_asset, exchange_symbol, cfg):
                continue

            ticker = ticker_by_symbol.get(exchange_symbol, {})
            is_active = bool(raw.get("isActive", False)) and str(ticker.get("type", "market")).lower() in {"market", ""}

            last_price = safe_float(ticker.get("last_price") or raw.get("lastPrice"))
            volume_base = safe_float(ticker.get("base_volume") or raw.get("volume"))
            quote_volume = safe_float(ticker.get("target_volume"))
            if math.isnan(quote_volume) and not math.isnan(last_price) and not math.isnan(volume_base):
                quote_volume = last_price * volume_base

            bid_price = safe_float(ticker.get("bid"))
            ask_price = safe_float(ticker.get("ask"))
            mid_price = (bid_price + ask_price) / 2.0 if bid_price > 0 and ask_price > 0 else math.nan
            spread_bps = ((ask_price - bid_price) / mid_price * 10_000.0) if mid_price and mid_price > 0 else math.nan

            price_decimals = safe_int(raw.get("priceDecimals"), default=-1)
            quantity_decimals = safe_int(raw.get("quantityDecimals"), default=-1)
            price_tick_estimate = 10.0 ** (-price_decimals) if price_decimals >= 0 else math.nan
            amount_step_estimate = 10.0 ** (-quantity_decimals) if quantity_decimals >= 0 else math.nan

            rows.append(
                {
                    "connector": cfg.connector,
                    "exchange_symbol": exchange_symbol,
                    "trading_pair": to_hb_pair(base_asset, quote_asset),
                    "base_asset": base_asset,
                    "quote_asset": quote_asset,
                    "is_active": is_active,
                    "status_detail": "active" if is_active else "inactive",
                    "last_price": last_price,
                    "quote_volume_24h": quote_volume,
                    "volume_base_24h": volume_base,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "spread_bps": max(spread_bps, 0.0) if not math.isnan(spread_bps) else spread_bps,
                    # top_of_book_quote is unknown until we query the orderbook.
                    "top_of_book_quote": math.nan,
                    "price_tick_estimate": price_tick_estimate,
                    "amount_step_estimate": amount_step_estimate,
                    "min_order_size_base_estimate": math.nan,
                    "min_notional_quote_estimate": math.nan,
                    "rule_estimate_source": "market.getlist.priceDecimals/quantityDecimals",
                    "last_trade_at_ms": safe_float(raw.get("lastTradeAt")),
                    "book_crossed": False,
                }
            )

        return records_to_frame(rows)

    def build_universe(self) -> pd.DataFrame:
        market_list = self.client.get("/market/getlist")
        tickers = self.client.get("/tickers")
        return self._build_universe_frame(market_list, tickers, self.config)

    def _fetch_orderbook(self, exchange_symbol: str) -> dict[str, Any]:
        try:
            return self.client.get(
                "/market/orderbook",
                params={"symbol": exchange_symbol, "limit": self.config.depth_limit},
            )
        except Exception:
            # Fallback to CMC-compatible endpoint
            return self.client.get(
                "/orderbook",
                params={"ticker_id": exchange_symbol.replace("/", "_"), "depth": self.config.depth_limit},
            )

    def _fetch_candles(self, exchange_symbol: str) -> pd.DataFrame:
        resolution = NONKYC_INTERVAL_TO_MINUTES.get(self.config.interval)
        if resolution is None:
            raise ValueError(f"NonKYC does not support interval {self.config.interval}")
        payload = self.client.get(
            "/market/candles",
            params={
                "symbol": exchange_symbol,
                "resolution": resolution,
                "countBack": self.config.candle_limit,
                "firstDataRequest": 1,
            },
        )
        rows: list[dict[str, Any]] = []
        for item in (payload or {}).get("bars", []):
            if not isinstance(item, Mapping):
                continue
            rows.append(
                {
                    "timestamp": safe_float(item.get("time")),
                    "open": safe_float(item.get("open")),
                    "high": safe_float(item.get("high")),
                    "low": safe_float(item.get("low")),
                    "close": safe_float(item.get("close")),
                    "volume": safe_float(item.get("volume")),
                }
            )
        return records_to_frame(rows)

    def _fetch_trades(self, exchange_symbol: str) -> pd.DataFrame:
        """Fetch recent trades from NonKYC /market/trades.

        Live API probe (2026-03-23) confirmed the response is a flat JSON array:
        [{"id", "price", "type", "baseVolume", "quoteVolume", "timestamp"}, ...]

        Field mapping (verified against live API):
          - price     → "price" (string)
          - quantity  → "baseVolume" (string) — NOT "amount" or "quantity"
          - quote qty → "quoteVolume" (string)
          - side      → "type" (string: "buy"/"sell") — NOT "side"
          - timestamp → "timestamp" (int, milliseconds)
        """
        payload = self.client.get(
            "/market/trades",
            params={"symbol": exchange_symbol, "limit": self.config.recent_trade_limit},
        )
        trade_list = payload if isinstance(payload, list) else []
        rows: list[dict[str, Any]] = []
        for item in trade_list:
            if not isinstance(item, Mapping):
                continue
            price = safe_float(item.get("price"))
            qty = safe_float(item.get("baseVolume"))
            if math.isnan(price) or math.isnan(qty):
                continue

            quote_qty = safe_float(item.get("quoteVolume"))
            if math.isnan(quote_qty):
                quote_qty = price * qty

            rows.append(
                {
                    "timestamp": item.get("timestamp"),
                    "price": price,
                    "quantity": qty,
                    "quote_quantity": quote_qty,
                    "side": str(item.get("type", "")).lower(),
                }
            )
        return records_to_frame(rows)

    def enrich_pair(self, row: Mapping[str, Any]) -> dict[str, Any]:
        exchange_symbol = str(row["exchange_symbol"])
        orderbook = self._fetch_orderbook(exchange_symbol)
        candles = self._fetch_candles(exchange_symbol)
        trades = self._fetch_trades(exchange_symbol)

        # Orderbook response is a dict with "bids" and "asks" arrays
        # (verified: {"marketid", "symbol", "timestamp", "sequence", "bids", "asks"})
        bids = orderbook.get("bids") if isinstance(orderbook, Mapping) else None
        asks = orderbook.get("asks") if isinstance(orderbook, Mapping) else None

        orderbook_metrics = compute_orderbook_metrics(bids, asks)
        candle_metrics = compute_candle_metrics(candles, interval_seconds=self.config.interval_seconds())
        trade_metrics = compute_trade_metrics(trades)

        return {
            **orderbook_metrics,
            **candle_metrics,
            **trade_metrics,
        }
