"""Pure-function: identical inputs → byte-identical event dict (sorted-key JSON)."""
from __future__ import annotations

import json

import pandas as pd

from bowaka_v2_lab.scanner.event_builder import build_candidate_event
from bowaka_v2_lab.utils.serialization import to_json


def _common_kwargs():
    return dict(
        symbol="AAA",
        universe_meta={
            "symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        },
        cfg={
            "data": {"provider": "alpaca", "feed": "iex"},
            "scanner": {"signal_expiry_seconds": 600},
        },
        universe_hash="sha256:abc",
        config_hash_v="sha256:def",
        session_bar={
            "session_open": 100.0, "session_high": 102.0, "session_low": 99.0,
            "last_price": 101.0, "session_volume": 12345.0,
            "session_range": 3.0, "last_bar_timestamp": "2024-09-04T14:30:00+00:00",
        },
        prior_baselines={
            "prior_close": 99.0, "avg_volume_20d": 100_000,
            "avg_dollar_volume_20d": 10_000_000, "prior_atr_14d": 1.5,
            "prior_atr_pct": 0.015, "ema_10_prior": 98.5, "ema_10_lag_3": 98.0,
            "ema_slope_prior": 0.005,
        },
        forming_feats={
            "rvol_so_far": 2.5, "projected_full_day_rvol": 3.0,
            "range_expansion_so_far": 2.0, "close_location_so_far": 0.8,
            "ema_distance": 0.025, "current_return_pct": 0.02, "gap_pct": 0.01,
            "expected_volume_until_scan": 5000.0,
        },
        volume_curve_fraction=0.20,
        gate_results={
            "price_gate": True, "avg_dollar_volume_gate": True, "rvol_gate": True,
            "projected_rvol_gate": True, "prior_atr_pct_gate": True,
            "range_expansion_gate": True, "close_location_gate": True,
            "ema_distance_gate": True, "ema_slope_gate": True, "max_gap_gate": True,
            "max_rvol_gate": True, "max_range_expansion_gate": True,
            "instrument_gate": True,
        },
        candidate_rank=1,
        scan_ts=pd.Timestamp("2024-09-04 14:30:00", tz="UTC"),
        signal_strength=4.5,
        generated_at=pd.Timestamp("2024-09-04 14:30:00", tz="UTC"),
    )


def test_deterministic_for_identical_inputs() -> None:
    a = build_candidate_event(**_common_kwargs())
    b = build_candidate_event(**_common_kwargs())
    assert to_json(a) == to_json(b)


def test_event_carries_strategy_id_and_schema_version() -> None:
    ev = build_candidate_event(**_common_kwargs())
    assert ev["strategy"] == "bowaka_v2"
    assert ev["schema_version"] == 3
    assert ev["event_type"] == "candidate_signal"
    assert ev["candidate_rank"] == 1


def test_event_has_signal_strength_and_gate_results() -> None:
    ev = build_candidate_event(**_common_kwargs())
    assert ev["features"]["signal_strength"] == 4.5
    assert ev["gate_results"]["projected_rvol_gate"] is True


def test_naive_scan_ts_rejected() -> None:
    import pytest
    kw = _common_kwargs()
    kw["scan_ts"] = pd.Timestamp("2024-09-04 14:30:00")  # naive
    with pytest.raises(ValueError, match="tz-aware"):
        build_candidate_event(**kw)
