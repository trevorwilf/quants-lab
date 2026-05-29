"""Phase 3 (audit 2026-05-29 §14) — parameter stability scoring."""
from __future__ import annotations

from bowaka_v2_lab.optuna.multi_seed import SeedResult
from bowaka_v2_lab.reports.parameter_stability import compute_parameter_stability


def _sr(seed, a, b):
    p = {"a": a, "b": b}
    return SeedResult(seed, f"s{seed}", p, p, 0.05, [0.05])


def test_stable_dim_scores_one_knife_edge_scores_zero() -> None:
    search_space = {"a": ("uniform", 0.0, 1.0), "b": ("uniform", 0.0, 1.0)}
    # a: every seed at 0.025 (stable). b: spans the full [0, 1] range (knife-edge).
    seeds = [
        _sr(i, 0.025, bv)
        for i, bv in enumerate([0.0, 0.25, 0.5, 0.75, 1.0])
    ]
    rep = compute_parameter_stability(seeds, search_space)
    assert rep["dimensions"]["a"]["stability_score"] == 1.0
    assert rep["dimensions"]["a"]["stable"] is True
    assert rep["dimensions"]["b"]["stability_score"] == 0.0
    assert rep["dimensions"]["b"]["knife_edge"] is True
