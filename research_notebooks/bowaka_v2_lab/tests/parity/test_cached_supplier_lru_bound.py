"""``CachedSessionMarketData`` honours its ``max_partition_entries`` cap.

Speedup report §5.3 / §11.2 Phase 3 — the LRU bound keeps the worker's RAM
footprint predictable when many symbols / months are touched.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.data.cached_suppliers import CachedSessionMarketData
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake


@pytest.fixture
def lake(tmp_path) -> Path:
    p = tmp_path / "lake"
    # 5 distinct months for one symbol.
    build_tiny_lake(p, ["AAA"], start=dt.date(2024, 1, 2), end=dt.date(2024, 5, 30))
    return p


def test_cache_bounded_to_max_partition_entries(lake: Path, monkeypatch):
    """Configure max_partition_entries=2; pull 5 months; cache must hold ≤ 2."""
    from bowaka_common.marketdata import MarketDataStore
    import pandas as _pd

    read_calls = {"n": 0}
    original = _pd.read_parquet

    def counting_read(*args, **kwargs):
        read_calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(_pd, "read_parquet", counting_read)

    adapter = CachedSessionMarketData(
        MarketDataStore(lake), feed="iex", max_partition_entries=2,
    )
    targets = [
        pd.Timestamp(f"2024-{m:02d}-15T15:00:00", tz="UTC")
        for m in (1, 2, 3, 4, 5)
    ]
    for ts in targets:
        adapter.forming_minutes("AAA", ts)
    # Five distinct months, cache size 2 → first three evicted.
    assert len(adapter._minute_cache) <= 2
    # Re-pulling the first month must trigger a fresh read (cache miss).
    reads_before = read_calls["n"]
    adapter.forming_minutes("AAA", targets[0])
    assert read_calls["n"] > reads_before, (
        "expected a fresh Parquet read on cache eviction"
    )
