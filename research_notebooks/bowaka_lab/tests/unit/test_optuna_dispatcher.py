"""Phase optuna-2: routing logic in ``run_optimization_dispatch``.

These tests cover the decision tree (certified / n_jobs / preflight) without
spawning worker processes. The parallel branch is exercised by mocking
``bowaka_lab.optuna.parallel.run_parallel_optimization`` so we never touch a
real database.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import optuna
import pytest

from bowaka_lab.optuna.dispatcher import run_optimization_dispatch
from bowaka_lab.optuna.parallel import WorkerResult
from bowaka_lab.optuna.study import create_study


def _sqlite(tmp_path):
    return f"sqlite:///{tmp_path}/study.db"


def _quadratic_factory(**kwargs):
    def _obj(trial):
        x = trial.suggest_float("x", -1.0, 1.0)
        return -(x - 0.25) ** 2

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


def test_certified_mode_forces_serial(tmp_path, caplog):
    storage = _sqlite(tmp_path)
    study = create_study("dispatch_certified", storage_url=storage)
    with caplog.at_level("INFO"):
        result = run_optimization_dispatch(
            study=study,
            study_name="dispatch_certified",
            objective_factory=_quadratic_factory,
            factory_kwargs={},
            n_trials=5,
            n_jobs=4,  # would parallelize but certified overrides
            certified=True,
            storage_url=storage,
        )
    assert len(result.trials) == 5
    assert any("Certified mode" in r.message for r in caplog.records)


def test_n_jobs_1_uses_serial(tmp_path):
    storage = _sqlite(tmp_path)
    study = create_study("dispatch_n1", storage_url=storage)
    result = run_optimization_dispatch(
        study=study,
        study_name="dispatch_n1",
        objective_factory=_quadratic_factory,
        factory_kwargs={},
        n_trials=4,
        n_jobs=1,
        certified=False,
        storage_url=storage,
    )
    assert len(result.trials) == 4


def test_nonstrict_falls_back_to_serial_when_sqlite_with_n_jobs_gt_1(tmp_path, caplog):
    storage = _sqlite(tmp_path)
    study = create_study("dispatch_fallback", storage_url=storage)
    with caplog.at_level("WARNING"):
        result = run_optimization_dispatch(
            study=study,
            study_name="dispatch_fallback",
            objective_factory=_quadratic_factory,
            factory_kwargs={},
            n_trials=3,
            n_jobs=2,
            certified=False,
            storage_url=storage,
            strict_parallel=False,
        )
    assert len(result.trials) == 3
    assert any("Falling back to serial" in r.message for r in caplog.records)


def test_strict_parallel_raises_on_sqlite(tmp_path):
    storage = _sqlite(tmp_path)
    study = create_study("dispatch_strict", storage_url=storage)
    with pytest.raises(ValueError, match="Preflight FAILED"):
        run_optimization_dispatch(
            study=study,
            study_name="dispatch_strict",
            objective_factory=_quadratic_factory,
            factory_kwargs={},
            n_trials=3,
            n_jobs=2,
            certified=False,
            storage_url=storage,
            strict_parallel=True,
        )


def test_parallel_path_invoked_when_postgres_and_preflight_passes(tmp_path):
    # Mock the parallel runner so we do not need a live Postgres.
    pg_url = "postgresql+psycopg2://u:p@h:5432/db"
    sqlite_for_study = _sqlite(tmp_path)
    study = create_study("dispatch_parallel", storage_url=sqlite_for_study)

    fake_results = [
        WorkerResult(worker_id=0, n_completed=3, n_pruned=0, wall_time=0.1),
        WorkerResult(worker_id=1, n_completed=3, n_pruned=0, wall_time=0.1),
    ]

    with patch(
        "bowaka_lab.optuna.parallel.run_parallel_optimization",
        return_value=fake_results,
    ) as mock_run, patch(
        "bowaka_lab.optuna.dispatcher.optuna.load_study",
        return_value=study,
    ):
        result = run_optimization_dispatch(
            study=study,
            study_name="dispatch_parallel",
            objective_factory=_quadratic_factory,
            factory_kwargs={},
            n_trials=6,
            n_jobs=2,
            certified=False,
            storage_url=pg_url,
            strict_parallel=False,
        )

    mock_run.assert_called_once()
    kwargs = mock_run.call_args.kwargs
    assert kwargs["study_name"] == "dispatch_parallel"
    assert kwargs["storage_url"] == pg_url
    assert kwargs["n_total_trials"] == 6
    assert kwargs["n_workers"] == 2
    assert result is study


def test_callbacks_skipped_in_parallel_with_warning(tmp_path, caplog):
    pg_url = "postgresql+psycopg2://u:p@h:5432/db"
    sqlite_for_study = _sqlite(tmp_path)
    study = create_study("dispatch_parallel_cb", storage_url=sqlite_for_study)

    cb_calls = []

    def _cb(study, trial):
        cb_calls.append(trial.number)

    fake_results = [
        WorkerResult(worker_id=0, n_completed=1, n_pruned=0, wall_time=0.0),
    ]

    with patch(
        "bowaka_lab.optuna.parallel.run_parallel_optimization",
        return_value=fake_results,
    ), patch(
        "bowaka_lab.optuna.dispatcher.optuna.load_study",
        return_value=study,
    ), caplog.at_level("WARNING"):
        run_optimization_dispatch(
            study=study,
            study_name="dispatch_parallel_cb",
            objective_factory=_quadratic_factory,
            factory_kwargs={},
            n_trials=1,
            n_jobs=2,
            certified=False,
            storage_url=pg_url,
            callbacks=[_cb],
        )
    assert any(
        "Callbacks are not supported in parallel mode" in r.message
        for r in caplog.records
    )
    assert cb_calls == []  # callbacks were not actually invoked
