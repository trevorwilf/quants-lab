"""Parallel workers must use the *configured* TPE sampler, not Optuna's default.

Bug fix (speedup investigation 2026-06-16, plan candidate c3). The dispatcher
creates the study with ``TPESampler(multivariate=True, seed, n_startup_trials)``,
but that sampler lives only in the parent's in-memory ``Study``. A worker that
calls ``optuna.load_study()`` WITHOUT a ``sampler=`` silently runs Optuna's
default ``TPESampler()`` (univariate, ``n_startup_trials=10``, unseeded). These
tests lock in the fix: :func:`build_worker_sampler` reconstructs the configured
sampler with a per-worker seed offset, and the worker entry point uses it.

Pure sampler logic — no market data, fixtures, or suppliers involved.
"""
from __future__ import annotations

import inspect

import optuna

from bowaka_v2_lab.optuna.parallel import build_worker_sampler

optuna.logging.set_verbosity(optuna.logging.WARNING)


def _startup_draws(sampler, n: int = 8) -> list[float]:
    """Draw ``n`` random-startup values from a fresh study driven by ``sampler``.

    ``n_startup_trials`` is large in these tests so every draw is in the
    seed-deterministic random-startup phase (independent sampling off the
    sampler's RNG) — the cleanest behavioural probe of the seed.
    """
    study = optuna.create_study(sampler=sampler, direction="maximize")
    out: list[float] = []
    for _ in range(n):
        t = study.ask()
        out.append(t.suggest_float("x", 0.0, 1.0))
        study.tell(t, 0.0)
    return out


def test_build_worker_sampler_is_multivariate_with_configured_startup():
    sampler = build_worker_sampler(sampler_seed=1337, n_startup_trials=500, worker_id=0)
    assert isinstance(sampler, optuna.samplers.TPESampler)
    # Mirrors OptunaStudy.create(): multivariate, the configured startup count.
    assert getattr(sampler, "_multivariate") is True
    assert getattr(sampler, "_n_startup_trials") == 500


def test_seed_offset_makes_workers_diverge():
    """Two workers with the same base seed must NOT draw the identical sequence."""
    w0 = _startup_draws(build_worker_sampler(sampler_seed=1337, n_startup_trials=100, worker_id=0))
    w1 = _startup_draws(build_worker_sampler(sampler_seed=1337, n_startup_trials=100, worker_id=1))
    assert w0 != w1, "per-worker seed offset failed: workers drew identical samples"


def test_same_worker_is_reproducible():
    """Same (seed, worker_id) → byte-identical draws (reproducibility preserved)."""
    a = _startup_draws(build_worker_sampler(sampler_seed=1337, n_startup_trials=100, worker_id=3))
    b = _startup_draws(build_worker_sampler(sampler_seed=1337, n_startup_trials=100, worker_id=3))
    assert a == b


def test_offset_is_additive_seed_plus_worker_id():
    """worker_id=k with base seed S draws the same as worker_id=0 with base seed S+k.

    Proves the offset is exactly ``sampler_seed + worker_id`` (not some other
    transform), independent of Optuna internals.
    """
    via_offset = _startup_draws(
        build_worker_sampler(sampler_seed=1337, n_startup_trials=100, worker_id=5)
    )
    via_base = _startup_draws(
        build_worker_sampler(sampler_seed=1342, n_startup_trials=100, worker_id=0)
    )
    assert via_offset == via_base


def test_worker_entrypoint_loads_study_with_a_sampler():
    """Regression guard: the worker entry point must pass ``sampler=`` to load_study.

    The original bug was a bare ``optuna.load_study(study_name=, storage=)`` with
    no sampler. Assert the source now constructs the sampler and threads it in,
    so a future refactor can't silently reintroduce the default-sampler bug.
    """
    from bowaka_v2_lab.optuna import parallel

    src = inspect.getsource(parallel._worker_entrypoint)
    assert "build_worker_sampler(" in src
    assert "sampler=sampler" in src


def test_malloc_trim_callback_is_safe_and_returns_none():
    """c10: the malloc_trim callback never raises and returns None (parity-safe).

    On non-glibc/Windows the trim resolves to None and the callback is a pure
    no-op; on Linux it trims freed heap. Either way it must not raise and must
    return None so Optuna ignores it and the trial value is untouched.
    """
    from bowaka_v2_lab.optuna.parallel import make_malloc_trim_callback

    cb = make_malloc_trim_callback(every_k=1)
    for _ in range(5):
        assert cb(object(), object()) is None


def test_worker_entrypoint_passes_malloc_trim_callback():
    """Regression guard: the worker must hand a callback to study.optimize (c10)."""
    from bowaka_v2_lab.optuna import parallel

    src = inspect.getsource(parallel._worker_entrypoint)
    assert "callbacks=[make_malloc_trim_callback()]" in src
