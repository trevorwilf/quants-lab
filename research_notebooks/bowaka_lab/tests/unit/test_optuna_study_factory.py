"""Phase optuna-1: study factory + wrapped objective + safety shims."""

from __future__ import annotations

import warnings

import optuna
import pytest

from bowaka_lab.optuna.study import (
    StudyConfig,
    create_study,
    run_optimization,
    safe_n_jobs,
)


def _sqlite(tmp_path):
    return f"sqlite:///{tmp_path}/study.db"


def test_create_study_uses_multivariate_tpe_sampler(tmp_path):
    study = create_study("test_mv", storage_url=_sqlite(tmp_path))
    assert isinstance(study.sampler, optuna.samplers.TPESampler)
    assert getattr(study.sampler, "_multivariate", False) is True


def test_create_study_uses_median_pruner(tmp_path):
    study = create_study("test_pruner", storage_url=_sqlite(tmp_path))
    assert isinstance(study.pruner, optuna.pruners.MedianPruner)


def test_create_study_load_if_exists_true(tmp_path):
    url = _sqlite(tmp_path)
    s1 = create_study("test_load", storage_url=url)
    s1.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=3)
    s2 = create_study("test_load", storage_url=url, load_if_exists=True)
    assert len(s2.trials) == 3


def test_wrapped_objective_records_failure_attrs(tmp_path):
    study = create_study("test_failure_attrs", storage_url=_sqlite(tmp_path))

    def objective(trial):
        trial.suggest_float("x", 0, 1)
        raise ValueError("kaboom")

    run_optimization(study, objective, n_trials=1)
    failed = [t for t in study.trials if t.state == optuna.trial.TrialState.FAIL]
    assert failed
    assert failed[-1].user_attrs.get("failure_type") == "ValueError"
    assert "kaboom" in failed[-1].user_attrs.get("failure_message", "")


def test_run_optimization_catches_objective_exceptions(tmp_path):
    study = create_study("test_catches", storage_url=_sqlite(tmp_path))

    def objective(trial):
        x = trial.suggest_float("x", 0, 1)
        if x > 0.5:
            raise RuntimeError("nope")
        return x

    run_optimization(study, objective, n_trials=10)
    assert len(study.trials) == 10
    # Mix of completed + failed; no exception propagates.
    states = {t.state for t in study.trials}
    assert optuna.trial.TrialState.FAIL in states or optuna.trial.TrialState.COMPLETE in states


def test_safe_n_jobs_forces_1_on_sqlite_with_warning():
    with pytest.warns(UserWarning, match="SQLite Optuna storage"):
        nj = safe_n_jobs(4, "sqlite:///example.db")
    assert nj == 1


def test_safe_n_jobs_preserves_under_postgres():
    nj = safe_n_jobs(4, "postgresql+psycopg2://u:p@host:5432/db")
    assert nj == 4


def test_create_study_accepts_legacy_StudyConfig(tmp_path):
    """Back-compat: old test_optuna_smoke uses StudyConfig + load_if_exists=False."""
    cfg = StudyConfig(study_name="legacy_cfg", storage=_sqlite(tmp_path))
    study = create_study(cfg, load_if_exists=False)
    assert isinstance(study, optuna.Study)
