"""Realism / parity modes require the full live signal-gate set.

Realism Phase 1, Task D, audit P0-001/P0-002. A ``current_code_parity`` or
``intended_realism`` config with a missing live signal threshold must fail
Pydantic validation — a missing threshold silently disables a gate. Setting
``simulation.allow_research_relaxed: true`` opts out (a research run).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from bowaka_v2_lab.config.models import _REALISM_REQUIRED_SIGNAL_GATES, BowakaV2Config

# A full live signal-gate set — every gate in _REALISM_REQUIRED_SIGNAL_GATES set.
_FULL_SIGNALS: dict[str, float] = {
    "rvol_so_far_min": 0.7,
    "projected_full_day_rvol_min": 0.5,
    "prior_atr_pct_min": 0.06,
    "range_expansion_so_far_min": 0.5,
    "close_location_so_far_min": 0.6,
    "ema_distance_min": -0.05,
    "ema_slope_min": -0.05,
    "price_min": 1.0,
    "price_max": 20.0,
    "avg_dollar_volume_min": 250000,
    "rvol_so_far_max": 8.0,
    "projected_full_day_rvol_max": 8.0,
    "range_expansion_so_far_max": 2.5,
    "gap_pct_max": 0.25,
    "current_return_pct_max": 0.5,
}


def _base_cfg(*, simulation: dict, signals: dict) -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": simulation,
        # require_adjusted_daily_bars must be explicit for real-mode configs
        # (realism remediation 2 Phase 1); this test exercises the signal-gate
        # validator, not the adjustment one — set it so the latter is satisfied.
        "market_data": {"feed": "sip", "require_adjusted_daily_bars": True},
        "signals": signals,
        "paths": {
            "lab_root": "research_notebooks/bowaka_v2_lab",
            "data_root": "research_notebooks/bowaka_v2_lab/data",
            "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
        },
    }


def test_full_signal_set_covers_required_gates() -> None:
    """The test's full set must cover every required gate (guards drift)."""
    assert set(_FULL_SIGNALS) == set(_REALISM_REQUIRED_SIGNAL_GATES)


def test_realism_mode_with_missing_threshold_raises() -> None:
    """intended_realism + a missing gate -> ValidationError."""
    partial = dict(_FULL_SIGNALS)
    del partial["rvol_so_far_min"]
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            _base_cfg(simulation={"mode": "intended_realism"}, signals=partial)
        )


def test_parity_mode_with_missing_threshold_raises() -> None:
    """current_code_parity + a missing gate -> ValidationError."""
    partial = dict(_FULL_SIGNALS)
    del partial["gap_pct_max"]
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            _base_cfg(simulation={"mode": "current_code_parity"}, signals=partial)
        )


def test_allow_research_relaxed_lets_partial_signals_pass() -> None:
    """intended_realism + allow_research_relaxed -> partial signals validate."""
    partial = dict(_FULL_SIGNALS)
    del partial["rvol_so_far_min"]
    cfg = BowakaV2Config.model_validate(
        _base_cfg(
            simulation={"mode": "intended_realism", "allow_research_relaxed": True},
            signals=partial,
        )
    )
    assert cfg.simulation.allow_research_relaxed is True


def test_realism_mode_with_full_signals_validates() -> None:
    """intended_realism + the complete gate set validates cleanly."""
    cfg = BowakaV2Config.model_validate(
        _base_cfg(simulation={"mode": "intended_realism"}, signals=dict(_FULL_SIGNALS))
    )
    assert cfg.simulation.mode == "intended_realism"


def test_smoke_mode_does_not_require_full_signals() -> None:
    """smoke_fixture mode never requires the full gate set."""
    cfg = BowakaV2Config.model_validate(
        _base_cfg(simulation={"mode": "smoke_fixture"}, signals={})
    )
    assert cfg.simulation.mode == "smoke_fixture"
