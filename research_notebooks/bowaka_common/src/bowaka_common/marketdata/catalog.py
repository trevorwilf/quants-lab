"""Coverage queries and dataset hashing for the shared market-data lake.

Used by backtests to discover what data is present and to pin a reproducible
``dataset_hash`` for a given (symbols, date-range) selection.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..storage.dataset_hash import hash_dataframe
from . import layout as _layout
from .store import MarketDataStore, resolve_market_data_root


def available_symbols(
    root: str | Path | None = None,
    *,
    timeframe: str = "1d",
    vendor: str = "alpaca",
    feed: str = "iex",
    adjustment: str = "raw",
) -> list[str]:
    """Sorted symbols with bars present for one (timeframe, feed, adjustment)."""
    base = _layout.bars_timeframe_root(
        resolve_market_data_root(root, create=False),
        timeframe,
        vendor=vendor,
        feed=feed,
        adjustment=adjustment,
    )
    if not base.is_dir():
        return []
    return sorted(
        p.name.split("=", 1)[1] for p in base.glob("symbol=*") if p.is_dir()
    )


def date_coverage(
    symbol: str,
    root: str | Path | None = None,
    *,
    timeframe: str = "1d",
    vendor: str = "alpaca",
    feed: str = "iex",
    adjustment: str = "raw",
) -> tuple[_dt.date, _dt.date] | None:
    """``(min_date, max_date)`` of bars present for ``symbol``, or ``None``."""
    md_root = resolve_market_data_root(root, create=False)
    if timeframe == "1d":
        sym_dir = _layout.daily_bars_symbol_dir(
            md_root, symbol, vendor=vendor, feed=feed, adjustment=adjustment
        )
    else:
        sym_dir = _layout.minute_bars_symbol_dir(
            md_root, symbol, vendor=vendor, feed=feed, adjustment=adjustment
        )
    if not sym_dir.is_dir():
        return None
    lo: _dt.date | None = None
    hi: _dt.date | None = None
    for f in sorted(sym_dir.rglob("part.parquet")):
        df = pd.read_parquet(f)
        if df.empty or "timestamp" not in df.columns:
            continue
        ts = pd.to_datetime(df["timestamp"], utc=True)
        fmn, fmx = ts.min().date(), ts.max().date()
        lo = fmn if lo is None or fmn < lo else lo
        hi = fmx if hi is None or fmx > hi else hi
    if lo is None or hi is None:
        return None
    return lo, hi


def dataset_hash(
    symbols: Iterable[str],
    start,
    end,
    root: str | Path | None = None,
    *,
    timeframe: str = "1d",
    vendor: str = "alpaca",
    feed: str = "iex",
    adjustment: str = "raw",
) -> str:
    """Deterministic content hash of the bars for ``symbols`` over ``[start, end]``.

    Order-independent in both symbol order and physical row order — the same
    selection always hashes to the same value.
    """
    store = MarketDataStore(root, vendor=vendor)
    frames: list[pd.DataFrame] = []
    for sym in sorted({str(s) for s in symbols}):
        if timeframe == "1d":
            df = store.daily_bars(sym, start, end, feed=feed, adjustment=adjustment)
        else:
            df = store.minute_bars(sym, start, end, feed=feed, adjustment=adjustment)
        if not df.empty:
            frames.append(df)
    if not frames:
        return hash_dataframe(pd.DataFrame())
    combined = pd.concat(frames, ignore_index=True)
    sort_keys = [c for c in ("symbol", "timestamp") if c in combined.columns]
    return hash_dataframe(combined, sort_by=sort_keys or None)
