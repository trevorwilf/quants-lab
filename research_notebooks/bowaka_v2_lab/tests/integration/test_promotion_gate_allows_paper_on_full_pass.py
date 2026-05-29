"""Phase 4 (audit 2026-05-29 §9 Phase 6) — a fully-passing reconcile report
allows paper promotion (given an otherwise-eligible SIP run).
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence


def test_full_pass_allows_paper() -> None:
    report = {
        "status": "ok", "n_sessions": 12, "passes_all_thresholds": True,
        "failing_metrics": [],
    }
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="paper_candidate", reconcile_report=report,
    )
    assert ev.promotable_to_paper is True
    assert ev.effective_tier == "paper_candidate"
