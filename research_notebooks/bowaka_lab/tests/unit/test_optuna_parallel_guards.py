"""Phase optuna-2: unit-level guards / dataclass shape for parallel.py.

These tests do not spawn workers -- they cover the synchronous guard at the
top of ``run_parallel_optimization``, the BLAS-pinning helper, and the
``WorkerResult`` shape. Live parallel runs are covered by the integration
suite under the ``live_postgres`` marker.
"""

from __future__ import annotations

import os

import pytest

from bowaka_lab.optuna.parallel import (
    WorkerResult,
    _pin_blas_threads,
    run_parallel_optimization,
)


def _dummy_factory(**kwargs):  # picklable top-level function
    def _obj(trial):
        return trial.suggest_float("x", 0.0, 1.0)

    return _obj


def test_run_parallel_optimization_raises_on_sqlite_storage():
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        run_parallel_optimization(
            study_name="anything",
            storage_url="sqlite:///x.db",
            n_total_trials=4,
            n_workers=2,
            objective_factory=_dummy_factory,
            factory_kwargs={},
        )


def test_run_parallel_optimization_raises_on_none_storage():
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        run_parallel_optimization(
            study_name="anything",
            storage_url=None,  # type: ignore[arg-type]
            n_total_trials=4,
            n_workers=2,
            objective_factory=_dummy_factory,
            factory_kwargs={},
        )


def test_pin_blas_threads_sets_env_vars(monkeypatch):
    for var in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        monkeypatch.delenv(var, raising=False)
    _pin_blas_threads()
    for var in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        assert os.environ[var] == "1"


def test_worker_result_dataclass_fields():
    wr = WorkerResult(worker_id=3, n_completed=10, n_pruned=2, wall_time=1.25)
    assert wr.worker_id == 3
    assert wr.n_completed == 10
    assert wr.n_pruned == 2
    assert wr.wall_time == pytest.approx(1.25)
    assert wr.error is None


def test_worker_result_error_field_optional():
    wr = WorkerResult(
        worker_id=0, n_completed=0, n_pruned=0, wall_time=0.0, error="boom"
    )
    assert wr.error == "boom"
