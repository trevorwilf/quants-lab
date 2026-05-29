"""Phase 2 (audit 2026-05-29 §6.8 / §10.4) — structured promotion evidence."""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import (
    PromotionEvidence,
    evaluate_promotion_evidence,
)


def test_invalid_study_blocks_everything() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=False, invalid_reasons=["CONSTANT_OBJECTIVE_SURFACE"],
        feed="sip", simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="live_candidate",
    )
    assert isinstance(ev, PromotionEvidence)
    assert ev.reviewable_for_research is False
    assert ev.parameter_recommendation_allowed is False
    assert ev.promotable_to_paper is False
    assert ev.promotable_to_live is False
    assert ev.best_params is None
    assert ev.effective_tier == "research_only"


def test_valid_iex_parity_is_research_only() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="iex",
        simulation_mode="current_code_parity", risk_control_drift=False,
        paper_reconciliation_artifact_present=False, best_params={"a": 1},
        requested_tier="research_only",
    )
    assert ev.reviewable_for_research is True
    assert ev.parameter_recommendation_allowed is False
    assert ev.promotable_to_paper is False
    assert ev.promotable_to_live is False
    assert ev.effective_tier == "research_only"
    assert "IEX_PARTIAL_TAPE" in ev.caps_applied


def test_valid_sip_realism_without_reconciliation_is_backtesting_only() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=False, best_params={"a": 1},
        requested_tier="paper_candidate",
    )
    assert ev.parameter_recommendation_allowed is True
    assert ev.promotable_to_paper is False
    assert ev.effective_tier == "backtesting_only"


def test_valid_sip_realism_with_reconciliation_can_reach_live() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="live_candidate",
    )
    assert ev.promotable_to_paper is True
    assert ev.promotable_to_live is True
    assert ev.effective_tier == "live_candidate"
