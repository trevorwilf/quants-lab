"""Phase 6 — parity mode + no historical quote → zero-spread synthetic quote.

The ``zero_spread`` fallback policy (resolved from ``current_code_parity`` mode)
mirrors the live code's quote gate fallback (``bowaka_v2_strategy.py:743-748``):
``bid == ask == mid == signal_price``, ``spread_pct == 0``, ``age == 0``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.quote_model import (
    SOURCE_SYNTHETIC_ZERO_SPREAD,
    resolve_quote,
    synthesize_zero_spread_quote,
)


def test_zero_spread_fallback_at_signal_price():
    res = resolve_quote(
        symbol="AAA", at=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        signal_price=123.45,
        historical_quote=None,
        quote_fallback_policy="zero_spread",
    )
    assert res.missing_quote is False
    q = res.quote
    assert q is not None
    assert q.source == SOURCE_SYNTHETIC_ZERO_SPREAD
    assert q.bid == q.ask == q.mid == 123.45
    assert q.spread_pct == 0.0
    assert q.quote_age_seconds == 0.0
    assert q.is_synthetic is True
    assert q.is_historical is False


def test_synthesize_zero_spread_directly():
    q = synthesize_zero_spread_quote(
        signal_price=50.0, at=pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    )
    assert q.bid == q.ask == q.mid == 50.0
    assert q.spread_pct == 0.0
    assert q.source == SOURCE_SYNTHETIC_ZERO_SPREAD


def test_historical_quote_still_wins_under_zero_spread_policy():
    """A real historical quote is used even when the policy is zero_spread."""
    historical = {
        "bid": 99.9, "ask": 100.1, "mid": 100.0, "spread_pct": 0.002,
        "quote_timestamp": "2024-09-04T14:00:00Z", "quote_age_seconds": 0.5,
        "source": "historical",
    }
    res = resolve_quote(
        symbol="AAA", at=pd.Timestamp("2024-09-04 14:00:01", tz="UTC"),
        signal_price=100.0,
        historical_quote=historical,
        quote_fallback_policy="zero_spread",
    )
    assert res.is_historical is True
    assert res.quote.source == "historical"
    assert res.quote.bid == 99.9
