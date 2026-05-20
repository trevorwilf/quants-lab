"""Multi-symbol quote fetcher with full pagination."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import pandas as pd

from bowaka_common.data.alpaca_client import AlpacaClient


def _normalize_quote(symbol: str, row: Any) -> dict[str, Any]:
    def attr(name: str, *aliases: str, default=None):
        if hasattr(row, name):
            return getattr(row, name)
        if isinstance(row, dict):
            for k in (name, *aliases):
                if k in row:
                    return row[k]
        return default

    ts = attr("timestamp", "t")
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return {
        "symbol": symbol,
        "timestamp": ts,
        "bid_price": float(attr("bid_price", "bp", default=0.0) or 0.0),
        "ask_price": float(attr("ask_price", "ap", default=0.0) or 0.0),
        "bid_size": int(attr("bid_size", "bs", default=0) or 0),
        "ask_size": int(attr("ask_size", "as_", default=0) or 0),
    }


def _coerce_quotes_response(resp: Any) -> dict[str, list[Any]]:
    if hasattr(resp, "data") and isinstance(resp.data, dict):
        return resp.data
    if isinstance(resp, dict):
        return resp
    raise TypeError(f"Unsupported quotes response type: {type(resp)!r}")


def fetch_quotes(
    client: AlpacaClient,
    *,
    symbols: list[str],
    start: datetime | str,
    end: datetime | str,
    request_factory: Callable[..., Any] | None = None,
    page_size: int = 10_000,
) -> pd.DataFrame:
    """Fetch quotes for ``symbols`` over ``[start, end]``, paginating fully."""
    if not symbols:
        return pd.DataFrame(columns=["symbol", "timestamp", "bid_price", "ask_price", "bid_size", "ask_size"])
    data_client = client.data()

    if request_factory is None:
        request_factory = _default_quote_request_factory(feed=client.feed, page_size=page_size)

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
        resp = client.call(data_client.get_stock_quotes, req)
        by_symbol = _coerce_quotes_response(resp)
        for symbol, qlist in by_symbol.items():
            for q in qlist:
                rows.append(_normalize_quote(symbol, q))
        next_token = getattr(resp, "next_page_token", None)
        if next_token is None and isinstance(resp, dict):
            next_token = resp.get("next_page_token")
        if not next_token:
            break
        page_token = next_token

    if not rows:
        return pd.DataFrame(columns=["symbol", "timestamp", "bid_price", "ask_price", "bid_size", "ask_size"])
    df = pd.DataFrame(rows).sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    df["spread"] = df["ask_price"] - df["bid_price"]
    df["mid"] = (df["ask_price"] + df["bid_price"]) / 2.0
    df["spread_pct"] = (df["spread"] / df["mid"]).where(df["mid"] > 0, 0.0)
    return df


def _default_quote_request_factory(*, feed: str, page_size: int):
    from alpaca.data.requests import StockQuotesRequest

    def _factory(*, symbol_or_symbols, start, end, page_token, limit=page_size):
        kw = dict(
            symbol_or_symbols=symbol_or_symbols,
            start=start,
            end=end,
            feed=feed,
            limit=limit,
        )
        if page_token is not None:
            kw["page_token"] = page_token
        return StockQuotesRequest(**kw)

    return _factory
