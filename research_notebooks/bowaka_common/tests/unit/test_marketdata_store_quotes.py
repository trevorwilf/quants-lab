"""MarketDataStore.quotes_at_or_before — the historical quote reader (Phase 6).

The store reads the lake's ``quotes/`` partition and returns a typed
``QuoteRow`` for the most recent quote at-or-before a timestamp, within a
max-age window. When the partition is absent — the normal case on the current
lake, which has no quote-ingestion stage — it returns ``None``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import QuoteRow, layout
from bowaka_common.marketdata.store import MarketDataStore


def _write_quotes(root, symbol, year, month, rows):
    path = layout.quotes_path(root, symbol, year, month, feed="iex")
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def _row(ts, *, bid, ask, bid_size=100, ask_size=100):
    mid = (bid + ask) / 2.0
    return {
        "symbol": "AAA", "timestamp": ts, "bid": bid, "ask": ask,
        "bid_size": bid_size, "ask_size": ask_size, "mid": mid,
        "spread_pct": (ask - bid) / mid,
    }


def test_returns_none_when_partition_absent(tmp_path):
    store = MarketDataStore(tmp_path)
    out = store.quotes_at_or_before(
        "AAA", pd.Timestamp("2026-05-04 14:00:00", tz="UTC"),
        max_age_seconds=60, feed="iex",
    )
    assert out is None


def test_returns_latest_quote_at_or_before(tmp_path):
    _write_quotes(
        tmp_path, "AAA", 2026, 5,
        [
            _row(pd.Timestamp("2026-05-04 14:00:00", tz="UTC"), bid=9.98, ask=10.02),
            _row(pd.Timestamp("2026-05-04 14:00:20", tz="UTC"), bid=9.99, ask=10.01),
            _row(pd.Timestamp("2026-05-04 14:01:00", tz="UTC"), bid=9.97, ask=10.03),
        ],
    )
    store = MarketDataStore(tmp_path)
    out = store.quotes_at_or_before(
        "AAA", pd.Timestamp("2026-05-04 14:00:30", tz="UTC"),
        max_age_seconds=60, feed="iex",
    )
    assert isinstance(out, QuoteRow)
    assert out.bid == 9.99 and out.ask == 10.01  # the 14:00:20 quote
    assert out.source == "historical"
    assert out.quote_age_seconds == 10.0
    assert out.mid == 10.0
    assert out.spread_pct > 0.0


def test_returns_none_when_quote_stale(tmp_path):
    _write_quotes(
        tmp_path, "AAA", 2026, 5,
        [_row(pd.Timestamp("2026-05-04 14:00:00", tz="UTC"), bid=9.9, ask=10.1)],
    )
    store = MarketDataStore(tmp_path)
    # Five minutes later with a 60s max age — too stale.
    out = store.quotes_at_or_before(
        "AAA", pd.Timestamp("2026-05-04 14:05:00", tz="UTC"),
        max_age_seconds=60, feed="iex",
    )
    assert out is None


def test_returns_none_when_no_quote_before_ts(tmp_path):
    _write_quotes(
        tmp_path, "AAA", 2026, 5,
        [_row(pd.Timestamp("2026-05-04 14:10:00", tz="UTC"), bid=9.9, ask=10.1)],
    )
    store = MarketDataStore(tmp_path)
    # The only quote is AFTER the query timestamp.
    out = store.quotes_at_or_before(
        "AAA", pd.Timestamp("2026-05-04 14:05:00", tz="UTC"),
        max_age_seconds=3600, feed="iex",
    )
    assert out is None
