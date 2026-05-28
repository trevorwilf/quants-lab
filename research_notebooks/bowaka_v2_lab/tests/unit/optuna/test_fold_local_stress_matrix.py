"""Phase 5 — fold-local stress matrix shape + worst-case extraction."""
from __future__ import annotations

from bowaka_v2_lab.optuna.evaluate_finalists import _build_fold_local_stress_matrix


def _finalist(trial_number, axis_scores):
    """axis_scores: {axis_name: [fold0, fold1, ...]}"""
    return {
        "trial_number": trial_number,
        "is_incumbent": False,
        "stress": {
            axis: {"validation": {"fold_scores": scores}}
            for axis, scores in axis_scores.items()
        },
    }


def test_matrix_shape_and_worst_case() -> None:
    rows = [
        _finalist(1, {"cost": [0.5, 0.4], "spread": [0.3, 0.2]}),
        _finalist(2, {"cost": [0.6, 0.1], "spread": [0.45, -0.2]}),
    ]
    m = _build_fold_local_stress_matrix(rows)
    assert m["n_finalists"] == 2
    assert m["n_axes"] == 1  # at least one axis seen
    assert m["n_folds"] == 2
    # Worst cell across all (finalist, fold, axis): -0.2.
    assert m["worst_case_objective"] == -0.2
    # Each finalist row carries by-axis fold scores.
    assert m["matrix"][0]["by_axis"]["cost"] == [0.5, 0.4]


def test_empty_stress_yields_none_worst() -> None:
    rows = [{"trial_number": 1, "stress": {}}]
    m = _build_fold_local_stress_matrix(rows)
    assert m["worst_case_objective"] is None
