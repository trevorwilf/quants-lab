"""Daily and minute bar fetchers with full pagination.

The Alpaca multi-symbol bar endpoint returns results sorted by symbol and then
timestamp; the response includes ``next_page_token`` when more data is available.
This module always paginates until exhaustion and never assumes one request
returns all symbols (per ``[Report §9.2]``).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Iterable

import pandas as pd

from bowaka_common.data.alpaca_client import AlpacaClient


def _normalize_bar_row(symbol: str, row: Any) -> dict[str, Any]:
    """Build a flat dict per bar regardless of source (alpaca-py model or dict)."""
    timestamp = row.timestamp if hasattr(row, "timestamp") else row.get("t") or row.get("timestamp")
    if hasattr(timestamp, "isoformat"):
        ts = pd.Timestamp(timestamp)
    else:
        ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return {
        "symbol": symbol,
        "timestamp": ts,
        "open": float(row.open) if hasattr(row, "open") else float(row.get("o", row.get("open"))),
        "high": float(row.high) if hasattr(row, "high") else float(row.get("h", row.get("high"))),
        "low": float(row.low) if hasattr(row, "low") else float(row.get("l", row.get("low"))),
        "close": float(row.close) if hasattr(row, "close") else float(row.get("c", row.get("close"))),
        "volume": int(row.volume) if hasattr(row, "volume") else int(row.get("v", row.get("volume", 0))),
        "vwap": float(row.vwap) if hasattr(row, "vwap") and row.vwap is not None else None,
        "trade_count": (
            int(row.trade_count) if hasattr(row, "trade_count") and row.trade_count is not None else None
        ),
    }


def _coerce_bars_response_to_rows(resp: Any) -> dict[str, list[Any]]:
    """Return ``{symbol: [bar_objects]}`` from various alpaca-py response shapes."""
    # alpaca-py returns BarSet with `.data` dict[str, list[Bar]] OR a
    # `dict` directly. Tests inject plain dicts.
    if hasattr(resp, "data") and isinstance(resp.data, dict):
        return resp.data
    if isinstance(resp, dict):
        return resp
    raise TypeError(f"Unsupported bars response type: {type(resp)!r}")


def fetch_daily_bars(
    client: AlpacaClient,
    *,
    symbols: list[str],
    start: date | datetime | str,
    end: date | datetime | str,
    request_factory: Callable[..., Any] | None = None,
    page_size: int = 10_000,
) -> pd.DataFrame:
    """Fetch daily bars for ``symbols`` between ``start`` and ``end`` inclusive.

    Paginates fully through ``next_page_token`` and returns one row per symbol/day.
    """
    return _fetch_bars(
        client,
        symbols=symbols,
        start=start,
        end=end,
        timeframe="1Day",
        request_factory=request_factory,
        page_size=page_size,
    )


def fetch_minute_bars(
    client: AlpacaClient,
    *,
    symbols: list[str],
    start: date | datetime | str,
    end: date | datetime | str,
    request_factory: Callable[..., Any] | None = None,
    page_size: int = 10_000,
) -> pd.DataFrame:
    """Fetch 1-minute bars for ``symbols`` between ``start`` and ``end`` inclusive."""
    return _fetch_bars(
        client,
        symbols=symbols,
        start=start,
        end=end,
        timeframe="1Min",
        request_factory=request_factory,
        page_size=page_size,
    )


def _fetch_bars(
    client: AlpacaClient,
    *,
    symbols: list[str],
    start,
    end,
    timeframe: str,
    request_factory: Callable[..., Any] | None,
    page_size: int,
) -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame(
            columns=["symbol", "timestamp", "open", "high", "low", "close", "volume", "vwap", "trade_count"]
        )
    data_client = client.data()

    if request_factory is None:
        request_factory = _default_stock_bars_request_factory(timeframe=timeframe, page_size=page_size, feed=client.feed)

    page_token: str | None = None
    rows: list[dict[str, Any]] = []
    while True:
        req = request_factory(
            symbol_or_symbols=symbols,
            start=start,
            end=end,
            page_token=page_token,
            limit=page_size,
        )
        resp = client.call(data_client.get_stock_bars, req)
        bars_by_symbol = _coerce_bars_response_to_rows(resp)
        for symbol, bar_list in bars_by_symbol.items():
            for bar in bar_list:
                rows.append(_normalize_bar_row(symbol, bar))
        next_token = getattr(resp, "next_page_token", None)
        if next_token is None and isinstance(resp, dict):
            next_token = resp.get("next_page_token")
        if not next_token:
            break
        page_token = next_token

    if not rows:
        return pd.DataFrame(
            columns=["symbol", "timestamp", "open", "high", "low", "close", "volume", "vwap", "trade_count"]
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def _default_stock_bars_request_factory(*, timeframe: str, page_size: int, feed: str):
    """Build a callable that returns alpaca-py's StockBarsRequest."""
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    def _factory(*, symbol_or_symbols, start, end, page_token, limit=page_size):
        if timeframe.lower() in ("1d", "1day", "day"):
            tf = TimeFrame.Day
        elif timeframe.lower() in ("1m", "1min", "min", "minute"):
            tf = TimeFrame.Minute
        else:
            tf = TimeFrame.Day
        kw = dict(
            symbol_or_symbols=symbol_or_symbols,
            timeframe=tf,
            start=start,
            end=end,
            feed=feed,
            limit=limit,
        )
        if page_token is not None:
            kw["page_token"] = page_token
        return StockBarsRequest(**kw)

    return _factory
