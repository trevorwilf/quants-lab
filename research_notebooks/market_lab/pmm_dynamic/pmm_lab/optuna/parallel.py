"""
Process-based Optuna worker launcher.

Spawns N worker *processes*, each calling study.optimize(n_jobs=1).
All workers share the same study via PostgreSQL storage.
This bypasses Python's GIL for CPU-bound simulation objectives.
"""

import os
import time
import logging
import multiprocessing as mp
from typing import Callable, Optional, List
from dataclasses import dataclass

import optuna

logger = logging.getLogger(__name__)


@dataclass
class WorkerResult:
    """Result from a single worker process."""
    worker_id: int
    n_completed: int
    n_pruned: int
    wall_time: float
    error: Optional[str] = None


def _pin_blas_threads():
    """Force single-threaded BLAS inside each worker (must be called before numpy import)."""
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[var] = "1"


def _worker_fn(
    worker_id: int,
    study_name: str,
    storage_url: str,
    n_trials: int,
    objective_factory: Callable,
    factory_kwargs: dict,
    sampler_seed: int,
    n_startup_trials: int,
    result_queue: mp.Queue,
):
    """Worker process entry point.

    Each worker loads the shared study and runs n_trials with n_jobs=1.
    """
    _pin_blas_threads()

    try:
        import optuna as _optuna
        _optuna.logging.set_verbosity(_optuna.logging.WARNING)

        # Each worker gets a unique sampler seed for diversity
        sampler = _optuna.samplers.TPESampler(
            seed=sampler_seed + worker_id,
            multivariate=True,
            n_startup_trials=n_startup_trials,
            warn_independent_sampling=False,
        )

        pruner = _optuna.pruners.MedianPruner(
            n_startup_trials=n_startup_trials,
            n_warmup_steps=1,
            interval_steps=1,
        )

        study = _optuna.load_study(
            study_name=study_name,
            storage=storage_url,
            sampler=sampler,
            pruner=pruner,
        )

        # Build the objective inside the worker process
        objective_fn = objective_factory(**factory_kwargs)

        t0 = time.time()
        study.optimize(
            objective_fn,
            n_trials=n_trials,
            n_jobs=1,  # single thread per process — the key fix
            catch=(Exception,),
        )
        elapsed = time.time() - t0

        completed = len([t for t in study.trials if t.state == _optuna.trial.TrialState.COMPLETE])
        pruned = len([t for t in study.trials if t.state == _optuna.trial.TrialState.PRUNED])

        result_queue.put(WorkerResult(
            worker_id=worker_id,
            n_completed=completed,
            n_pruned=pruned,
            wall_time=elapsed,
        ))

    except Exception as e:
        result_queue.put(WorkerResult(
            worker_id=worker_id,
            n_completed=0,
            n_pruned=0,
            wall_time=0.0,
            error=str(e),
        ))


def run_parallel_optimization(
    study_name: str,
    storage_url: str,
    n_total_trials: int,
    n_workers: int,
    objective_factory: Callable,
    factory_kwargs: dict,
    sampler_seed: int = 12345,
    n_startup_trials: int = 15,
) -> List[WorkerResult]:
    """Launch n_workers processes to optimize a shared Optuna study.

    Parameters
    ----------
    study_name : str
        Name of the study (must already exist in storage).
    storage_url : str
        PostgreSQL connection string for Optuna storage.
    n_total_trials : int
        Total trials across all workers. Each worker runs n_total_trials // n_workers
        (remainder goes to the last worker).
    n_workers : int
        Number of worker processes to spawn.
    objective_factory : Callable
        A function that returns an Optuna objective callable.
        Must be picklable (top-level function, not a closure).
    factory_kwargs : dict
        Keyword arguments passed to objective_factory.
    sampler_seed : int
        Base seed for TPE sampler. Each worker gets sampler_seed + worker_id.
    n_startup_trials : int
        Number of random startup trials for TPE sampler.

    Returns
    -------
    List[WorkerResult]
        Results from each worker process.

    Raises
    ------
    ValueError
        If storage_url is not PostgreSQL.
    """
    if not storage_url or "postgresql" not in storage_url.lower():
        raise ValueError(
            f"Process-based parallel optimization requires PostgreSQL storage. "
            f"Got: {storage_url!r}. Set OPTUNA_STORAGE to a PostgreSQL URI."
        )

    trials_per_worker = n_total_trials // n_workers
    remainder = n_total_trials % n_workers

    result_queue = mp.Queue()
    processes = []

    logger.info(
        "Launching %d worker processes (%d trials each, %d extra in last worker)",
        n_workers, trials_per_worker, remainder,
    )

    for i in range(n_workers):
        worker_trials = trials_per_worker + (remainder if i == n_workers - 1 else 0)

        p = mp.Process(
            target=_worker_fn,
            kwargs=dict(
                worker_id=i,
                study_name=study_name,
                storage_url=storage_url,
                n_trials=worker_trials,
                objective_factory=objective_factory,
                factory_kwargs=factory_kwargs,
                sampler_seed=sampler_seed,
                n_startup_trials=n_startup_trials,
                result_queue=result_queue,
            ),
            daemon=True,
        )
        processes.append(p)

    # Start all workers
    for p in processes:
        p.start()

    # Collect results
    results = []
    for _ in processes:
        results.append(result_queue.get())

    # Wait for all workers to finish
    for p in processes:
        p.join(timeout=30)

    # Report errors
    for r in results:
        if r.error:
            logger.error("Worker %d failed: %s", r.worker_id, r.error)

    return results


def preflight_check(
    n_workers: int,
    storage_url: Optional[str],
    worker_model: str = "processes",
):
    """Run preflight checks before optimization. Raises ValueError on failure.

    Checks:
    1. BLAS thread env vars are 1 when n_workers > 1
    2. Storage is PostgreSQL when using process-based workers
    3. Worker count does not exceed physical CPU cores
    """
    errors = []

    if n_workers > 1:
        for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            val = os.environ.get(var, "not set")
            if val not in ("1", "not set"):
                errors.append(
                    f"{var}={val} but must be '1' when n_workers > 1. "
                    f"Set it in the compose environment or call seed_everything() first."
                )

    if worker_model == "processes":
        if not storage_url or "postgresql" not in str(storage_url).lower():
            errors.append(
                f"Process-based workers require PostgreSQL storage. "
                f"Got OPTUNA_STORAGE={storage_url!r}. "
                f"SQLite does not support concurrent writes safely."
            )

    try:
        cpu_count = os.cpu_count() or 1
        if n_workers > cpu_count:
            errors.append(
                f"n_workers={n_workers} exceeds physical CPU count={cpu_count}. "
                f"Set n_workers <= {cpu_count}."
            )
    except Exception:
        pass

    if errors:
        raise ValueError(
            "Preflight check failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
