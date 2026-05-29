"""Phase 1 (audit 2026-05-29 §8.5) — paper-candidate gate keys on the floor.

A SIP + intended_realism + paper-recon-present finalist is paper-promotable
ONLY when its conservative-floor stress score holds; a sub-floor score flips
``promotable_to_paper`` False and records the cap.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence
from bowaka_v2_lab.optuna.stress_matrix import StressPoint, StressResult


def _floor(score: float) -> list[StressResult]:
    return [StressResult(
        point=StressPoint(50, 2.0, "conservative"), fold_metrics=[],
        score=score, n_trades_total=20, fill_rate_total=0.95,
    )]


def _evidence(stress_results):
    return evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="paper_candidate", stress_results=stress_results,
    )


def test_floor_pass_allows_paper_candidate() -> None:
    ev = _evidence(_floor(0.02))
    assert ev.promotable_to_paper is True
    assert "STRESS_MATRIX_FLOOR_FAILED" not in ev.caps_applied


def test_floor_fail_blocks_paper_candidate() -> None:
    ev = _evidence(_floor(-0.005))
    assert ev.promotable_to_paper is False
    assert "STRESS_MATRIX_FLOOR_FAILED" in ev.caps_applied
