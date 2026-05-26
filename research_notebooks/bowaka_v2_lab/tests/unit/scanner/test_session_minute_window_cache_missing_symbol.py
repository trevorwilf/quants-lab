"""Missing-symbol semantics: cache + legacy supplier agree on the empty frame.

Speedup report v2 §5.7 / Phase 4 task 6. A symbol not present in the
cache's eligible-symbol set returns the canonical empty minute frame
(same columns, zero rows) — matching the legacy supplier behaviour.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import MarketDataStore
from bowaka_v2_lab.data.suppliers import make_lake_suppliers
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.scanner.session_minute_window_cache import (
    SessionMinuteWindowCache,
)


def test_missing_symbol_returns_empty_frame(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 28), end=dt.date(2024, 2, 5))
    cache = SessionMinuteWindowCache(
        MarketDataStore(lake), dt.date(2024, 1, 30), ["AAA"], feed="iex",
    )
    legacy_minute, _ = make_lake_suppliers(lake, feed="iex")
    scan_ts = pd.Timestamp("2024-01-30T15:00:00", tz="America/New_York").tz_convert("UTC")
    miss_cache = cache.bars_until("MISSING", scan_ts)
    miss_legacy = legacy_minute("MISSING", scan_ts)
    assert len(miss_cache) == 0
    assert len(miss_legacy) == 0
    assert list(miss_cache.columns) == [
        "symbol", "timestamp", "open", "high", "low", "close", "volume",
    ]
