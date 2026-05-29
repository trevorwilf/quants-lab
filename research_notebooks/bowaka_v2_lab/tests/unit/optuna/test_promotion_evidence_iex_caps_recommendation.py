"""Phase 2 (audit 2026-05-29 §10.4) — IEX caps parameter recommendation.

Even a valid IEX study with no risk drift must NOT be a parameter
recommendation — IEX is partial-tape. This protects against management
mistaking a clean IEX run for a deployable parameter set.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence


def test_iex_valid_no_drift_still_caps_recommendation() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="iex",
        simulation_mode="intended_realism",  # even intended_realism on IEX
        risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="paper_candidate",
    )
    assert ev.parameter_recommendation_allowed is False
    assert ev.promotable_to_paper is False
    assert ev.promotable_to_live is False
    assert ev.effective_tier == "research_only"
    assert "IEX_PARTIAL_TAPE" in ev.caps_applied
