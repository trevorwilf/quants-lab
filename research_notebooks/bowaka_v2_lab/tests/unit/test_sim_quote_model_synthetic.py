"""Synthetic quote shape per [Report §9.8]."""
from __future__ import annotations

import pandas as pd
import pytest

from bowaka_v2_lab.sim.quote_model import QuoteSnapshot, get_quote, synthesize_quote


def test_synthetic_quote_has_required_fields() -> None:
    q = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"),
                          stress_level="conservative",
                          calibration_dataset_hash="sha256:test")
    assert q.source == "synthetic_quote_model_v1"
    assert q.calibration_dataset_hash == "sha256:test"
    assert q.stress_level == "conservative"
    assert q.quote_age_seconds == 0.0
    assert q.spread_pct > 0
    assert q.ask > q.bid
    assert abs(q.mid - 100.0) < 1.0


def test_synthetic_spread_widens_with_stress() -> None:
    q_base = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"),
                                stress_level="base")
    q_severe = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"),
                                  stress_level="severe")
    assert q_severe.spread_pct > q_base.spread_pct


def test_get_quote_prefers_historical_when_present() -> None:
    historical = {"bid": 99.9, "ask": 100.1, "mid": 100.0, "spread_pct": 0.002,
                   "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 0.5,
                   "source": "historical"}
    q = get_quote(symbol="AAA", at=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
                    last_price=100.0, historical_quote=historical)
    assert q.source == "historical"
    assert q.bid == 99.9


def test_synthesize_rejects_zero_last_price() -> None:
    with pytest.raises(ValueError):
        synthesize_quote(last_price=0.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"))


def test_naive_at_rejected() -> None:
    with pytest.raises(ValueError):
        synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00"))
