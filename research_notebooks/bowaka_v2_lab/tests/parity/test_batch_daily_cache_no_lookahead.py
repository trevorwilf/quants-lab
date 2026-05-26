"""The batch builder does not leak future data into earlier sessions.

Speedup report v2 §4 P1 / Phase 1 task 5. The per-session slice uses
``prior["_sd"] < session`` (strictly less than) so even though each symbol's
parquet is read over the full span up to ``max_session``, no row dated on or
after ``session`` contributes to that session's output. Adding a synthetic
extreme close after ``s0`` must not change ``out[s0]``.
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


def test_batch_does_not_leak_future_data(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    sym = "ABC"
    start = dt.date(2024, 1, 1)
    # 90 trading days, two scan sessions s0 / s1 (5 days apart).
    days = [d.date() for d in pd.bdate_range(start, start + dt.timedelta(days=130))]
    daily_path = layout.daily_bars_path(lake, sym, feed="iex")
    _write_daily(daily_path, pd.DataFrame({
        "symbol": [sym] * len(days),
        "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
        "open":   [100.0 + 0.1 * i for i in range(len(days))],
        "high":   [101.0 + 0.1 * i for i in range(len(days))],
        "low":    [ 99.0 + 0.1 * i for i in range(len(days))],
        "close":  [100.0 + 0.1 * i for i in range(len(days))],
        "volume": [1_000_000] * len(days),
        "session_date": days,
    }))
    s0 = days[-10]
    s1 = days[-5]

    symbols_by_session = {s0: [sym], s1: [sym]}
    initial = build_daily_cache_for_sessions_from_lake(
        lake, symbols_by_session, [s0, s1], feed="iex",
    )
    s0_initial = initial[s0].copy()

    # Mutate: append a row dated s1 + 1 day with an extreme close.
    df = pd.read_parquet(daily_path)
    df = pd.concat(
        [df, pd.DataFrame({
            "symbol": [sym],
            "timestamp": [pd.Timestamp(s1 + dt.timedelta(days=1), tz="UTC")
                          + pd.Timedelta(hours=20)],
            "open": [9999.0], "high": [10000.0], "low": [9900.0], "close": [9999.0],
            "volume": [10_000_000],
            "session_date": [s1 + dt.timedelta(days=1)],
        })], ignore_index=True,
    )
    _write_daily(daily_path, df)

    after = build_daily_cache_for_sessions_from_lake(
        lake, {s0: [sym]}, [s0], feed="iex",
    )
    # s0's output must be unchanged — the new row is dated after s0's cutoff.
    pd.testing.assert_frame_equal(s0_initial.reset_index(drop=True),
                                  after[s0].reset_index(drop=True))
