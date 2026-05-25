"""Cached quote supplier matches the legacy ``make_quote_supplier``.

Speedup report §5.3 / §11.2 Phase 3. The tiny lake has no ``quotes/``
partition so both must return ``None`` for every call — that is the only
real branch the public lake exercises today. The dict-shape parity
fixture exercises the synthetic-partition branch via a hand-built
partition file.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import layout as _layout
from bowaka_v2_lab.data.cached_suppliers import make_cached_lake_suppliers
from bowaka_v2_lab.data.suppliers import make_quote_supplier
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake


def test_no_quote_partition_both_return_none(tmp_path):
    """Both suppliers return ``None`` when no partition exists."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 2), end=dt.date(2024, 1, 5))
    legacy = make_quote_supplier(lake, feed="iex")
    cached = make_cached_lake_suppliers(lake, feed="iex")
    ts = pd.Timestamp("2024-01-03T14:00:00", tz="UTC")
    assert legacy("AAA", ts) is None
    assert cached.quote_at_or_before("AAA", ts) is None


def _write_quote_partition(lake: Path, symbol: str, year: int, month: int):
    """Write a tiny synthetic quote parquet at the expected path."""
    path = _layout.quotes_path(lake, symbol, year, month, vendor="alpaca", feed="iex")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for day in range(2, 6):
        for h, m in [(14, 0), (14, 15), (14, 30)]:
            ts = pd.Timestamp(
                dt.datetime(year, month, day, h, m), tz="UTC",
            )
            rows.append({
                "timestamp": ts,
                "bid": 99.5, "ask": 100.5, "bid_size": 100, "ask_size": 200,
                "mid": 100.0, "spread_pct": 0.01,
            })
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_synthetic_quote_partition_both_return_same_dict(tmp_path):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 2), end=dt.date(2024, 1, 5))
    _write_quote_partition(lake, "AAA", 2024, 1)

    legacy = make_quote_supplier(lake, feed="iex", default_max_age_seconds=60.0)
    cached = make_cached_lake_suppliers(lake, feed="iex", default_max_age_seconds=60.0)
    # Request 5 seconds after a quote so age is small and both return the row.
    ts = pd.Timestamp("2024-01-03T14:00:05", tz="UTC")
    a = legacy("AAA", ts)
    b = cached.quote_at_or_before("AAA", ts)
    assert a is not None and b is not None
    # Both should report the same business fields.
    for k in ("bid", "ask", "bid_size", "ask_size", "mid", "spread_pct",
              "quote_timestamp", "source"):
        assert a[k] == b[k], (
            f"quote dict differs on {k!r}: legacy={a[k]!r} cached={b[k]!r}"
        )
    # quote_age_seconds may differ by floating-point cruft only.
    assert abs(a["quote_age_seconds"] - b["quote_age_seconds"]) < 1e-6


def test_stale_quote_returns_none(tmp_path):
    """A quote older than ``max_age_seconds`` must give ``None`` from both."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 2), end=dt.date(2024, 1, 5))
    _write_quote_partition(lake, "AAA", 2024, 1)
    legacy = make_quote_supplier(lake, feed="iex", default_max_age_seconds=10.0)
    cached = make_cached_lake_suppliers(lake, feed="iex", default_max_age_seconds=10.0)
    # 60 seconds after the last quote at 14:30 — beyond the 10s threshold.
    ts = pd.Timestamp("2024-01-03T14:31:00", tz="UTC")
    assert legacy("AAA", ts) is None
    assert cached.quote_at_or_before("AAA", ts) is None
