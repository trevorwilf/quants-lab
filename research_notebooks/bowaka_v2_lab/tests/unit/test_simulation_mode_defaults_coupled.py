"""SimulationConfig couples its four policy fields to `mode` (realism Phase 0)."""
from __future__ import annotations

from bowaka_v2_lab.config.models import SimulationConfig


def test_current_code_parity_defaults() -> None:
    sim = SimulationConfig(mode="current_code_parity")
    assert sim.intraday_window_policy == "scanner_start_to_scan"
    assert sim.accepted_event_sequencing == "pre_submit"
    assert sim.unknown_instrument_class_policy == "fail_open"
    assert sim.quote_fallback_policy == "zero_spread"


def test_intended_realism_defaults() -> None:
    sim = SimulationConfig(mode="intended_realism")
    assert sim.intraday_window_policy == "regular_open_to_scan"
    assert sim.accepted_event_sequencing == "post_submit"
    assert sim.unknown_instrument_class_policy == "fail_closed"
    assert sim.quote_fallback_policy == "require_real"


def test_smoke_fixture_defaults() -> None:
    sim = SimulationConfig(mode="smoke_fixture")
    assert sim.intraday_window_policy == "regular_open_to_scan"
    assert sim.accepted_event_sequencing == "pre_submit"
    assert sim.unknown_instrument_class_policy == "fail_open"
    assert sim.quote_fallback_policy == "synthetic_calibrated"


def test_default_mode_is_smoke_fixture() -> None:
    assert SimulationConfig().mode == "smoke_fixture"
    assert SimulationConfig().allow_research_relaxed is False


def test_explicit_override_wins_over_mode_default() -> None:
    """An explicit field overrides only that axis; the rest stay mode-coupled."""
    sim = SimulationConfig(
        mode="current_code_parity", intraday_window_policy="regular_open_to_scan"
    )
    assert sim.intraday_window_policy == "regular_open_to_scan"  # explicit
    assert sim.quote_fallback_policy == "zero_spread"  # still mode-coupled
    assert sim.unknown_instrument_class_policy == "fail_open"  # still mode-coupled


def test_every_coupled_field_is_concrete_after_validation() -> None:
    """No policy field is left None for any mode (so the manifest is complete)."""
    for mode in ("current_code_parity", "intended_realism", "smoke_fixture"):
        sim = SimulationConfig(mode=mode)
        for field in (
            "intraday_window_policy",
            "accepted_event_sequencing",
            "unknown_instrument_class_policy",
            "quote_fallback_policy",
        ):
            assert getattr(sim, field) is not None, f"{mode}.{field} unresolved"
