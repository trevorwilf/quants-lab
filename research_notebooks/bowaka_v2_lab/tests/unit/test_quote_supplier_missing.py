"""Phase 6 — quote supplier returns None when the quote partition is absent.

This is the normal case on the current lake: there is no quote-ingestion stage,
so the ``quotes/`` tree does not exist and every quote lookup returns ``None``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import MarketDataStore
from bowaka_v2_lab.data.suppliers import make_quote_supplier


def test_supplier_returns_none_when_partition_absent(tmp_path):
    # The lake has no quotes/ tree at all.
    supplier = make_quote_supplier(tmp_path, feed="iex")
    q = supplier("AAA", pd.Timestamp("2024-09-04 14:00:00", tz="UTC"), 60)
    assert q is None


def test_store_returns_none_when_partition_absent(tmp_path):
    store = MarketDataStore(tmp_path)
    row = store.quotes_at_or_before(
        "AAA", pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        max_age_seconds=60, feed="iex",
    )
    assert row is None


def test_supplier_none_for_symbol_without_partition(tmp_path):
    """A partition exists for one symbol but not the queried one → None."""
    from bowaka_common.marketdata import layout

    path = layout.quotes_path(tmp_path, "AAA", 2024, 9, feed="iex")
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"symbol": "AAA", "timestamp": pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
          "bid": 99.9, "ask": 100.1, "bid_size": 100, "ask_size": 100,
          "mid": 100.0, "spread_pct": 0.002}]
    ).to_parquet(path, index=False)

    supplier = make_quote_supplier(tmp_path, feed="iex")
    # ZZZ has no partition.
    assert supplier("ZZZ", pd.Timestamp("2024-09-04 14:00:00", tz="UTC"), 60) is None
    # AAA does.
    assert supplier("AAA", pd.Timestamp("2024-09-04 14:00:05", tz="UTC"), 60) is not None
