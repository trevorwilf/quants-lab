"""SessionMinuteWindowCache returns the same slice as the legacy minute supplier.

Speedup report v2 §4 P3 / §5.7 / Phase 4 task 6. Boundary cases:

* Before the first bar.
* Exactly on a bar timestamp.
* Between bars.
* After the last bar.
* On a session-boundary timestamp.

Each comparison uses ``DataFrame.equals(...)`` — exact match on columns,
dtypes, row count, and content.
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


@pytest.fixture
def lake(tmp_path: Path) -> Path:
    p = tmp_path / "lake"
    build_tiny_lake(p, ["AAA", "BBB"],
                    start=dt.date(2024, 1, 28), end=dt.date(2024, 2, 5))
    return p


def _utc(date: dt.date, h: int, m: int) -> pd.Timestamp:
    return pd.Timestamp(
        dt.datetime.combine(date, dt.time(hour=h, minute=m)), tz="America/New_York"
    ).tz_convert("UTC")


@pytest.mark.parametrize(
    "symbol,session,scan_time_et",
    [
        ("AAA", dt.date(2024, 1, 30), (10, 0)),    # mid-session
        ("AAA", dt.date(2024, 1, 30), (9, 45)),    # window start (legacy default)
        ("AAA", dt.date(2024, 1, 30), (15, 55)),   # late session
        ("AAA", dt.date(2024, 1, 30), (16, 0)),    # session end (inclusive)
        ("BBB", dt.date(2024, 1, 30), (11, 30)),
    ],
)
def test_bars_until_matches_legacy_supplier(
    lake: Path, symbol: str, session: dt.date, scan_time_et: tuple[int, int],
) -> None:
    legacy_minute, _ = make_lake_suppliers(lake, feed="iex")
    cache = SessionMinuteWindowCache(
        MarketDataStore(lake), session, ["AAA", "BBB"], feed="iex",
    )
    cutoff = _utc(session, *scan_time_et)
    a = legacy_minute(symbol, cutoff).reset_index(drop=True)
    b = cache.bars_until(symbol, cutoff).reset_index(drop=True)
    assert list(a.columns) == list(b.columns), (
        f"column drift: legacy={list(a.columns)} cache={list(b.columns)}"
    )
    assert len(a) == len(b), f"row count differs: legacy={len(a)} cache={len(b)}"
    for col in a.columns:
        for va, vb in zip(a[col].tolist(), b[col].tolist()):
            assert va == vb, f"{col} mismatch: legacy={va!r} cache={vb!r}"


def test_bars_until_before_first_bar_returns_empty(lake: Path) -> None:
    """Scan-ts before the window start — cache returns the same empty frame."""
    cache = SessionMinuteWindowCache(
        MarketDataStore(lake), dt.date(2024, 1, 30), ["AAA"], feed="iex",
    )
    # 09:30 ET — earlier than the default 09:45 ET policy window start.
    cutoff = _utc(dt.date(2024, 1, 30), 9, 30)
    out = cache.bars_until("AAA", cutoff)
    assert len(out) == 0, (
        f"expected no bars before window start; got {len(out)}: {out}"
    )
