"""Notebook preflight checks and observability for bowaka_lab Optuna.

Mirrors ``research_notebooks/market_lab/pmm_dynamic/pmm_lab/optuna/preflight.py``
with the ``pmm_lab`` namespace swapped for ``bowaka_lab``.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PreflightReport:
    """Summary of preflight checks."""

    storage_backend: str
    worker_model: str
    n_workers: int
    blas_threads: dict
    cpu_count: int
    passed: bool
    errors: list


def print_environment():
    """Print environment info at notebook startup."""
    import numpy as np
    import pandas as pd
    import optuna

    try:
        import bowaka_lab

        bowaka_version = bowaka_lab.__version__
    except Exception:
        bowaka_version = "unknown"

    print(f"Python     : {sys.version.split()[0]}")
    print(f"NumPy      : {np.__version__}")
    print(f"Pandas     : {pd.__version__}")
    print(f"Optuna     : {optuna.__version__}")
    print(f"bowaka_lab : {bowaka_version}")

    storage = os.environ.get("OPTUNA_STORAGE", "NOT SET (SQLite fallback)")
    if "postgresql" in str(storage).lower():
        print(f"Storage    : PostgreSQL (SET)")
    else:
        print(f"Storage    : {storage}")

    print(f"CPU cores  : {os.cpu_count()}")

    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        val = os.environ.get(var, "NOT SET")
        flag = " WARNING" if val not in ("1", "NOT SET") else ""
        print(f"{var:25s}: {val}{flag}")


def run_preflight(
    n_workers: int,
    storage_url: Optional[str],
    worker_model: str = "processes",
    strict: bool = True,
) -> PreflightReport:
    """Run preflight checks and return a :class:`PreflightReport`.

    Parameters
    ----------
    n_workers:
        Number of worker processes/threads.
    storage_url:
        Optuna storage URL (or ``None`` for the SQLite fallback).
    worker_model:
        ``"processes"`` or ``"threads"``.
    strict:
        If True, raise :class:`ValueError` on failure.
    """
    errors: list[str] = []
    cpu_count = os.cpu_count() or 1

    blas_threads: dict[str, str] = {}
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        blas_threads[var] = os.environ.get(var, "NOT SET")

    # Check 1: BLAS threads
    if n_workers > 1:
        for var, val in blas_threads.items():
            if val not in ("1", "NOT SET"):
                errors.append(f"{var}={val} must be '1' when running {n_workers} workers.")

    # Check 2: Storage backend
    storage_backend = "unknown"
    if storage_url and "postgresql" in str(storage_url).lower():
        storage_backend = "postgresql"
    elif storage_url and "sqlite" in str(storage_url).lower():
        storage_backend = "sqlite"
    elif not storage_url:
        storage_backend = "sqlite (fallback)"

    if worker_model == "processes" and n_workers > 1 and storage_backend != "postgresql":
        errors.append(f"Process-based workers require PostgreSQL. Storage is: {storage_backend}.")

    if n_workers > 1 and storage_backend != "postgresql":
        errors.append(f"Multi-worker optimization requires PostgreSQL. Storage is: {storage_backend}.")

    # Check 3: CPU oversubscription
    if n_workers > cpu_count:
        errors.append(f"n_workers={n_workers} exceeds CPU count={cpu_count}.")

    # Check 4: Thread model warning
    if worker_model == "threads" and n_workers > 1:
        errors.append(
            f"Thread-based workers with n_workers={n_workers} will not scale for "
            f"CPU-bound simulation. Use worker_model='processes'."
        )

    passed = len(errors) == 0
    report = PreflightReport(
        storage_backend=storage_backend,
        worker_model=worker_model,
        n_workers=n_workers,
        blas_threads=blas_threads,
        cpu_count=cpu_count,
        passed=passed,
        errors=errors,
    )

    if not passed:
        msg = "Preflight FAILED:\n" + "\n".join(f"  - {e}" for e in errors)
        if strict:
            raise ValueError(msg)
        logger.warning(msg)
    else:
        print("Preflight: ALL CHECKS PASSED")

    return report
