"""Process-parallel Optuna requires PostgreSQL storage.

Speedup report §6.1 / §11.3 Phase 5. SQLite cannot serve concurrent writers
without corruption; passing ``n_jobs > 1`` with SQLite either raises
``OptunaStudyInvalidError`` (strict mode) or falls back to serial with a
log warning (default).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bowaka_v2_lab.optuna.dispatcher import run_bowaka_optimization_dispatch
from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError


def _stub_study():
    study = MagicMock(name="optuna.Study")
    study.optimize = MagicMock()
    return study


def test_strict_parallel_refuses_sqlite():
    study = _stub_study()
    with pytest.raises(OptunaStudyInvalidError) as info:
        run_bowaka_optimization_dispatch(
            study=study, study_name="x",
            objective=lambda t: 0.0,
            objective_factory_dotted=None,
            factory_kwargs={},
            n_trials=4, n_jobs=2,
            storage_url="sqlite:///x.db",
            strict_parallel=True,
        )
    assert "PostgreSQL" in str(info.value) or "postgresql" in str(info.value).lower()


def test_non_strict_parallel_falls_back_to_serial(caplog):
    """SQLite + ``strict_parallel=False`` logs a warning and runs serial."""
    import logging

    study = _stub_study()
    caplog.set_level(logging.WARNING)
    run_bowaka_optimization_dispatch(
        study=study, study_name="x",
        objective=lambda t: 0.0,
        objective_factory_dotted="some:thing",
        factory_kwargs={},
        n_trials=4, n_jobs=2,
        storage_url="sqlite:///x.db",
        strict_parallel=False,
    )
    # The serial path was taken — study.optimize called with n_jobs=1.
    study.optimize.assert_called_once()
    _, call_kwargs = study.optimize.call_args
    assert call_kwargs.get("n_jobs") == 1
    assert call_kwargs.get("n_trials") == 4
    # Some warning about SQLite + parallel was emitted.
    assert any("PostgreSQL" in r.message or "sqlite" in r.message.lower()
               for r in caplog.records)


def test_serial_passthrough_when_n_jobs_le_one():
    """``n_jobs <= 1`` always uses serial in-process optimize."""
    study = _stub_study()
    run_bowaka_optimization_dispatch(
        study=study, study_name="x",
        objective=lambda t: 0.0,
        objective_factory_dotted=None,
        factory_kwargs={},
        n_trials=3, n_jobs=1, storage_url="sqlite:///x.db",
    )
    study.optimize.assert_called_once_with(
        lambda t: 0.0 if False else 0.0,  # placeholder; assert call shape below
        n_trials=3, n_jobs=1,
    ) if False else None
    args, kwargs = study.optimize.call_args
    assert kwargs.get("n_trials") == 3
    assert kwargs.get("n_jobs") == 1


def test_parallel_without_factory_raises():
    study = _stub_study()
    with pytest.raises(OptunaStudyInvalidError) as info:
        run_bowaka_optimization_dispatch(
            study=study, study_name="x",
            objective=lambda t: 0.0,
            objective_factory_dotted=None,
            factory_kwargs={},
            n_trials=2, n_jobs=2,
            storage_url="postgresql+psycopg2://u:p@h:5432/d",
            strict_parallel=True,
        )
    assert "objective_factory_dotted" in str(info.value)
