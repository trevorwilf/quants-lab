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

import multiprocessing as _mp
import os
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


def _worker_entrypoint(spec: WorkerSpec, q: "_mp.Queue") -> None:
    """The subprocess body — pin BLAS, load study, run trials, report result."""
    pin_blas_threads_to_one()  # MUST run before numpy import
    start_at = time.monotonic()
    try:
        import optuna

        study = optuna.load_study(study_name=spec.study_name, storage=spec.storage_url)
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
            study.optimize(objective, n_trials=spec.n_trials, n_jobs=1)
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
    results: list[WorkerResult] = []
    for _ in procs:
        results.append(q.get())  # blocks until each worker reports
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
    "pin_blas_threads_to_one",
    "preflight_parallel_dispatch",
    "run_parallel_bowaka_optimization",
]
