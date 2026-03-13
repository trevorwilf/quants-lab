"""Tests for pmm_lab.optuna.storage — storage URL resolution."""

import os
import pytest

from pmm_lab.optuna.storage import get_storage_url, get_storage_type


class TestStorage:
    def test_storage_defaults_to_sqlite(self, monkeypatch):
        """Unset OPTUNA_STORAGE → returns sqlite URL."""
        monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
        url = get_storage_url()
        assert url == "sqlite:///optuna_studies.db"

    def test_storage_reads_env(self, monkeypatch):
        """Set OPTUNA_STORAGE → returns that value."""
        pg_url = "postgresql+psycopg2://optuna:optuna@localhost:5432/optuna"
        monkeypatch.setenv("OPTUNA_STORAGE", pg_url)
        url = get_storage_url()
        assert url == pg_url

    def test_storage_type_detection(self, monkeypatch):
        """get_storage_type returns 'sqlite' when env unset, 'postgres' when set."""
        monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
        assert get_storage_type() == "sqlite"

        monkeypatch.setenv("OPTUNA_STORAGE", "postgresql+psycopg2://...")
        assert get_storage_type() == "postgres"
