"""Phase 3 (audit 2026-05-29 §14.1) — multi-seed orchestrator runs N studies."""
from __future__ import annotations

from bowaka_v2_lab.optuna.multi_seed import run_multi_seed_sweep


def test_runs_one_study_per_seed_with_suffix() -> None:
    calls: list[dict] = []

    def _stub(*, cfg_path, seed, n_trials, study_name, **kw):
        calls.append({"seed": seed, "study_name": study_name, "n_trials": n_trials})
        return {
            "best_params": {"exits.stop_pct": 0.01 * seed},
            "best_value": 0.05 * seed,
            "fold_scores": [0.05 * seed, 0.06 * seed],
        }

    results = run_multi_seed_sweep(
        seeds=(1, 2, 3), n_trials_per_seed=2, cfg_path="cfg.yml", study_runner=_stub,
    )
    assert len(results) == 3
    assert [r.seed for r in results] == [1, 2, 3]
    assert all(r.study_name.endswith(f"__seed={r.seed}") for r in results)
    assert all(c["n_trials"] == 2 for c in calls)
    # params seeded distinctly
    assert results[0].best_params_internal != results[1].best_params_internal
