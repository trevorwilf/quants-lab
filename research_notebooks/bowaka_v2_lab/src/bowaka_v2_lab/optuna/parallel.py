"""Process-parallel Optuna launcher (speedup report §6.1 / §10.5 / §11.3).

Conceptually mirrors ``pmm_lab/optuna/parallel.py`` but is independently
implemented (Bowaka v2 must not import from pmm_lab).

A worker is a fresh Python subprocess (``multiprocessing.get_context("spawn")``)
that:

1. **Pins BLAS threads to 1 BEFORE importing NumPy.** Without this each worker
   may oversubscribe a multi-core BLAS library and contend with sibling workers.
2. Loads the study from the shared PostgreSQL storage URL.
3. Runs ``study.optimize(objective_factory(**factory_kwargs), n_trials=
   worker_trials, n_jobs=1)``.
4. Returns a :class:`WorkerResult` summarizing how many trials completed,
   pruned, or failed.

The launcher itself only orchestrates: it does NOT touch the study state
except to count how many trials each worker reported, and it asserts the
memory reserve before launch.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import multiprocessing as _mp
import os
import queue as _queue
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

from ..utils.memory_guard import MemoryBudget, MemoryReserveViolation
from .errors import OptunaStudyInvalidError


@dataclass
class WorkerResult:
    worker_id: int
    n_completed: int = 0
    n_pruned: int = 0
    n_failed: int = 0
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class WorkerSpec:
    worker_id: int
    n_trials: int
    storage_url: str
    study_name: str
    sampler_seed: int
    n_startup_trials: int
    objective_factory_dotted: str
    factory_kwargs: dict[str, Any]


_BLAS_THREAD_ENV_VARS: tuple[str, ...] = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def pin_blas_threads_to_one() -> None:
    """Set every BLAS-thread env var to ``1`` for the current process.

    MUST be called before NumPy / SciPy / pandas import. The worker entry
    point is the canonical call site; tests may call it to verify the env.
    """
    for name in _BLAS_THREAD_ENV_VARS:
        os.environ[name] = "1"


def _import_dotted(dotted: str) -> Any:
    """Resolve ``"pkg.mod:attr"`` to the imported attribute."""
    module_path, _, attr = dotted.partition(":")
    if not module_path or not attr:
        raise ValueError(
            f"invalid dotted reference {dotted!r}; expected 'module.path:attr'"
        )
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, attr)


def build_worker_sampler(*, sampler_seed: int, n_startup_trials: int, worker_id: int) -> Any:
    """Reconstruct the *configured* TPE sampler for a parallel worker.

    Bug fix (speedup investigation 2026-06-16, plan candidate c3). The parent
    dispatcher creates the study via :meth:`OptunaStudy.create` with
    ``TPESampler(multivariate=True, seed=sampler_seed, n_startup_trials=...)``,
    but that sampler instance lives only in the parent's *in-memory* ``Study``
    object — it is NOT persisted to the RDB. A worker that calls
    :func:`optuna.load_study` WITHOUT a ``sampler=`` argument therefore silently
    runs Optuna's DEFAULT sampler (``TPESampler()`` — univariate,
    ``n_startup_trials=10``, unseeded), not the configured multivariate sampler.
    The ``sampler_seed`` / ``n_startup_trials`` carried on :class:`WorkerSpec`
    were threaded all the way through but never actually used.

    This helper rebuilds the sampler exactly as :meth:`OptunaStudy.create` does
    (``multivariate=True``, the configured ``n_startup_trials``), with a
    **per-worker seed offset** (``sampler_seed + worker_id``) so each worker's
    random-startup proposals diverge instead of every worker drawing the
    identical sequence — the standard recipe for shared-storage parallel TPE.
    Keeping construction in one tested helper guarantees the workers stay in
    lock-step with the parent's sampler definition.
    """
    import optuna

    return optuna.samplers.TPESampler(
        multivariate=True,
        seed=int(sampler_seed) + int(worker_id),
        n_startup_trials=int(n_startup_trials),
    )


#: c10 — trim freed heap back to the OS every K completed trials per worker.
_MALLOC_TRIM_EVERY_K = 25


def _resolve_malloc_trim() -> Optional[Callable[[int], int]]:
    """Return glibc ``malloc_trim`` if available on this platform, else ``None``.

    On Linux/glibc this returns the ``malloc_trim`` symbol; on Windows / musl /
    any libc-resolution failure it returns ``None`` so the caller no-ops.
    """
    try:
        libc_name = ctypes.util.find_library("c") or "libc.so.6"
        return ctypes.CDLL(libc_name).malloc_trim
    except Exception:  # noqa: BLE001 — non-glibc / Windows / resolution failure
        return None


def make_malloc_trim_callback(every_k: int = _MALLOC_TRIM_EVERY_K) -> Callable[[Any, Any], None]:
    """An Optuna ``study.optimize`` callback that returns freed heap to the OS.

    c10 (speedup investigation 2026-06-16) — bounds the worker RSS climb (~17
    GiB/hr observed) so a long study does not hit the container RAM wall and force
    a restart (each restart re-pays cold imports + the fold-context build). This is
    allocator-level ONLY: ``malloc_trim(0)`` returns already-freed pages to the OS
    and never touches a live Python object, the trial value, or the sampler RNG.
    Optuna invokes callbacks AFTER the trial's value is recorded, and the callback
    returns ``None``, so it cannot change any trial result (parity-safe). No-op on
    non-glibc / Windows, and any trim error is swallowed so it can never fail a trial.
    """
    trim = _resolve_malloc_trim()
    seen = [0]

    def _cb(study: Any, trial: Any) -> None:  # noqa: ARG001 — Optuna callback signature
        seen[0] += 1
        if trim is not None and every_k > 0 and seen[0] % every_k == 0:
            try:
                trim(0)
            except Exception:  # noqa: BLE001 — never fail a trial on a trim error
                pass

    return _cb


def _worker_entrypoint(spec: WorkerSpec, q: "_mp.Queue") -> None:
    """The subprocess body — pin BLAS, load study, run trials, report result."""
    pin_blas_threads_to_one()  # MUST run before numpy import
    start_at = time.monotonic()
    try:
        import optuna

        # c3 fix: reconstruct the CONFIGURED sampler (multivariate, configured
        # n_startup_trials, per-worker-offset seed). Without an explicit
        # ``sampler=`` the worker would silently use Optuna's default TPESampler.
        sampler = build_worker_sampler(
            sampler_seed=spec.sampler_seed,
            n_startup_trials=spec.n_startup_trials,
            worker_id=spec.worker_id,
        )
        study = optuna.load_study(
            study_name=spec.study_name, storage=spec.storage_url, sampler=sampler,
        )
        factory = _import_dotted(spec.objective_factory_dotted)
        objective = factory(**spec.factory_kwargs)
        before_complete = sum(
            1 for t in study.get_trials(deepcopy=False)
            if t.state == optuna.trial.TrialState.COMPLETE
        )
        before_pruned = sum(
            1 for t in study.get_trials(deepcopy=False)
            if t.state == optuna.trial.TrialState.PRUNED
        )
        before_failed = sum(
            1 for t in study.get_trials(deepcopy=False)
            if t.state == optuna.trial.TrialState.FAIL
        )
        try:
            study.optimize(
                objective, n_trials=spec.n_trials, n_jobs=1,
                callbacks=[make_malloc_trim_callback()],  # c10 — bound RSS climb
            )
        except Exception as opt_exc:  # noqa: BLE001 — reported back to dispatcher
            q.put(WorkerResult(
                worker_id=spec.worker_id,
                n_completed=0, n_pruned=0, n_failed=spec.n_trials,
                error=f"{type(opt_exc).__name__}: {opt_exc}",
                elapsed_seconds=time.monotonic() - start_at,
            ))
            return
        after_complete = sum(
            1 for t in study.get_trials(deepcopy=False)
            if t.state == optuna.trial.TrialState.COMPLETE
        )
        after_pruned = sum(
            1 for t in study.get_trials(deepcopy=False)
            if t.state == optuna.trial.TrialState.PRUNED
        )
        after_failed = sum(
            1 for t in study.get_trials(deepcopy=False)
            if t.state == optuna.trial.TrialState.FAIL
        )
        q.put(WorkerResult(
            worker_id=spec.worker_id,
            n_completed=after_complete - before_complete,
            n_pruned=after_pruned - before_pruned,
            n_failed=after_failed - before_failed,
            error=None,
            elapsed_seconds=time.monotonic() - start_at,
        ))
    except Exception as exc:  # noqa: BLE001 — pre-optimize failure
        q.put(WorkerResult(
            worker_id=spec.worker_id,
            n_completed=0, n_pruned=0, n_failed=spec.n_trials,
            error=f"{type(exc).__name__}: {exc}",
            elapsed_seconds=time.monotonic() - start_at,
        ))


def _drain_worker_results(
    procs: "list[_mp.Process]", q: Any, *, poll_timeout: float = 2.0
) -> list[WorkerResult]:
    """Drain one :class:`WorkerResult` per process WITHOUT deadlocking on a dead worker.

    c9 liveness slice (speedup investigation 2026-06-16). The legacy drain was
    ``for _ in procs: results.append(q.get())`` — a blocking ``q.get()`` per
    process. If a worker dies WITHOUT putting a result (OOM-killed / crashed mid
    study — a real hazard over a 2-3 day run; see c10's RSS note) that ``q.get()``
    blocks FOREVER and hangs the whole study. Here ``q.get(timeout=...)`` returns a
    result immediately when one is available (the timeout only bounds the idle
    wait), so the happy path is unchanged; once every process has exited and the
    queue is drained we stop and synthesize a failure result for each worker that
    never reported, so the dispatcher's ``sum(n_completed)`` / ``all(r.error)``
    logic stays correct instead of hanging.
    """
    results: list[WorkerResult] = []
    n = len(procs)
    while len(results) < n:
        try:
            results.append(q.get(timeout=poll_timeout))
            continue
        except _queue.Empty:
            pass
        if not any(p.is_alive() for p in procs):
            # Every worker has exited — drain any results still buffered, then stop.
            while True:
                try:
                    results.append(q.get_nowait())
                except _queue.Empty:
                    break
            break
    missing = n - len(results)
    for _ in range(missing):
        results.append(WorkerResult(
            worker_id=-1, n_completed=0, n_pruned=0, n_failed=0,
            error="worker exited without reporting (likely OOM/crash)",
        ))
    return results


def _split_trials(n_total: int, n_workers: int) -> list[int]:
    """Spread ``n_total`` trials across ``n_workers`` chunks; last absorbs remainder."""
    if n_workers <= 0:
        return []
    base = n_total // n_workers
    chunks = [base] * n_workers
    chunks[-1] += n_total - base * n_workers
    return chunks


def run_parallel_bowaka_optimization(
    *,
    study_name: str,
    storage_url: str,
    n_total_trials: int,
    n_workers: int,
    objective_factory_dotted: str,
    factory_kwargs: dict[str, Any],
    sampler_seed: int = 1337,
    n_startup_trials: int = 25,
    memory_budget: Optional[MemoryBudget] = None,
) -> list[WorkerResult]:
    """Launch ``n_workers`` spawn subprocesses against the shared study.

    Each worker pins BLAS to 1 thread, loads the study from
    ``storage_url`` (must be PostgreSQL — caller enforces), constructs its
    objective from ``objective_factory_dotted(**factory_kwargs)``, and
    runs ``n_trials`` of ``study.optimize``.

    Returns one :class:`WorkerResult` per worker.
    """
    if memory_budget is not None:
        memory_budget.assert_available_reserve()
    n_workers = max(1, int(n_workers))
    trials_per_worker = _split_trials(int(n_total_trials), n_workers)
    ctx = _mp.get_context("spawn")
    q: "_mp.Queue" = ctx.Queue()
    procs: list[_mp.Process] = []
    for wid, n_trials in enumerate(trials_per_worker):
        if n_trials <= 0:
            continue
        spec = WorkerSpec(
            worker_id=wid, n_trials=n_trials,
            storage_url=storage_url, study_name=study_name,
            sampler_seed=sampler_seed, n_startup_trials=n_startup_trials,
            objective_factory_dotted=objective_factory_dotted,
            factory_kwargs=factory_kwargs,
        )
        p = ctx.Process(target=_worker_entrypoint, args=(spec, q))
        p.start()
        procs.append(p)
    # c9 (liveness): drain without deadlocking if a worker dies without reporting.
    results = _drain_worker_results(procs, q)
    for p in procs:
        p.join()
    results.sort(key=lambda r: r.worker_id)
    return results


@dataclass(frozen=True)
class ParallelDecision:
    """The result of :func:`preflight_parallel_dispatch`.

    ``mode``:

    * ``"serial"`` — run ``study.optimize`` in-process; the parent SHOULD
      build the fold contexts once (legacy behaviour).
    * ``"process_parallel"`` — spawn workers against the shared storage URL;
      the parent MUST NOT build fold contexts (each worker rebuilds them
      via the dotted-factory entrypoint).

    ``reason`` is a human-readable note surfaced in study user_attrs.
    """

    mode: Literal["serial", "process_parallel"]
    n_workers: int
    reason: str


def preflight_parallel_dispatch(
    study: Any,
    *,
    n_jobs: int,
    storage_uri: Optional[str],
    mem_budget: MemoryBudget,
    strict_parallel: bool,
) -> ParallelDecision:
    """Decide serial vs process-parallel BEFORE any expensive setup.

    Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 task 1. Runs the same
    storage + memory checks the in-process dispatcher used to perform AFTER
    fold contexts were already built; bubbling them up here means the
    strict-parallel parent never pays the context-build cost when it cannot
    legally launch workers.

    Rules:

    * ``n_jobs <= 1`` → ``serial``, no further checks.
    * Process-parallel REQUIRES a PostgreSQL storage URL.
      ``sqlite:`` / in-memory studies cannot host concurrent writers safely.
      Either ``strict_parallel`` mode raises here (regardless of count), so
      the only way to run against SQLite is ``n_jobs == 1`` (which still
      returns ``serial``).
    * Memory: ``mem_budget.assert_launch_safe(0.0, n_workers=n_jobs)``. On
      :class:`MemoryReserveViolation`:
      - ``strict_parallel`` → raises :class:`OptunaStudyInvalidError`.
      - otherwise → returns ``serial`` with the violation reason.
    """
    if int(n_jobs) <= 1:
        return ParallelDecision(mode="serial", n_workers=1, reason="n_jobs <= 1")
    if not storage_uri or "postgresql" not in str(storage_uri).lower():
        raise OptunaStudyInvalidError(
            "process-parallel Optuna requires an RDB (PostgreSQL), not SQLite; "
            f"got storage_uri={storage_uri!r}. Set "
            "OPTUNA_STORAGE=postgresql+psycopg2://... or run with n_jobs=1. "
            "See speedup report v2 §7.5."
        )
    try:
        mem_budget.assert_launch_safe(
            feature_store_gib_estimate=0.0,
            n_workers=int(n_jobs),
        )
    except MemoryReserveViolation as exc:
        if strict_parallel:
            raise OptunaStudyInvalidError(
                f"strict_parallel: {exc}"
            )
        return ParallelDecision(
            mode="serial", n_workers=1,
            reason=f"memory refused parallel; falling back: {exc}",
        )
    return ParallelDecision(
        mode="process_parallel", n_workers=int(n_jobs), reason="ok",
    )


__all__ = [
    "ParallelDecision",
    "WorkerResult",
    "WorkerSpec",
    "_BLAS_THREAD_ENV_VARS",
    "build_worker_sampler",
    "make_malloc_trim_callback",
    "pin_blas_threads_to_one",
    "preflight_parallel_dispatch",
    "run_parallel_bowaka_optimization",
]
