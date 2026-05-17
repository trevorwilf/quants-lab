"""Phase optuna-1: storage URL resolution + back-compat."""

from __future__ import annotations

import warnings

import pytest

from bowaka_lab.optuna.storage import (
    StorageSpec,
    get_storage_type,
    get_storage_url,
    require_postgres,
    resolve_storage,
)


def test_get_storage_url_reads_OPTUNA_STORAGE(monkeypatch):
    monkeypatch.setenv("OPTUNA_STORAGE", "postgresql+psycopg2://u:p@host:5432/db")
    monkeypatch.delenv("BOWAKA_OPTUNA_STORAGE", raising=False)
    assert get_storage_url() == "postgresql+psycopg2://u:p@host:5432/db"


def test_get_storage_url_falls_back_to_sqlite_when_unset(monkeypatch):
    monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
    monkeypatch.delenv("BOWAKA_OPTUNA_STORAGE", raising=False)
    url = get_storage_url()
    assert url.startswith("sqlite:///")


def test_get_storage_url_backcompat_reads_BOWAKA_OPTUNA_STORAGE_with_warning(monkeypatch):
    monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
    monkeypatch.setenv("BOWAKA_OPTUNA_STORAGE", "postgresql://legacy:legacy@host:5432/db")
    with pytest.warns(DeprecationWarning, match="BOWAKA_OPTUNA_STORAGE is deprecated"):
        url = get_storage_url()
    assert url == "postgresql://legacy:legacy@host:5432/db"


def test_get_storage_type_postgres(monkeypatch):
    monkeypatch.setenv("OPTUNA_STORAGE", "postgresql+psycopg2://u:p@h:5432/db")
    monkeypatch.delenv("BOWAKA_OPTUNA_STORAGE", raising=False)
    assert get_storage_type() == "postgres"


def test_get_storage_type_sqlite(monkeypatch):
    monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
    monkeypatch.delenv("BOWAKA_OPTUNA_STORAGE", raising=False)
    assert get_storage_type() == "sqlite"


def test_require_postgres_raises_on_sqlite(monkeypatch):
    monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
    monkeypatch.delenv("BOWAKA_OPTUNA_STORAGE", raising=False)
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        require_postgres()


def test_require_postgres_raises_on_explicit_sqlite():
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        require_postgres("sqlite:///x.db")


def test_require_postgres_returns_url_on_postgres():
    url = "postgresql+psycopg2://u:p@h:5432/db"
    assert require_postgres(url) == url


def test_resolve_storage_backcompat_returns_StorageSpec(monkeypatch):
    monkeypatch.setenv("OPTUNA_STORAGE", "postgresql://u:p@h:5432/db")
    spec = resolve_storage()
    assert isinstance(spec, StorageSpec)
    assert "postgresql" in spec.url
    assert spec.requires_n_jobs_1 is False


def test_resolve_storage_sqlite_explicit_requires_n_jobs_1():
    spec = resolve_storage("sqlite:///example.db")
    assert spec.requires_n_jobs_1 is True
