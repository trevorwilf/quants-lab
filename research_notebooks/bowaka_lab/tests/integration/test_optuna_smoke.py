"""Phase 9: tiny Optuna smoke run on a fast synthetic objective.

The objective ignores fixture data — it just evaluates a quadratic so we can
verify the study/storage/sampler plumbing works end-to-end within 10 seconds.
"""

from __future__ import annotations

import optuna
import pytest

from bowaka_lab.optuna.study import StudyConfig, create_study, optimize


@pytest.mark.timeout(15)
def test_optuna_smoke(tmp_path):
    storage_url = f"sqlite:///{tmp_path}/test_optuna.db"
    cfg = StudyConfig(study_name="bowaka_lab_smoke", storage=storage_url)
    study = create_study(cfg, load_if_exists=False)

    def objective(trial: optuna.trial.Trial) -> float:
        x = trial.suggest_float("x", -1.0, 1.0)
        # Quadratic with peak at x=0.5
        return -(x - 0.5) ** 2

    optimize(study, objective, n_trials=20, storage=storage_url, n_jobs=4)  # n_jobs will be clamped
    assert len(study.trials) == 20
    best = study.best_value
    assert -0.05 <= best <= 0.0
