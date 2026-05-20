"""Data loaders for bowaka_v2_lab — backed by bowaka_common.

All functions return DataFrames with tz-aware timestamps. Fixture-mode
loaders read from Parquet under ``data_root/fixtures/`` which is the
default supplier for tests and the smoke backtester.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from ..config.paths import BowakaV2Paths
from ..utils.time import require_aware_timestamp


_FIXTURE_BARS_DIR = "fixtures"
_FIXTURE_QUOTES_DIR = "fixtures/quotes"
_FIXTURE_ACTIONS_DIR = "fixtures/corporate_actions"


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
) -> pd.DataFrame:
    """Return daily bars for ``symbol`` over ``[start, end]``.

    When ``source == "fixture"`` (default for tests), reads
    ``<data_root>/fixtures/daily_bars/<symbol>.parquet`` and filters by date.
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
    raise NotImplementedError(f"daily_bars_for: source={source!r} not wired in Phase 3")


def minute_bars_for(
    symbol: str,
    scan_ts_or_session: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
) -> pd.DataFrame:
    """Return minute bars for ``symbol`` up to ``scan_ts_or_session`` (tz-aware).

    Returned frame is sorted by timestamp and trimmed to bars at-or-before the cutoff.
    """
    cutoff = require_aware_timestamp(scan_ts_or_session, label="minute_bars_for")
    session_date = cutoff.tz_convert("America/New_York").date()
    if source == "fixture":
        # Two layouts supported:
        #   <data_root>/fixtures/minute_bars/<symbol>/<YYYY-MM-DD>.parquet
        #   <data_root>/fixtures/minute_bars/<symbol>.parquet
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
        df = df.sort_values(ts_col).reset_index(drop=True)
        return df
    raise NotImplementedError(f"minute_bars_for: source={source!r} not wired in Phase 3")


def quotes_for(
    symbol: str,
    at: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
) -> Optional[dict[str, Any]]:
    """Return the most recent quote at or before ``at`` for ``symbol``, or None."""
    cutoff = require_aware_timestamp(at, label="quotes_for")
    if source == "fixture":
        p = Path(paths.data_root) / "fixtures" / "quotes" / f"{symbol}.parquet"
        if not p.is_file():
            return None
        df = pd.read_parquet(p)
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
            "source": "fixture",
        }
    raise NotImplementedError(f"quotes_for: source={source!r} not wired in Phase 3")


def corporate_actions_for(
    symbol: str,
    start: Any,
    end: Any,
    *,
    paths: BowakaV2Paths,
    source: str = "fixture",
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
    raise NotImplementedError(f"corporate_actions_for: source={source!r} not wired in Phase 3")
