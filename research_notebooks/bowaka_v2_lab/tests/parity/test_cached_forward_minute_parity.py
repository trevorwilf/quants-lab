"""Cached forward-minute supplier matches the legacy supplier.

Speedup report §5.3 / §11.2 Phase 3.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.data.cached_suppliers import make_cached_lake_suppliers
from bowaka_v2_lab.data.suppliers import make_forward_minute_supplier
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake


@pytest.fixture
def lake(tmp_path) -> Path:
    p = tmp_path / "lake"
    build_tiny_lake(p, ["AAA"],
                    start=dt.date(2024, 1, 28), end=dt.date(2024, 2, 5))
    return p


@pytest.mark.parametrize(
    "ts_et",
    [
        dt.datetime(2024, 1, 30, 10, 0),    # mid-session
        dt.datetime(2024, 1, 30, 13, 0),    # afternoon
        dt.datetime(2024, 1, 30, 15, 55),   # close-ish
        dt.datetime(2024, 1, 30, 15, 59),   # last minute
        dt.datetime(2024, 1, 31, 9, 45),    # session open
        dt.datetime(2024, 2, 1, 10, 0),     # month boundary
    ],
)
def test_forward_minutes_matches_legacy(lake: Path, ts_et: dt.datetime):
    cached = make_cached_lake_suppliers(lake, feed="iex", window_minutes=5)
    legacy = make_forward_minute_supplier(lake, feed="iex", window_minutes=5)
    ts = pd.Timestamp(ts_et, tz="America/New_York").tz_convert("UTC")
    a = legacy("AAA", ts)
    b = cached.forward_minutes("AAA", ts)
    if a.empty and b.empty:
        return
    pd.testing.assert_frame_equal(
        a.reset_index(drop=True), b.reset_index(drop=True),
        check_dtype=True, check_column_type=True,
    )


def test_forward_minutes_window_override(lake: Path):
    cached = make_cached_lake_suppliers(lake, feed="iex", window_minutes=5)
    ts = pd.Timestamp("2024-01-30T14:00:00", tz="UTC")
    df_5 = cached.forward_minutes("AAA", ts)
    df_10 = cached.forward_minutes("AAA", ts, window_minutes=10)
    # Wider window = at least as many bars.
    assert len(df_10) >= len(df_5)
