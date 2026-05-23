"""Audit P1-002: quote_supplier records the row's actual timestamp, not the request ts.

The pre-fix supplier set ``quote_timestamp: str(pd.Timestamp(ts))`` — the
request timestamp. The fix uses the ``QuoteRow.timestamp`` field returned from
:meth:`MarketDataStore.quotes_at_or_before`, so quote-age analytics see the real
quote time.
"""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import QuoteRow, layout
from bowaka_v2_lab.data.suppliers import make_quote_supplier


def _write_quotes(root, symbol, year, month, rows):
    path = layout.quotes_path(root, symbol, year, month, feed="iex")
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_quote_supplier_returns_row_timestamp_not_request(tmp_path) -> None:
    """A quote stored at 10:00:18 retrieved at 10:00:30 records the 10:00:18 ts."""
    # The last quote row sits 12 seconds before the requested ts.
    quote_ts = pd.Timestamp("2024-09-04 10:00:18", tz="UTC")
    _write_quotes(
        tmp_path, "AAA", 2024, 9,
        [
            {
                "symbol": "AAA", "timestamp": quote_ts,
                "bid": 99.95, "ask": 100.05, "bid_size": 200, "ask_size": 220,
                "mid": 100.0, "spread_pct": 0.001,
            },
        ],
    )
    supplier = make_quote_supplier(tmp_path, feed="iex")
    request_ts = pd.Timestamp("2024-09-04 10:00:30", tz="UTC")
    q = supplier("AAA", request_ts, 60)
    assert q is not None
    # The recorded quote_timestamp is the ROW's actual ts, not the request.
    recorded = pd.Timestamp(q["quote_timestamp"])
    if recorded.tzinfo is None:
        recorded = recorded.tz_localize("UTC")
    assert recorded == quote_ts, (
        f"expected row ts {quote_ts}, got {recorded} (P1-002 regression)"
    )
    # And the age is the distance from row ts -> request ts, exactly 12s.
    assert q["quote_age_seconds"] == 12.0


def test_store_quoterow_carries_timestamp(tmp_path) -> None:
    """``MarketDataStore.quotes_at_or_before`` populates ``QuoteRow.timestamp``."""
    from bowaka_common.marketdata import MarketDataStore

    quote_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    _write_quotes(
        tmp_path, "BBB", 2024, 9,
        [{"symbol": "BBB", "timestamp": quote_ts,
          "bid": 10.0, "ask": 10.04, "bid_size": 300, "ask_size": 400,
          "mid": 10.02, "spread_pct": 0.004}],
    )
    store = MarketDataStore(tmp_path)
    row = store.quotes_at_or_before(
        "BBB", pd.Timestamp("2024-09-04 14:00:10", tz="UTC"),
        max_age_seconds=60, feed="iex",
    )
    assert isinstance(row, QuoteRow)
    assert row.timestamp == quote_ts
