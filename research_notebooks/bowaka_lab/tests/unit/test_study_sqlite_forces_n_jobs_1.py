"""Phase 9: SQLite Optuna storage forces n_jobs=1 with a warning."""

from __future__ import annotations

import warnings

import pytest

from bowaka_lab.optuna.storage import resolve_storage
from bowaka_lab.optuna.study import safe_n_jobs


def test_sqlite_requires_n_jobs_1():
    spec = resolve_storage("sqlite:///example.db")
    assert spec.requires_n_jobs_1


def test_postgres_allows_parallel():
    spec = resolve_storage("postgresql+psycopg2://u:p@host:5432/db")
    assert not spec.requires_n_jobs_1


def test_safe_n_jobs_clamps_under_sqlite():
    with pytest.warns(UserWarning):
        nj = safe_n_jobs(4, "sqlite:///example.db")
    assert nj == 1


def test_safe_n_jobs_preserves_under_postgres():
    nj = safe_n_jobs(4, "postgresql+psycopg2://u:p@host:5432/db")
    assert nj == 4
