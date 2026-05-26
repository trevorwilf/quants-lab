"""Batch builder preserves caller-provided per-session symbol order.

Speedup report v2 §4 P1 / Phase 1 task 5. The legacy builder iterates the
input ``symbols`` list and appends rows in that order; the batch builder
must mirror it (the downstream scanner relies on the row order matching
the eligible-symbol order). A regression that alphabetises would silently
re-order the per-session feature DataFrame.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.daily_cache_batch import build_daily_cache_for_sessions_from_lake


def _write_daily(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_batch_preserves_caller_symbol_order(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    start = dt.date(2024, 1, 1)
    days = [d.date() for d in pd.bdate_range(start, start + dt.timedelta(days=80))]
    sessions = days[-1:]  # one scan session
    for sym in ("ZZZZ", "AAAA", "MMMM"):
        _write_daily(
            layout.daily_bars_path(lake, sym, feed="iex"),
            pd.DataFrame({
                "symbol": [sym] * len(days),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
                "open":   [100.0] * len(days), "high":   [101.0] * len(days),
                "low":    [ 99.0] * len(days), "close":  [100.0] * len(days),
                "volume": [1_000_000] * len(days), "session_date": days,
            }),
        )
    symbols_by_session = {s: ["ZZZZ", "AAAA", "MMMM"] for s in sessions}
    out = build_daily_cache_for_sessions_from_lake(
        lake, symbols_by_session, sessions, feed="iex",
    )
    for s in sessions:
        assert out[s]["symbol"].tolist() == ["ZZZZ", "AAAA", "MMMM"], (
            f"row order changed for {s}: {out[s]['symbol'].tolist()}"
        )
