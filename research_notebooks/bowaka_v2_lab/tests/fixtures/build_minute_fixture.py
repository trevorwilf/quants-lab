"""Minute-bar fixture builder.

Anchors timestamps to 16:00 ET close (mirrors the v1 fixture-builder lesson
documented in ``bowaka_lab/_implementation_summary.md`` deviation note about
session-aligned anchoring).
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore


ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def make_minute_bars(
    symbol: str,
    session_date: _dt.date,
    *,
    open_price: float = 100.0,
    drift_per_minute: float = 0.0,
    minute_volume: float = 1000.0,
    minutes: int = 30,
) -> pd.DataFrame:
    """Build ``minutes`` 1-min bars starting at 09:30 ET on ``session_date``."""
    open_ts_et = _dt.datetime.combine(session_date, _dt.time(9, 30, tzinfo=ET))
    rows = []
    price = open_price
    for i in range(minutes):
        ts = (open_ts_et + _dt.timedelta(minutes=i)).astimezone(UTC)
        o = price
        h = o + 0.5
        l = o - 0.2
        c = o + drift_per_minute
        rows.append({
            "symbol": symbol,
            "timestamp": pd.Timestamp(ts),
            "open": o, "high": h, "low": l, "close": c,
            "volume": float(minute_volume),
        })
        price = c
    return pd.DataFrame(rows)


def write_minute_fixture(
    out_dir: Path,
    symbol: str,
    session_date: _dt.date,
    df: pd.DataFrame,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{session_date.isoformat()}.parquet"
    df.to_parquet(p, index=False)
    return p
