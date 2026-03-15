"""Tests for process-based parallel optimization and preflight checks."""

import os
import pytest

from pmm_lab.optuna.parallel import preflight_check


class TestPreflightCheck:
    def test_passes_with_single_worker(self):
        """Single worker should always pass regardless of storage."""
        # Should not raise
        preflight_check(n_workers=1, storage_url=None, worker_model="threads")

    def test_fails_without_postgres_for_processes(self):
        """Process-based workers with SQLite should fail."""
        with pytest.raises(ValueError, match="PostgreSQL"):
            preflight_check(
                n_workers=4,
                storage_url="sqlite:///test.db",
                worker_model="processes",
            )

    def test_fails_with_high_blas_threads(self, monkeypatch):
        """BLAS threads > 1 with multiple workers should fail."""
        monkeypatch.setenv("OMP_NUM_THREADS", "12")
        with pytest.raises(ValueError, match="OMP_NUM_THREADS"):
            preflight_check(
                n_workers=4,
                storage_url="postgresql://localhost/optuna",
                worker_model="processes",
            )

    def test_passes_with_correct_config(self, monkeypatch):
        """Correct config should pass."""
        for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            monkeypatch.setenv(var, "1")
        # Should not raise
        preflight_check(
            n_workers=4,
            storage_url="postgresql://localhost/optuna",
            worker_model="processes",
        )

    def test_fails_without_storage_for_multiworker(self):
        """No storage URL with multi-worker processes should fail."""
        with pytest.raises(ValueError, match="PostgreSQL"):
            preflight_check(
                n_workers=4,
                storage_url=None,
                worker_model="processes",
            )
