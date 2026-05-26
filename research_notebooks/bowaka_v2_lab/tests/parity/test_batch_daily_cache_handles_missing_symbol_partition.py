"""Missing-symbol parquet → batch builder drops the symbol cleanly.

Speedup report v2 §4 P1 / Phase 1 task 5. A symbol named in
``symbols_by_session[s]`` that has no parquet partition under the lake is
handled identically to the legacy builder: the row is omitted, the
remaining rows are produced in caller-provided order.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.daily_cache_batch import build_daily_cache_for_sessions_from_lake
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake


def _write_daily(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_missing_symbol_partition_is_silently_dropped(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    days = [d.date() for d in pd.bdate_range(dt.date(2024, 1, 1), periods=80)]
    session = days[-1]
    # Only PRESENT has a parquet; MISSING has none.
    _write_daily(
        layout.daily_bars_path(lake, "PRESENT", feed="iex"),
        pd.DataFrame({
            "symbol": ["PRESENT"] * len(days),
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
            "open":   [100.0] * len(days), "high":   [101.0] * len(days),
            "low":    [ 99.0] * len(days), "close":  [100.0] * len(days),
            "volume": [1_000_000] * len(days), "session_date": days,
        }),
    )
    symbols = ["MISSING", "PRESENT"]
    legacy = build_daily_cache_from_lake(lake, symbols, session, feed="iex")
    batch = build_daily_cache_for_sessions_from_lake(
        lake, {session: symbols}, [session], feed="iex",
    )
    assert legacy["symbol"].tolist() == ["PRESENT"]
    assert batch[session]["symbol"].tolist() == ["PRESENT"]
    pd.testing.assert_frame_equal(
        legacy.reset_index(drop=True),
        batch[session].reset_index(drop=True),
    )
