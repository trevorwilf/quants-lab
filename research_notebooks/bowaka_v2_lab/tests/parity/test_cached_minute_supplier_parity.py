"""Cached minute-bar supplier matches the legacy MarketDataStore reads.

Speedup report §5.3 / §11.2 Phase 3. ``CachedSessionMarketData`` is a
performance optimisation; behavioural parity with the legacy
``make_lake_suppliers``-backed minute supplier is the only safety net.
Boundary semantics MUST match ``MarketDataStore.minute_bars`` exactly:
``[start, end]`` both ends inclusive, ``sort_values("timestamp")``,
``drop_duplicates(subset=["timestamp"], keep="last")``, tz-aware UTC.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.data.cached_suppliers import (
    CachedSessionMarketData,
    make_cached_lake_suppliers,
)
from bowaka_v2_lab.data.suppliers import make_lake_suppliers
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake


@pytest.fixture
def lake(tmp_path) -> Path:
    """A tiny lake spanning a month boundary so the cache must concat months."""
    p = tmp_path / "lake"
    build_tiny_lake(p, ["AAA", "BBB"],
                    start=dt.date(2024, 1, 28), end=dt.date(2024, 2, 5))
    return p


@pytest.mark.parametrize(
    "symbol,scan_date,scan_time_et",
    [
        ("AAA", dt.date(2024, 1, 30), (10, 0)),    # mid-session
        ("AAA", dt.date(2024, 1, 30), (9, 45)),    # first scan
        ("AAA", dt.date(2024, 1, 30), (15, 55)),   # last scan
        ("AAA", dt.date(2024, 1, 30), (16, 0)),    # session end
        ("AAA", dt.date(2024, 1, 29), (13, 30)),   # day before
        ("AAA", dt.date(2024, 2, 1), (10, 15)),    # month boundary
        ("BBB", dt.date(2024, 1, 30), (11, 30)),   # different symbol
        ("ZZZ", dt.date(2024, 1, 30), (10, 0)),    # symbol with no data
    ],
)
def test_forming_minutes_matches_legacy_supplier(
    lake: Path, symbol: str, scan_date: dt.date, scan_time_et: tuple[int, int],
):
    legacy_minute, _ = make_lake_suppliers(lake, feed="iex")
    cached = make_cached_lake_suppliers(lake, feed="iex")
    cutoff = pd.Timestamp(
        f"{scan_date.isoformat()}T{scan_time_et[0]:02d}:{scan_time_et[1]:02d}:00",
        tz="America/New_York",
    ).tz_convert("UTC")

    a = legacy_minute(symbol, cutoff)
    b = cached.forming_minutes(symbol, cutoff)
    # Both should agree on columns + row counts + content.
    if a.empty and b.empty:
        return
    pd.testing.assert_frame_equal(
        a.reset_index(drop=True),
        b.reset_index(drop=True),
        check_dtype=True, check_column_type=True,
    )


def test_repeated_calls_reuse_cache(lake: Path, monkeypatch):
    """Two calls for the same cutoff must read the parquet ONCE."""
    import pandas as _pd

    read_calls = {"n": 0}
    original = _pd.read_parquet

    def counting_read(*args, **kwargs):
        read_calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(_pd, "read_parquet", counting_read)
    cached = make_cached_lake_suppliers(lake, feed="iex")
    cutoff = pd.Timestamp("2024-01-30T14:00:00", tz="UTC")
    cached.forming_minutes("AAA", cutoff)
    first = read_calls["n"]
    cached.forming_minutes("AAA", cutoff)
    second = read_calls["n"]
    # The second call must not trigger any additional Parquet reads.
    assert second == first, (
        f"cache miss on repeated call: {first} -> {second} reads"
    )


def test_cache_returns_independent_views(lake: Path):
    """Cached frames are not exposed via reference — downstream code's
    in-place edits must not contaminate later calls."""
    cached = make_cached_lake_suppliers(
        lake, feed="iex", intraday_window_policy="extended_hours_to_scan",
    )
    cutoff = pd.Timestamp("2024-01-30T14:00:00", tz="UTC")
    a = cached.forming_minutes("AAA", cutoff)
    assert not a.empty, "test setup error — extended_hours window should be non-empty"
    a_hash = int(pd.util.hash_pandas_object(a, index=True).sum())
    # Mutate the returned slice — must not affect the next call.
    a.loc[:, "close"] = -1.0
    b = cached.forming_minutes("AAA", cutoff)
    b_hash = int(pd.util.hash_pandas_object(b, index=True).sum())
    assert a_hash == b_hash, (
        "downstream in-place edit contaminated the cached partition"
    )
