"""Phase optuna-2: ``optimize_study_for_notebook`` wrapper behavior."""

from __future__ import annotations

from unittest.mock import patch

import optuna
import pytest

from bowaka_lab.optuna.notebook_dispatch import optimize_study_for_notebook
from bowaka_lab.optuna.parallel import WorkerResult


def _sqlite(tmp_path):
    return f"sqlite:///{tmp_path}/study.db"


def _quadratic_factory(**kwargs):
    def _obj(trial):
        x = trial.suggest_float("x", -1.0, 1.0)
        return -(x - 0.5) ** 2

    return _obj


@pytest.fixture(autouse=True)
def _pin_blas(monkeypatch):
    for var in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        monkeypatch.setenv(var, "1")
    yield


def test_serial_path_runs_to_completion_on_sqlite(tmp_path, capsys):
    storage = _sqlite(tmp_path)
    study = optimize_study_for_notebook(
        study_name="nb_serial",
        storage_url=storage,
        n_trials=5,
        n_jobs=1,
        objective_factory=_quadratic_factory,
        factory_kwargs={},
    )
    assert isinstance(study, optuna.Study)
    assert len(study.trials) == 5
    out = capsys.readouterr().out
    assert "[preflight] Optimization dispatch: serial" in out


def test_n_jobs_gt_1_on_sqlite_emits_serial_fallback_message(tmp_path, capsys):
    storage = _sqlite(tmp_path)
    optimize_study_for_notebook(
        study_name="nb_fallback",
        storage_url=storage,
        n_trials=3,
        n_jobs=4,
        objective_factory=_quadratic_factory,
        factory_kwargs={},
    )
    out = capsys.readouterr().out
    assert "serial" in out
    assert "storage not PostgreSQL" in out


def test_n_jobs_gt_1_on_postgres_announces_parallel(tmp_path, capsys):
    pg_url = "postgresql+psycopg2://u:p@h:5432/db"
    fake_results = [
        WorkerResult(worker_id=0, n_completed=2, n_pruned=0, wall_time=0.0),
        WorkerResult(worker_id=1, n_completed=2, n_pruned=0, wall_time=0.0),
    ]

    # We must intercept both parallel & study creation since pg_url is not real.
    sqlite_for_study = _sqlite(tmp_path)
    real_study = optuna.create_study(
        study_name="nb_parallel_announce",
        storage=sqlite_for_study,
        direction="maximize",
    )

    with patch(
        "bowaka_lab.optuna.notebook_dispatch.create_study", return_value=real_study
    ), patch(
        "bowaka_lab.optuna.parallel.run_parallel_optimization",
        return_value=fake_results,
    ), patch(
        "bowaka_lab.optuna.dispatcher.optuna.load_study", return_value=real_study
    ):
        optimize_study_for_notebook(
            study_name="nb_parallel_announce",
            storage_url=pg_url,
            n_trials=4,
            n_jobs=2,
            objective_factory=_quadratic_factory,
            factory_kwargs={},
        )
    out = capsys.readouterr().out
    assert "process-parallel" in out
    assert "2 workers" in out


def test_uses_get_storage_url_when_storage_url_none(tmp_path, monkeypatch):
    fallback = _sqlite(tmp_path)
    monkeypatch.setenv("OPTUNA_STORAGE", fallback)
    monkeypatch.delenv("BOWAKA_OPTUNA_STORAGE", raising=False)

    study = optimize_study_for_notebook(
        study_name="nb_env",
        storage_url=None,
        n_trials=2,
        n_jobs=1,
        objective_factory=_quadratic_factory,
        factory_kwargs={},
    )
    assert len(study.trials) == 2
