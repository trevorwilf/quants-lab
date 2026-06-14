"""Phase 1 (audit 2026-05-29 §5.3 / §13.1) — daily-adjustment resolver."""
from __future__ import annotations

from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config


def test_require_split_adjustment_maps_to_split_adjusted() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"require_split_adjustment": True}}
    ) == "split_adjusted"


def test_require_adjusted_daily_bars_maps_to_all() -> None:
    # §3.5 cutover: "adjusted" daily bars are split+dividend ("all"), not split-only
    # (was "split_adjusted", which silently dropped dividend adjustment).
    assert daily_adjustment_for_config(
        {"market_data": {"require_adjusted_daily_bars": True}}
    ) == "all"


def test_require_adjusted_takes_precedence_over_split() -> None:
    # Both flags set (the shipped configs) -> "all" (adjusted is a superset of split).
    assert daily_adjustment_for_config(
        {"market_data": {"require_adjusted_daily_bars": True, "require_split_adjustment": True}}
    ) == "all"


def test_explicit_daily_adjustment_passed_through() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"daily_adjustment": "split_adjusted"}}
    ) == "split_adjusted"


def test_empty_config_defaults_to_raw() -> None:
    assert daily_adjustment_for_config({}) == "raw"
    assert daily_adjustment_for_config({"market_data": {}}) == "raw"


def test_explicit_raw_with_flags_false() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"require_split_adjustment": False, "daily_adjustment": "raw"}}
    ) == "raw"


def test_mixed_adjustment_divergence_detection() -> None:
    """§3.5 — surface the in-window split/dividend sessions where raw-minute
    execution + adjusted-daily features mix scales."""
    from bowaka_v2_lab.data.adjustment import (
        daily_adjustment_divergence_bps,
        is_mixed_adjustment_session,
    )

    # No corporate action: raw == adjusted -> 0 bps, not mixed.
    assert daily_adjustment_divergence_bps(10.0, 10.0) == 0.0
    assert is_mixed_adjustment_session(10.0, 10.0) is False
    # A 2:1 split in-window: adjusted 5.0 vs raw 10.0 -> 5000 bps, mixed.
    assert daily_adjustment_divergence_bps(5.0, 10.0) == 5000.0
    assert is_mixed_adjustment_session(5.0, 10.0) is True
    # A ~0.3% dividend: below the 0.5% threshold -> not flagged (microcap-typical).
    assert is_mixed_adjustment_session(9.97, 10.0) is False
    # Degenerate inputs -> 0 (no false positive).
    assert daily_adjustment_divergence_bps(None, 10.0) == 0.0
    assert daily_adjustment_divergence_bps(10.0, 0.0) == 0.0
