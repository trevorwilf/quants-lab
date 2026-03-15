"""Tests for preflight checks and environment reporting."""

import os
import pytest

from pmm_lab.optuna.preflight import run_preflight, print_environment


class TestRunPreflight:
    def test_single_worker_passes(self):
        """Single worker with no storage passes (non-strict)."""
        report = run_preflight(n_workers=1, storage_url=None, worker_model="threads", strict=False)
        assert report.n_workers == 1

    def test_processes_without_postgres_fails_strict(self):
        """Process mode without PostgreSQL fails in strict mode."""
        with pytest.raises(ValueError, match="PostgreSQL"):
            run_preflight(
                n_workers=4,
                storage_url="sqlite:///test.db",
                worker_model="processes",
                strict=True,
            )

    def test_processes_without_postgres_warns_nonstrict(self):
        """Process mode without PostgreSQL warns in non-strict mode."""
        report = run_preflight(
            n_workers=4,
            storage_url="sqlite:///test.db",
            worker_model="processes",
            strict=False,
        )
        assert not report.passed
        assert len(report.errors) > 0

    def test_thread_warning_for_multiworker(self):
        """Thread model with multiple workers should produce a warning."""
        report = run_preflight(
            n_workers=4,
            storage_url="postgresql://localhost/optuna",
            worker_model="threads",
            strict=False,
        )
        assert not report.passed
        assert any("Thread-based" in e for e in report.errors)

    def test_blas_thread_check(self, monkeypatch):
        """High BLAS threads with multi-worker should fail."""
        monkeypatch.setenv("MKL_NUM_THREADS", "8")
        report = run_preflight(
            n_workers=4,
            storage_url="postgresql://localhost/optuna",
            worker_model="processes",
            strict=False,
        )
        assert not report.passed
        assert any("MKL_NUM_THREADS" in e for e in report.errors)

    def test_print_environment_runs(self, capsys):
        """print_environment should not raise."""
        print_environment()
        captured = capsys.readouterr()
        assert "Python" in captured.out
        assert "NumPy" in captured.out


class TestPreflightCorrectConfig:
    def test_all_correct(self, monkeypatch):
        """Fully correct config passes."""
        for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            monkeypatch.setenv(var, "1")
        report = run_preflight(
            n_workers=4,
            storage_url="postgresql://localhost/optuna",
            worker_model="processes",
            strict=True,  # should not raise
        )
        assert report.passed
        assert report.storage_backend == "postgresql"
        assert report.worker_model == "processes"
