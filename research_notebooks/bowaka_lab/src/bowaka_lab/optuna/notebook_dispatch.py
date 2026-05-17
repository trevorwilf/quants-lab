"""
Notebook-friendly optimization dispatch.

Wraps the same serial/parallel logic as the main pipeline dispatcher,
but with notebook-specific defaults (e.g., callback handling).
"""

import logging
from typing import Callable, Optional

import optuna

from bowaka_lab.optuna.dispatcher import run_optimization_dispatch
from bowaka_lab.optuna.storage import get_storage_url
from bowaka_lab.optuna.study import create_study

logger = logging.getLogger(__name__)


def optimize_study_for_notebook(
    *,
    study_name: str,
    storage_url: Optional[str] = None,
    n_trials: int,
    n_jobs: int,
    objective_factory: Callable,
    factory_kwargs: dict,
    callbacks: Optional[list] = None,
    strict_parallel: bool = False,
    sampler_seed: int = 12345,
    n_startup_trials: int = 15,
) -> optuna.Study:
    """Notebook entry point for optimization with safe dispatch.

    This is a thin wrapper around run_optimization_dispatch. It:
    1. Creates or loads the Optuna study
    2. Delegates to the same serial/parallel dispatch used by the headless pipeline

    Parameters
    ----------
    study_name : str
        Optuna study name.
    storage_url : str, optional
        Optuna storage URL. If None, uses get_storage_url().
    n_trials : int
        Total number of Optuna trials.
    n_jobs : int
        Number of workers. 1 = serial, >1 = process-parallel (requires PostgreSQL).
    objective_factory : Callable
        A picklable function that returns an Optuna objective callable.
    factory_kwargs : dict
        Keyword arguments passed to objective_factory.
    callbacks : list, optional
        Optuna callbacks. Only used in serial mode; ignored in parallel mode.
    strict_parallel : bool
        If True, raise on misconfigured parallel setup.
        If False (default), warn and fall back to serial.
    sampler_seed : int
        Base seed for the TPE sampler.
    n_startup_trials : int
        Number of random startup trials before TPE kicks in.

    Returns
    -------
    optuna.Study
        The completed study with all trial results.
    """
    if storage_url is None:
        storage_url = get_storage_url()

    # Visible preflight: make serial fallback impossible to miss in a notebook.
    _is_pg = bool(storage_url) and "postgresql" in storage_url.lower()
    if n_jobs > 1 and not _is_pg:
        logger.warning(
            "Optimization will run SERIAL despite n_jobs=%d because OPTUNA_STORAGE is not "
            "PostgreSQL-backed (storage_url=%r). To enable process-parallel search, "
            "set OPTUNA_STORAGE to a PostgreSQL URI.",
            n_jobs, storage_url,
        )
        print(
            f"[preflight] Optimization dispatch: serial (n_jobs={n_jobs}, "
            f"storage not PostgreSQL)"
        )
    elif n_jobs > 1 and _is_pg:
        logger.info(
            "Optimization will attempt process-parallel search with %d workers (PostgreSQL storage)",
            n_jobs,
        )
        print(
            f"[preflight] Optimization dispatch: process-parallel with {n_jobs} workers (PostgreSQL)"
        )
    else:
        logger.info("Optimization will run serial (n_jobs=%d)", n_jobs)
        print(f"[preflight] Optimization dispatch: serial (n_jobs={n_jobs})")

    study = create_study(
        study_name,
        storage_url=storage_url,
        seed=sampler_seed,
        n_startup_trials=n_startup_trials,
    )

    return run_optimization_dispatch(
        study=study,
        study_name=study_name,
        objective_factory=objective_factory,
        factory_kwargs=factory_kwargs,
        n_trials=n_trials,
        n_jobs=n_jobs,
        certified=False,
        storage_url=storage_url,
        strict_parallel=strict_parallel,
        callbacks=callbacks,
        sampler_seed=sampler_seed,
        n_startup_trials=n_startup_trials,
    )
