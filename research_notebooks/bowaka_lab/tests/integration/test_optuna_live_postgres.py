"""Phase optuna-2: live PostgreSQL integration.

Gated behind the ``live_postgres`` marker. The test:

1. Skips automatically when ``OPTUNA_STORAGE`` is not a Postgres URI.
2. Spawns 2 worker processes against the shared study and checks that the
   total number of completed + failed trials equals the requested total.
3. Cleans up the study from Postgres at the end.
"""

from __future__ import annotations

import os
import uuid

import optuna
import pytest

from bowaka_lab.optuna.parallel import run_parallel_optimization
from bowaka_lab.optuna.study import create_study

pytestmark = pytest.mark.live_postgres


def _is_postgres(url):
    return bool(url) and "postgresql" in url.lower()


def _picklable_factory(**kwargs):
    """Top-level picklable factory -- workers must be able to import this."""

    def _obj(trial):
        x = trial.suggest_float("x", -1.0, 1.0)
        return -(x - 0.5) ** 2

    return _obj


@pytest.fixture
def live_storage_url():
    url = os.environ.get("OPTUNA_STORAGE")
    if not _is_postgres(url):
        pytest.skip(
            "Live Postgres test requires OPTUNA_STORAGE to point at a PostgreSQL URI"
        )
    return url


@pytest.fixture
def study_name(live_storage_url):
    name = f"bowaka_live_test_{uuid.uuid4().hex[:12]}"
    yield name
    # Cleanup: delete the study so we don't pollute the shared Postgres.
    try:
        optuna.delete_study(study_name=name, storage=live_storage_url)
    except Exception:
        pass


@pytest.mark.timeout(120)
def test_parallel_smoke_against_live_postgres(live_storage_url, study_name):
    # Pre-create study so workers can load it.
    pre_blas = {
        var: os.environ.get(var)
        for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
    }
    try:
        for var in pre_blas:
            os.environ[var] = "1"
        create_study(study_name, storage_url=live_storage_url, n_startup_trials=4)

        results = run_parallel_optimization(
            study_name=study_name,
            storage_url=live_storage_url,
            n_total_trials=8,
            n_workers=2,
            objective_factory=_picklable_factory,
            factory_kwargs={},
            sampler_seed=42,
            n_startup_trials=4,
        )
        assert len(results) == 2
        total_completed = sum(r.n_completed for r in results)
        total_pruned = sum(r.n_pruned for r in results)
        assert total_completed + total_pruned == 8

        # Reload to confirm trials persisted.
        study = optuna.load_study(study_name=study_name, storage=live_storage_url)
        assert len(study.trials) == 8
    finally:
        for var, val in pre_blas.items():
            if val is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = val
