"""Public REST screener for MEXC spot markets.

Uses only unauthenticated market-data endpoints.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional

import pandas as pd

from pmm_lab.screener.common import (
    PublicExchangeScreener,
    ScreenerConfig,
    compute_candle_metrics,
    compute_orderbook_metrics,
    compute_trade_metrics,
    records_to_frame,
    safe_float,
    safe_int,
    should_exclude_symbol,
    to_hb_pair,
)


MEXC_BASE_URL = "https://api.mexc.com"



def default_mexc_config() -> ScreenerConfig:
    """Conservative default gates for public MEXC screening."""

    return ScreenerConfig(
        connector="mexc",
        quote_asset="USDT",
        interval="5m",
        universe_top_k=100,
        final_top_n=30,
        candle_limit=288,
        depth_limit=200,
        recent_trade_limit=500,
        request_pause_sec=0.12,
        timeout_seconds=30.0,
        max_retries=3,
        retry_backoff=1.8,
        min_quote_volume_24h=1_000_000.0,
        max_spread_bps=50.0,
        min_top_of_book_quote=250.0,
        min_depth_10bps_quote=1_000.0,
        max_last_trade_age_sec=1800.0,
        min_recent_trade_count=100,
        min_candle_count=240,
        min_candle_coverage_ratio=0.97,
        max_zero_volume_fraction=0.20,
        min_natr_bps=10.0,
        max_natr_bps=250.0,
        natr_soft_min=6.0,
        natr_target_min=15.0,
        natr_target_max=120.0,
        natr_soft_max=250.0,
        efficiency_soft_min=0.00,
        efficiency_target_min=0.05,
        efficiency_target_max=0.40,
        efficiency_soft_max=0.75,
        vol_to_spread_soft_min=1.0,
        vol_to_spread_target_min=3.0,
        vol_to_spread_target_max=20.0,
        vol_to_spread_soft_max=50.0,
    )


class MEXCPublicScreener(PublicExchangeScreener):
    """Screen MEXC spot pairs using public REST endpoints only."""

    base_url = MEXC_BASE_URL

    @staticmethod
    def _build_universe_frame(
        exchange_info: Mapping[str, Any],
        tickers_24h: Any,
        book_tickers: Any,
        config: Optional[ScreenerConfig] = None,
    ) -> pd.DataFrame:
        cfg = config or default_mexc_config()

        tickers = tickers_24h if isinstance(tickers_24h, list) else [tickers_24h]
        books = book_tickers if isinstance(book_tickers, list) else [book_tickers]
        ticker_by_symbol = {
            str(item.get("symbol", "")).upper(): item
            for item in tickers
            if isinstance(item, Mapping) and item.get("symbol")
        }
        book_by_symbol = {
            str(item.get("symbol", "")).upper(): item
            for item in books
            if isinstance(item, Mapping) and item.get("symbol")
        }

        rows: list[dict[str, Any]] = []
        for raw in exchange_info.get("symbols", []):
            if not isinstance(raw, Mapping):
                continue
            exchange_symbol = str(raw.get("symbol", "")).upper()
            base_asset = str(raw.get("baseAsset", "")).upper()
            quote_asset = str(raw.get("quoteAsset", "")).upper()
            if not exchange_symbol or not base_asset or not quote_asset:
                continue
            if not cfg.matches_quote_asset(quote_asset):
                continue
            if should_exclude_symbol(base_asset, exchange_symbol, cfg):
                continue

            permissions = {str(p).upper() for p in raw.get("permissions", [])}
            is_spot_permissioned = (not permissions) or ("SPOT" in permissions)
            status_value = str(raw.get("status", ""))
            is_active = status_value == "1" and is_spot_permissioned and (not bool(raw.get("st", False)))

            ticker = ticker_by_symbol.get(exchange_symbol, {})
            book = book_by_symbol.get(exchange_symbol, {})

            last_price = safe_float(ticker.get("lastPrice"))
            volume_base = safe_float(ticker.get("volume"))
            quote_volume = safe_float(ticker.get("quoteVolume"))
            if math.isnan(quote_volume) and not math.isnan(last_price) and not math.isnan(volume_base):
                quote_volume = last_price * volume_base

            bid_price = safe_float(book.get("bidPrice") or ticker.get("bidPrice"))
            bid_qty = safe_float(book.get("bidQty") or ticker.get("bidQty"))
            ask_price = safe_float(book.get("askPrice") or ticker.get("askPrice"))
            ask_qty = safe_float(book.get("askQty") or ticker.get("askQty"))
            mid_price = (bid_price + ask_price) / 2.0 if bid_price > 0 and ask_price > 0 else math.nan
            spread_bps = ((ask_price - bid_price) / mid_price * 10_000.0) if mid_price and mid_price > 0 else math.nan
            top_of_book_quote = (
                min(bid_price * bid_qty, ask_price * ask_qty)
                if bid_price > 0 and ask_price > 0 and bid_qty > 0 and ask_qty > 0
                else math.nan
            )

            quote_precision = safe_int(raw.get("quotePrecision"), default=-1)
            base_asset_precision = safe_int(raw.get("baseAssetPrecision"), default=-1)
            price_tick_estimate = 10.0 ** (-quote_precision) if quote_precision >= 0 else math.nan
            amount_step_estimate = safe_float(raw.get("baseSizePrecision"))
            if math.isnan(amount_step_estimate) and base_asset_precision >= 0:
                amount_step_estimate = 10.0 ** (-base_asset_precision)
            min_order_size_base_estimate = safe_float(raw.get("baseSizePrecision"))
            min_notional_quote_estimate = safe_float(raw.get("quoteAmountPrecision"))

            rows.append(
                {
                    "connector": cfg.connector,
                    "exchange_symbol": exchange_symbol,
                    "trading_pair": to_hb_pair(base_asset, quote_asset),
                    "base_asset": base_asset,
                    "quote_asset": quote_asset,
                    "is_active": is_active,
                    "status_detail": status_value,
                    "permissions_spot": is_spot_permissioned,
                    "last_price": last_price,
                    "quote_volume_24h": quote_volume,
                    "volume_base_24h": volume_base,
                    "bid_price": bid_price,
                    "bid_quantity": bid_qty,
                    "ask_price": ask_price,
                    "ask_quantity": ask_qty,
                    "spread_bps": max(spread_bps, 0.0) if not math.isnan(spread_bps) else spread_bps,
                    "top_of_book_quote": top_of_book_quote,
                    "price_tick_estimate": price_tick_estimate,
                    "amount_step_estimate": amount_step_estimate,
                    "min_order_size_base_estimate": min_order_size_base_estimate,
                    "min_notional_quote_estimate": min_notional_quote_estimate,
                    "maker_fee_estimate": safe_float(raw.get("makerCommission")),
                    "taker_fee_estimate": safe_float(raw.get("takerCommission")),
                    "rule_estimate_source": "exchangeInfo.quotePrecision/baseSizePrecision/quoteAmountPrecision",
                    "raw_trade_side_type": raw.get("tradeSideType"),
                    "book_crossed": bool(ask_price > 0 and bid_price > 0 and ask_price <= bid_price),
                }
            )

        return records_to_frame(rows)

    def build_universe(self) -> pd.DataFrame:
        exchange_info = self.client.get("/api/v3/exchangeInfo")
        tickers_24h = self.client.get("/api/v3/ticker/24hr")
        book_tickers = self.client.get("/api/v3/ticker/bookTicker")
        return self._build_universe_frame(exchange_info, tickers_24h, book_tickers, self.config)

    def _fetch_orderbook(self, exchange_symbol: str) -> dict[str, Any]:
        return self.client.get(
            "/api/v3/depth",
            params={"symbol": exchange_symbol, "limit": self.config.depth_limit},
        )

    def _fetch_candles(self, exchange_symbol: str) -> pd.DataFrame:
        payload = self.client.get(
            "/api/v3/klines",
            params={
                "symbol": exchange_symbol,
                "interval": self.config.interval,
                "limit": self.config.candle_limit,
            },
        )
        rows: list[dict[str, Any]] = []
        for item in payload or []:
            if not isinstance(item, (list, tuple)) or len(item) < 6:
                continue
            rows.append(
                {
                    "timestamp": safe_float(item[0]),
                    "open": safe_float(item[1]),
                    "high": safe_float(item[2]),
                    "low": safe_float(item[3]),
                    "close": safe_float(item[4]),
                    "volume": safe_float(item[5]),
                    "quote_volume": safe_float(item[7]) if len(item) > 7 else math.nan,
                }
            )
        return records_to_frame(rows)

    def _fetch_trades(self, exchange_symbol: str) -> pd.DataFrame:
        payload = self.client.get(
            "/api/v3/aggTrades",
            params={"symbol": exchange_symbol, "limit": self.config.recent_trade_limit},
        )
        rows: list[dict[str, Any]] = []
        for item in payload or []:
            if not isinstance(item, Mapping):
                continue
            price = safe_float(item.get("p"))
            qty = safe_float(item.get("q"))
            if math.isnan(price) or math.isnan(qty):
                continue
            rows.append(
                {
                    "timestamp": safe_float(item.get("T")),
                    "price": price,
                    "quantity": qty,
                    "quote_quantity": price * qty,
                    # Binance/MEXC style: m=True means buyer was maker => sell aggressor.
                    "side": "sell" if bool(item.get("m")) else "buy",
                }
            )
        return records_to_frame(rows)

    def enrich_pair(self, row: Mapping[str, Any]) -> dict[str, Any]:
        exchange_symbol = str(row["exchange_symbol"])
        orderbook = self._fetch_orderbook(exchange_symbol)
        candles = self._fetch_candles(exchange_symbol)
        trades = self._fetch_trades(exchange_symbol)

        orderbook_metrics = compute_orderbook_metrics(orderbook.get("bids"), orderbook.get("asks"))
        candle_metrics = compute_candle_metrics(candles, interval_seconds=self.config.interval_seconds())
        trade_metrics = compute_trade_metrics(trades)

        return {
            **orderbook_metrics,
            **candle_metrics,
            **trade_metrics,
        }
