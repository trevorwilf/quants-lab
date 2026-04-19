"""Verify BLAS thread pinning in subprocess workers.

Stacked parallelism (PAIR_JOBS × N_JOBS × BLAS_THREADS) oversubscribes CPUs
and degrades wall time 30-50% if BLAS threads aren't pinned to 1. Every
subprocess entry point MUST pin BLAS.
"""

from __future__ import annotations

import os
import pickle
from concurrent.futures import ProcessPoolExecutor


BLAS_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)


# Top-level so it's picklable (ProcessPoolExecutor needs that).
def _probe_env_after_pin_blas_optuna():
    from pmm_lab.optuna.parallel import _pin_blas_threads
    _pin_blas_threads()
    return {v: os.environ.get(v) for v in BLAS_VARS}


def _probe_env_after_pin_blas_phase2_directional():
    from pmm_lab.objective.phase2_parallel_directional import _pin_blas_threads
    _pin_blas_threads()
    return {v: os.environ.get(v) for v in BLAS_VARS}


def _probe_env_after_pin_blas_phase2_pmm():
    from pmm_lab.objective.phase2_parallel import _pin_blas_threads
    _pin_blas_threads()
    return {v: os.environ.get(v) for v in BLAS_VARS}


def test_optuna_worker_pins_blas():
    """pmm_lab/optuna/parallel.py::_pin_blas_threads sets every BLAS var to '1'."""
    env = _probe_env_after_pin_blas_optuna()
    for var in BLAS_VARS:
        assert env[var] == "1", f"Optuna worker left {var}={env[var]!r}"


def test_phase2_directional_worker_pins_blas():
    env = _probe_env_after_pin_blas_phase2_directional()
    for var in BLAS_VARS:
        assert env[var] == "1", f"Phase2-directional worker left {var}={env[var]!r}"


def test_phase2_pmm_worker_pins_blas():
    env = _probe_env_after_pin_blas_phase2_pmm()
    for var in BLAS_VARS:
        assert env[var] == "1", f"Phase2-PMM worker left {var}={env[var]!r}"


def test_pin_blas_persists_to_a_subprocess_child():
    """Confirm env vars set by _pin_blas_threads propagate to a subprocess
    child's environment (which is what Optuna actually uses)."""
    with ProcessPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_probe_env_after_pin_blas_optuna)
        env = fut.result()
    for var in BLAS_VARS:
        assert env[var] == "1", f"subprocess left {var}={env[var]!r}"
