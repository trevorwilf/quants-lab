"""Stage 4: Phase 1 preflight visibility tests.

`optimize_study_for_notebook` must emit a visible preflight message so the
silent serial fallback (when OPTUNA_STORAGE is not PostgreSQL) is impossible
to miss.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest


def _patch_deps():
    """Patch storage/study/dispatch so we don't actually run Optuna."""
    p1 = patch("pmm_lab.optuna.notebook_dispatch.create_study", return_value=MagicMock())
    p2 = patch(
        "pmm_lab.optuna.notebook_dispatch.run_optimization_dispatch",
        return_value=MagicMock(),
    )
    return p1, p2


def test_preflight_warns_on_njobs_gt_1_without_postgres(caplog, capsys):
    from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook

    p1, p2 = _patch_deps()
    with p1, p2, caplog.at_level(logging.WARNING, logger="pmm_lab.optuna.notebook_dispatch"):
        optimize_study_for_notebook(
            study_name="test", storage_url="sqlite:///tmp/foo.db",
            n_trials=10, n_jobs=4,
            objective_factory=lambda **kw: (lambda trial: 0.0),
            factory_kwargs={},
        )

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("SERIAL despite n_jobs=4" in r.getMessage() for r in warnings), (
        f"Expected WARNING mentioning SERIAL fallback; got: {[r.getMessage() for r in warnings]}"
    )
    out = capsys.readouterr().out
    assert "[preflight] Phase 1 dispatch: serial" in out
    assert "storage not PostgreSQL" in out


def test_preflight_info_on_njobs_gt_1_with_postgres(caplog, capsys):
    from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook

    p1, p2 = _patch_deps()
    with p1, p2, caplog.at_level(logging.INFO, logger="pmm_lab.optuna.notebook_dispatch"):
        optimize_study_for_notebook(
            study_name="test",
            storage_url="postgresql+psycopg2://u:p@host:5432/optuna",
            n_trials=10, n_jobs=4,
            objective_factory=lambda **kw: (lambda trial: 0.0),
            factory_kwargs={},
        )

    infos = [r for r in caplog.records if r.levelno == logging.INFO]
    assert any("process-parallel" in r.getMessage() for r in infos), (
        f"Expected INFO mentioning process-parallel; got: {[r.getMessage() for r in infos]}"
    )
    out = capsys.readouterr().out
    assert "[preflight] Phase 1 dispatch: process-parallel" in out
    assert "PostgreSQL" in out


def test_preflight_info_on_njobs_1(caplog, capsys):
    from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook

    p1, p2 = _patch_deps()
    with p1, p2, caplog.at_level(logging.INFO, logger="pmm_lab.optuna.notebook_dispatch"):
        optimize_study_for_notebook(
            study_name="test", storage_url="sqlite:///tmp/foo.db",
            n_trials=10, n_jobs=1,
            objective_factory=lambda **kw: (lambda trial: 0.0),
            factory_kwargs={},
        )

    infos = [r for r in caplog.records if r.levelno == logging.INFO]
    assert any("serial" in r.getMessage().lower() and "n_jobs=1" in r.getMessage()
               for r in infos), (
        f"Expected INFO mentioning serial with n_jobs=1; got: {[r.getMessage() for r in infos]}"
    )
    out = capsys.readouterr().out
    assert "[preflight] Phase 1 dispatch: serial (n_jobs=1)" in out
