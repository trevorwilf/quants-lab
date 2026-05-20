"""Daily-bar fixture builder."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np
import pandas as pd


def make_daily_bars(
    symbol: str,
    start: _dt.date,
    n_sessions: int = 30,
    *,
    base_price: float = 100.0,
    daily_drift_pct: float = 0.0,
    daily_volume: float = 1_000_000,
    daily_range_pct: float = 0.015,
) -> pd.DataFrame:
    rows = []
    price = base_price
    cur = start
    sessions = 0
    while sessions < n_sessions:
        if cur.weekday() < 5:
            o = price
            h = o * (1.0 + daily_range_pct)
            l = o * (1.0 - daily_range_pct)
            c = o * (1.0 + daily_drift_pct)
            rows.append({
                "symbol": symbol,
                "session_date": cur,
                "open": o, "high": h, "low": l, "close": c,
                "volume": float(daily_volume),
            })
            price = c
            sessions += 1
        cur = cur + _dt.timedelta(days=1)
    return pd.DataFrame(rows)


def write_daily_fixture(out_dir: Path, symbol: str, df: pd.DataFrame) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{symbol}.parquet"
    df.to_parquet(p, index=False)
    return p
