"""Phase 4 (audit 2026-05-29 §9 Phase 6) — paper requires a reconcile report."""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence


def test_paper_blocked_without_reconcile_report() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="paper_candidate", reconcile_report=None,
    )
    assert ev.promotable_to_paper is False
    assert "RECONCILE_MISSING" in ev.caps_applied
