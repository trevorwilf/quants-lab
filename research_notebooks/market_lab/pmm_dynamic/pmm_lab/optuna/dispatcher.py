"""
Optimization dispatch — routes to serial or process-parallel search.
"""

import logging
from typing import Callable, Optional

import optuna

from pmm_lab.optuna.preflight import run_preflight

logger = logging.getLogger(__name__)


def run_optimization_dispatch(
    *,
    study: optuna.Study,
    study_name: str,
    objective_factory: Callable,
    factory_kwargs: dict,
    n_trials: int,
    n_jobs: int,
    certified: bool,
    storage_url: Optional[str],
    strict_parallel: bool = False,
    callbacks: Optional[list] = None,
    sampler_seed: int = 12345,
    n_startup_trials: int = 15,
) -> optuna.Study:
    """Dispatch optimization to serial or process-parallel path.

    Serial mode is used when:
    - certified=True
    - n_jobs == 1
    - parallel preflight fails and strict_parallel=False

    Parallel mode is used when:
    - certified=False
    - n_jobs > 1
    - storage is PostgreSQL
    - BLAS thread preflight passes
    """
    # Force serial for certified or single-job
    if certified or n_jobs <= 1:
        if certified:
            logger.info("  Certified mode: using serial optimization for determinism")
        return _run_serial(study, objective_factory, factory_kwargs, n_trials, callbacks)

    # Attempt parallel
    try:
        preflight = run_preflight(
            n_workers=n_jobs,
            storage_url=storage_url,
            worker_model="processes",
            strict=strict_parallel,
        )
    except ValueError:
        if strict_parallel:
            raise
        logger.warning(
            "Parallel preflight failed. Falling back to serial (n_jobs=1)."
        )
        return _run_serial(study, objective_factory, factory_kwargs, n_trials, callbacks)

    if not preflight.passed:
        logger.warning(
            "Parallel preflight did not pass. Falling back to serial (n_jobs=1)."
        )
        return _run_serial(study, objective_factory, factory_kwargs, n_trials, callbacks)

    # Parallel path
    if callbacks:
        logger.warning(
            "Callbacks are not supported in parallel mode. "
            "They will be skipped. Use post-hoc analysis instead."
        )

    logger.info(
        "Dispatching to process-parallel optimization: %d workers, %d total trials",
        n_jobs, n_trials,
    )

    from pmm_lab.optuna.parallel import run_parallel_optimization

    try:
        worker_results = run_parallel_optimization(
            study_name=study_name,
            storage_url=storage_url,
            n_total_trials=n_trials,
            n_workers=n_jobs,
            objective_factory=objective_factory,
            factory_kwargs=factory_kwargs,
            sampler_seed=sampler_seed,
            n_startup_trials=n_startup_trials,
        )

        # Report worker results
        total_completed = sum(r.n_completed for r in worker_results)
        total_pruned = sum(r.n_pruned for r in worker_results)
        errors = [r for r in worker_results if r.error]
        logger.info(
            "  Parallel optimization complete: %d completed, %d pruned, %d worker errors",
            total_completed, total_pruned, len(errors),
        )
        for r in errors:
            logger.error("  Worker %d failed: %s", r.worker_id, r.error)
    except KeyboardInterrupt:
        logger.warning("Parallel optimization interrupted, reloading partial study")

    # Reload study from storage to get all worker results
    study = optuna.load_study(
        study_name=study_name,
        storage=storage_url,
    )
    return study


def _run_serial(study, objective_factory, factory_kwargs, n_trials, callbacks):
    """Run serial optimization using the existing path."""
    from pmm_lab.optuna.study import run_optimization
    objective_fn = objective_factory(**factory_kwargs)
    return run_optimization(study, objective_fn, n_trials=n_trials, callbacks=callbacks)
