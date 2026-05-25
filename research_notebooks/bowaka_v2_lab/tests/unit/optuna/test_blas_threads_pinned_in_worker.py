"""Worker entrypoint pins BLAS threads BEFORE importing numpy.

Speedup report §6.1 / §11.3 Phase 5. ``pin_blas_threads_to_one()`` is the
helper that must run inside every worker process. We assert two things:

1. Calling it in the current process sets every documented env var to ``"1"``.
2. Spawning a subprocess that calls it has the env vars set to ``"1"``
   visibly inside that subprocess at the time numpy would be imported.
"""
from __future__ import annotations

import multiprocessing as _mp
import os

from bowaka_v2_lab.optuna.parallel import (
    _BLAS_THREAD_ENV_VARS,
    pin_blas_threads_to_one,
)


def test_pin_blas_threads_sets_every_env_var():
    # Snapshot + clear so the assertion is meaningful.
    snapshot = {name: os.environ.pop(name, None) for name in _BLAS_THREAD_ENV_VARS}
    try:
        pin_blas_threads_to_one()
        for name in _BLAS_THREAD_ENV_VARS:
            assert os.environ[name] == "1", (
                f"{name} not pinned: got {os.environ.get(name)!r}"
            )
    finally:
        for name, val in snapshot.items():
            if val is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = val


def _worker_check(q: "_mp.Queue") -> None:
    """Subprocess entry — pin, then report env."""
    pin_blas_threads_to_one()
    q.put({name: os.environ.get(name) for name in _BLAS_THREAD_ENV_VARS})


def test_spawn_subprocess_pins_env():
    ctx = _mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_worker_check, args=(q,))
    p.start()
    env = q.get(timeout=30)
    p.join(timeout=30)
    for name in _BLAS_THREAD_ENV_VARS:
        assert env[name] == "1", f"{name} not pinned inside spawn worker"
