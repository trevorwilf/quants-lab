"""Phase 2 (audit 2026-05-29 §8.5) — a single failing envelope dimension blocks
paper-candidate promotion.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence
from bowaka_v2_lab.optuna.stress_matrix import (
    ENVELOPE_DIMENSIONS,
    StressPoint,
    StressResult,
)


def _labeled(adverse_score: float) -> list[StressResult]:
    out: list[StressResult] = []
    for dim in ENVELOPE_DIMENSIONS:
        score = adverse_score if dim == "adverse_selection" else 0.05
        out.append(StressResult(
            point=StressPoint(0, 1.0, "conservative", label=dim),
            fold_metrics=[], score=score, n_trades_total=12, fill_rate_total=0.95,
        ))
    return out


def _evidence(stress_results):
    return evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=True, best_params={"a": 1},
        requested_tier="paper_candidate", stress_results=stress_results,
    )


def test_adverse_selection_dim_failure_blocks_paper() -> None:
    ev = _evidence(_labeled(-0.01))
    assert ev.promotable_to_paper is False
    assert any("adverse_selection" in c for c in ev.caps_applied)


def test_all_dims_positive_allows_paper() -> None:
    ev = _evidence(_labeled(0.05))
    assert ev.promotable_to_paper is True
