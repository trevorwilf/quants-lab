"""Phase 3 (audit 2026-05-29 §14) — local perturbation robustness."""
from __future__ import annotations

from bowaka_v2_lab.optuna.perturbation import perturbation_robustness


def test_robust_when_all_within_tolerance() -> None:
    ss = {"a": ("uniform", 0.0, 1.0)}
    rep = perturbation_robustness(
        base_params={"a": 0.5}, base_score=0.05, search_space=ss,
        score_fn=lambda p: 0.05,
    )
    assert rep["overall_robust"] is True
    assert rep["n_dimensions"] == 1
    assert rep["fragile_dimensions"] == []


def test_fragile_dim_named_when_one_perturbation_drops() -> None:
    ss = {"a": ("uniform", 0.0, 1.0), "b": ("uniform", 0.0, 1.0)}

    def _score(p):
        # perturbing b away from its anchor drops the score by 0.15 (> 0.10 tol).
        if abs(p["b"] - 0.5) > 1e-9:
            return 0.05 - 0.15
        return 0.05

    rep = perturbation_robustness(
        base_params={"a": 0.5, "b": 0.5}, base_score=0.05, search_space=ss,
        score_fn=_score,
    )
    assert rep["overall_robust"] is False
    assert "b" in rep["fragile_dimensions"]
    assert "a" not in rep["fragile_dimensions"]
