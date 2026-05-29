"""Phase 4 (audit 2026-05-29 §9 Phase 6) — a failing reconcile threshold blocks
paper promotion and names the offending metric.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence


def test_threshold_miss_blocks_paper() -> None:
    report = {
        "status": "ok", "n_sessions": 12, "passes_all_thresholds": False,
        "failing_metrics": ["candidate_recall"],
    }
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="paper_candidate", reconcile_report=report,
    )
    assert ev.promotable_to_paper is False
    assert any("RECONCILE_THRESHOLDS_FAILED" in c and "candidate_recall" in c
               for c in ev.caps_applied)
