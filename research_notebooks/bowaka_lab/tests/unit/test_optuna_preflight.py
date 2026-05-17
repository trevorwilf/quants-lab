"""Phase optuna-1: preflight checks."""

from __future__ import annotations

import logging
import os

import pytest

from bowaka_lab.optuna.preflight import PreflightReport, print_environment, run_preflight


@pytest.fixture(autouse=True)
def _clean_thread_env(monkeypatch):
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        monkeypatch.delenv(var, raising=False)
    yield


def test_print_environment_runs_without_raising(capsys, monkeypatch):
    monkeypatch.setenv("OPTUNA_STORAGE", "postgresql+psycopg2://u:p@h:5432/db")
    print_environment()
    out = capsys.readouterr().out
    assert "bowaka_lab" in out
    assert "Storage" in out


def test_run_preflight_passes_on_postgres_single_worker():
    report = run_preflight(
        n_workers=1, storage_url="postgresql+psycopg2://u:p@h:5432/db", strict=False
    )
    assert report.passed is True
    assert report.errors == []
    assert report.storage_backend == "postgresql"


def test_run_preflight_passes_on_postgres_with_BLAS_pinned_multi_worker(monkeypatch):
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        monkeypatch.setenv(var, "1")
    cpu = os.cpu_count() or 8
    n_workers = min(2, cpu)
    report = run_preflight(
        n_workers=n_workers,
        storage_url="postgresql+psycopg2://u:p@h:5432/db",
        worker_model="processes",
        strict=False,
    )
    assert report.passed is True, report.errors


def test_run_preflight_fails_on_sqlite_with_n_workers_2(monkeypatch):
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        monkeypatch.setenv(var, "1")
    report = run_preflight(n_workers=2, storage_url="sqlite:///x.db", strict=False)
    assert report.passed is False
    assert any("PostgreSQL" in e for e in report.errors)


def test_run_preflight_fails_on_BLAS_not_pinned_multi_worker(monkeypatch):
    monkeypatch.setenv("OMP_NUM_THREADS", "8")
    report = run_preflight(
        n_workers=2,
        storage_url="postgresql+psycopg2://u:p@h:5432/db",
        strict=False,
    )
    assert report.passed is False
    assert any("OMP_NUM_THREADS" in e for e in report.errors)


def test_run_preflight_fails_on_n_workers_exceeds_cpu(monkeypatch):
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        monkeypatch.setenv(var, "1")
    too_many = (os.cpu_count() or 1) + 100
    report = run_preflight(
        n_workers=too_many,
        storage_url="postgresql+psycopg2://u:p@h:5432/db",
        strict=False,
    )
    assert report.passed is False
    assert any("exceeds CPU count" in e for e in report.errors)


def test_run_preflight_strict_raises_ValueError():
    with pytest.raises(ValueError, match="Preflight FAILED"):
        run_preflight(n_workers=2, storage_url="sqlite:///x.db", strict=True)


def test_run_preflight_nonstrict_returns_report_with_errors():
    report = run_preflight(n_workers=2, storage_url="sqlite:///x.db", strict=False)
    assert isinstance(report, PreflightReport)
    assert not report.passed
    assert report.errors
