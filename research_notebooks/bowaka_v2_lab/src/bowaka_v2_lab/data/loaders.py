"""Data loaders for bowaka_v2_lab.

Two sources:

- ``fixture`` — Parquet under ``<data_root>/fixtures/`` (tests, smoke backtester).
- ``alpaca`` (alias ``shared``) — the shared market-data lake, read through
  ``bowaka_common.marketdata.MarketDataStore``. The lake root comes from
  ``shared_root`` (or ``MARKET_DATA_ROOT`` / the in-repo default when ``None``)
  — it is **never** derived from ``BowakaV2Paths``, so strategy isolation is
  unaffected.

All functions return DataFrames with tz-aware timestamps.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from bowaka_common.marketdata import MarketDataStore

from ..config.paths import BowakaV2Paths
from ..utils.time import require_aware_timestamp

_FIXTURE_BARS_DIR = "fixtures"
_FIXTURE_QUOTES_DIR = "fixtures/quotes"
_FIXTURE_ACTIONS_DIR = "fixtures/corporate_actions"

#: Source values that resolve to the shared market-data lake.
_LAKE_SOURCES = ("alpaca", "shared")


def _to_date(d: Any) -> _dt.date:
    if isinstance(d, _dt.date) and not isinstance(d, _dt.datetime):
        return d
    if isinstance(d, _dt.datetime):
        return d.date()
    return pd.Timestamp(d).date()


def daily_bars_for(
    symbol: str,
    start: Any,
    end: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
    shared_root: str | Path | None = None,
    feed: str = "iex",
) -> pd.DataFrame:
    """Return daily bars for ``symbol`` over ``[start, end]``.

    ``source="fixture"`` reads ``<data_root>/fixtures/daily_bars/<symbol>.parquet``.
    ``source="alpaca"`` reads the shared lake via :class:`MarketDataStore`.
    """
    if source == "fixture":
        p = Path(paths.data_root) / "fixtures" / "daily_bars" / f"{symbol}.parquet"
        if not p.is_file():
            return pd.DataFrame()
        df = pd.read_parquet(p)
        start_d = _to_date(start)
        end_d = _to_date(end)
        if "session_date" in df.columns:
            df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
            df = df[(df["session_date"] >= start_d) & (df["session_date"] <= end_d)]
        return df.reset_index(drop=True)
    if source in _LAKE_SOURCES:
        return MarketDataStore(shared_root).daily_bars(symbol, start, end, feed=feed)
    raise ValueError(f"daily_bars_for: unknown source {source!r}")


def minute_bars_for(
    symbol: str,
    scan_ts_or_session: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
    shared_root: str | Path | None = None,
    feed: str = "iex",
) -> pd.DataFrame:
    """Return minute bars for ``symbol`` up to ``scan_ts_or_session`` (tz-aware).

    Returned frame is sorted by timestamp and trimmed to bars at-or-before the cutoff.
    """
    cutoff = require_aware_timestamp(scan_ts_or_session, label="minute_bars_for")
    session_date = cutoff.tz_convert("America/New_York").date()
    if source == "fixture":
        per_session = (
            Path(paths.data_root) / "fixtures" / "minute_bars" / symbol / f"{session_date.isoformat()}.parquet"
        )
        per_symbol = Path(paths.data_root) / "fixtures" / "minute_bars" / f"{symbol}.parquet"
        if per_session.is_file():
            df = pd.read_parquet(per_session)
        elif per_symbol.is_file():
            df = pd.read_parquet(per_symbol)
        else:
            return pd.DataFrame()
        cols = {c.lower(): c for c in df.columns}
        ts_col = cols.get("timestamp") or cols.get("ts")
        if ts_col is None:
            return df.reset_index(drop=True)
        df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
        df = df[df[ts_col] <= cutoff]
        return df.sort_values(ts_col).reset_index(drop=True)
    if source in _LAKE_SOURCES:
        session_start = pd.Timestamp(session_date, tz="UTC")
        return MarketDataStore(shared_root).minute_bars(symbol, session_start, cutoff, feed=feed)
    raise ValueError(f"minute_bars_for: unknown source {source!r}")


def quotes_for(
    symbol: str,
    at: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
    shared_root: str | Path | None = None,
    feed: str = "iex",
) -> Optional[dict[str, Any]]:
    """Return the most recent quote at or before ``at`` for ``symbol``, or None.

    The shared lake has no quote stage yet, so ``source="alpaca"`` returns None
    when no quote data is present — callers fall back to the synthetic quote model.
    """
    cutoff = require_aware_timestamp(at, label="quotes_for")
    if source == "fixture":
        p = Path(paths.data_root) / "fixtures" / "quotes" / f"{symbol}.parquet"
        if not p.is_file():
            return None
        df = pd.read_parquet(p)
    elif source in _LAKE_SOURCES:
        df = MarketDataStore(shared_root).quotes(
            symbol, cutoff - pd.Timedelta(days=3), cutoff, feed=feed
        )
        if df is None or df.empty:
            return None
    else:
        raise ValueError(f"quotes_for: unknown source {source!r}")

    cols = {c.lower(): c for c in df.columns}
    ts_col = cols.get("timestamp") or cols.get("ts")
    if ts_col is None:
        return None
    df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
    df = df[df[ts_col] <= cutoff].sort_values(ts_col)
    if len(df) == 0:
        return None
    row = df.iloc[-1].to_dict()
    bid = float(row.get("bid", 0.0) or 0.0)
    ask = float(row.get("ask", 0.0) or 0.0)
    mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else None
    spread_pct = (ask - bid) / mid if (mid and mid > 0) else None
    age_seconds = float((cutoff - pd.Timestamp(row[ts_col])).total_seconds())
    return {
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_pct": spread_pct,
        "quote_timestamp": pd.Timestamp(row[ts_col]).isoformat(),
        "quote_age_seconds": age_seconds,
        "source": source,
    }


def corporate_actions_for(
    symbol: str,
    start: Any,
    end: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
    shared_root: str | Path | None = None,
) -> pd.DataFrame:
    """Return corporate actions for ``symbol`` over ``[start, end]``."""
    if source == "fixture":
        p = Path(paths.data_root) / "fixtures" / "corporate_actions" / f"{symbol}.parquet"
        if not p.is_file():
            return pd.DataFrame()
        df = pd.read_parquet(p)
        if "ex_date" in df.columns:
            df["ex_date"] = pd.to_datetime(df["ex_date"]).dt.date
            start_d = _to_date(start)
            end_d = _to_date(end)
            df = df[(df["ex_date"] >= start_d) & (df["ex_date"] <= end_d)]
        return df.reset_index(drop=True)
    if source in _LAKE_SOURCES:
        return MarketDataStore(shared_root).corporate_actions(symbol, start, end)
    raise ValueError(f"corporate_actions_for: unknown source {source!r}")
