"""Phase 6 — quote supplier returns the latest historical quote at-or-before ts.

When the lake has a ``quotes/`` partition, ``make_quote_supplier`` reads it via
``MarketDataStore.quotes_at_or_before`` and returns the most recent quote
at-or-before the requested timestamp, within ``max_age_seconds``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import QuoteRow, layout
from bowaka_v2_lab.data.suppliers import make_quote_supplier


def _write_quotes(root, symbol, year, month, rows):
    path = layout.quotes_path(root, symbol, year, month, feed="iex")
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_supplier_returns_latest_quote_at_or_before(tmp_path):
    # Three quotes in the same minute partition; the supplier must pick the
    # newest one that is still at-or-before the query timestamp.
    _write_quotes(
        tmp_path, "AAA", 2024, 9,
        [
            {"symbol": "AAA", "timestamp": pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
             "bid": 99.90, "ask": 100.10, "bid_size": 100, "ask_size": 120,
             "mid": 100.0, "spread_pct": 0.002},
            {"symbol": "AAA", "timestamp": pd.Timestamp("2024-09-04 14:00:30", tz="UTC"),
             "bid": 99.95, "ask": 100.05, "bid_size": 200, "ask_size": 220,
             "mid": 100.0, "spread_pct": 0.001},
            {"symbol": "AAA", "timestamp": pd.Timestamp("2024-09-04 14:05:00", tz="UTC"),
             "bid": 99.80, "ask": 100.20, "bid_size": 50, "ask_size": 60,
             "mid": 100.0, "spread_pct": 0.004},
        ],
    )
    supplier = make_quote_supplier(tmp_path, feed="iex")
    q = supplier("AAA", pd.Timestamp("2024-09-04 14:00:45", tz="UTC"), 120)
    assert q is not None
    # The 14:00:30 quote is the newest at-or-before 14:00:45.
    assert q["bid"] == 99.95
    assert q["ask"] == 100.05
    assert q["bid_size"] == 200
    assert q["source"] == "historical"
    assert q["quote_age_seconds"] == 15.0


def test_store_returns_quoterow(tmp_path):
    """The store API itself returns a typed QuoteRow with source=historical."""
    from bowaka_common.marketdata import MarketDataStore

    _write_quotes(
        tmp_path, "BBB", 2024, 9,
        [{"symbol": "BBB", "timestamp": pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
          "bid": 10.0, "ask": 10.04, "bid_size": 300, "ask_size": 400,
          "mid": 10.02, "spread_pct": 0.004}],
    )
    store = MarketDataStore(tmp_path)
    row = store.quotes_at_or_before(
        "BBB", pd.Timestamp("2024-09-04 14:00:10", tz="UTC"), max_age_seconds=60, feed="iex"
    )
    assert isinstance(row, QuoteRow)
    assert row.source == "historical"
    assert row.bid == 10.0 and row.ask == 10.04
    assert row.quote_age_seconds == 10.0


def test_supplier_returns_none_when_quote_older_than_max_age(tmp_path):
    """A quote older than max_age_seconds is treated as no quote."""
    _write_quotes(
        tmp_path, "AAA", 2024, 9,
        [{"symbol": "AAA", "timestamp": pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
          "bid": 99.9, "ask": 100.1, "bid_size": 100, "ask_size": 100,
          "mid": 100.0, "spread_pct": 0.002}],
    )
    supplier = make_quote_supplier(tmp_path, feed="iex")
    # Query 5 minutes later with a 60s max age — the quote is stale → None.
    q = supplier("AAA", pd.Timestamp("2024-09-04 14:05:00", tz="UTC"), 60)
    assert q is None
