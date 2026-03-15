"""Tests for storage safety checks."""

import os
import pytest

from pmm_lab.optuna.storage import get_storage_url, get_storage_type, require_postgres


class TestGetStorageUrl:
    def test_returns_env_var_when_set(self, monkeypatch):
        monkeypatch.setenv("OPTUNA_STORAGE", "postgresql://localhost/optuna")
        assert get_storage_url() == "postgresql://localhost/optuna"

    def test_falls_back_to_sqlite(self, monkeypatch):
        monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
        url = get_storage_url()
        assert "sqlite" in url


class TestGetStorageType:
    def test_postgres_when_set(self, monkeypatch):
        monkeypatch.setenv("OPTUNA_STORAGE", "postgresql://localhost/optuna")
        assert get_storage_type() == "postgres"

    def test_sqlite_when_not_set(self, monkeypatch):
        monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
        assert get_storage_type() == "sqlite"


class TestRequirePostgres:
    def test_passes_with_postgres(self):
        url = require_postgres("postgresql://localhost/optuna")
        assert url == "postgresql://localhost/optuna"

    def test_fails_with_sqlite(self):
        with pytest.raises(ValueError, match="PostgreSQL"):
            require_postgres("sqlite:///test.db")

    def test_fails_with_none(self, monkeypatch):
        monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
        with pytest.raises(ValueError, match="PostgreSQL"):
            require_postgres(None)
