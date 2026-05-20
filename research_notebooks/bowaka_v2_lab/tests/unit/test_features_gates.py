"""Parametric tests for every gate at boundary / above / below."""
from __future__ import annotations

import pytest

from bowaka_v2_lab.features import apply_v2_gates


_BASE_FEATURES = {
    "rvol_so_far": 1.5,
    "projected_full_day_rvol": 2.0,
    "range_expansion_so_far": 1.2,
    "close_location_so_far": 0.8,
    "ema_distance": 0.05,
    "gap_pct": 0.02,
}


_PASS_THRESHOLDS = {
    "rvol_so_far_min": 1.0,
    "projected_full_day_rvol_min": 1.0,
    "prior_atr_pct_min": 0.005,
    "range_expansion_so_far_min": 1.0,
    "close_location_so_far_min": 0.5,
    "ema_distance_min": 0.0,
    "ema_slope_min": 0.0,
    "gap_pct_max": 0.10,
    "rvol_so_far_max": 5.0,
    "range_expansion_so_far_max": 3.0,
    "price_min": 1.0,
    "price_max": 1000.0,
    "avg_dollar_volume_min": 100_000,
}


def test_all_gates_pass_in_happy_path() -> None:
    ok, gates = apply_v2_gates(
        _BASE_FEATURES, _PASS_THRESHOLDS,
        price=50.0,
        avg_dollar_volume_20d=5_000_000,
        prior_atr_pct=0.02,
        ema_slope_prior=0.001,
        instrument_class="operating_equity",
    )
    assert ok
    assert all(gates.values())


@pytest.mark.parametrize(
    "feat_key,bad_value,broken_gate",
    [
        ("rvol_so_far", 0.5, "rvol_gate"),
        ("projected_full_day_rvol", 0.5, "projected_rvol_gate"),
        ("range_expansion_so_far", 0.5, "range_expansion_gate"),
        ("close_location_so_far", 0.1, "close_location_gate"),
        ("ema_distance", -0.05, "ema_distance_gate"),
        ("gap_pct", 0.25, "max_gap_gate"),
    ],
)
def test_individual_feature_failures(feat_key: str, bad_value: float, broken_gate: str) -> None:
    feats = {**_BASE_FEATURES, feat_key: bad_value}
    ok, gates = apply_v2_gates(
        feats, _PASS_THRESHOLDS,
        price=50.0,
        avg_dollar_volume_20d=5_000_000,
        prior_atr_pct=0.02,
        ema_slope_prior=0.001,
        instrument_class="operating_equity",
    )
    assert not ok, f"expected {broken_gate} to fail but all passed"
    assert gates[broken_gate] is False


def test_max_rvol_fails_when_above_cap() -> None:
    feats = {**_BASE_FEATURES, "rvol_so_far": 10.0}  # above max=5.0
    ok, gates = apply_v2_gates(
        feats, _PASS_THRESHOLDS,
        price=50.0, avg_dollar_volume_20d=5_000_000, prior_atr_pct=0.02,
        ema_slope_prior=0.001, instrument_class="operating_equity",
    )
    assert gates["max_rvol_gate"] is False
    assert not ok


def test_price_below_min_fails() -> None:
    ok, gates = apply_v2_gates(
        _BASE_FEATURES, _PASS_THRESHOLDS,
        price=0.5,  # below price_min=1.0
        avg_dollar_volume_20d=5_000_000, prior_atr_pct=0.02,
        ema_slope_prior=0.001, instrument_class="operating_equity",
    )
    assert gates["price_gate"] is False
    assert not ok


def test_missing_value_fails_closed_for_ge_gates() -> None:
    # Drop rvol_so_far entirely → fail-closed.
    feats = {k: v for k, v in _BASE_FEATURES.items() if k != "rvol_so_far"}
    ok, gates = apply_v2_gates(
        feats, _PASS_THRESHOLDS,
        price=50.0, avg_dollar_volume_20d=5_000_000, prior_atr_pct=0.02,
        ema_slope_prior=0.001, instrument_class="operating_equity",
    )
    assert gates["rvol_gate"] is False
