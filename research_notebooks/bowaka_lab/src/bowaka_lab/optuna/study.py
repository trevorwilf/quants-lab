"""Optuna study creation and optimization orchestration.

Mirrors ``research_notebooks/market_lab/pmm_dynamic/pmm_lab/optuna/study.py``
with:

- TPE multivariate sampler (n_startup_trials configurable).
- MedianPruner.
- ``load_if_exists=True`` by default so a re-run resumes an existing study.
- ``_wrapped_objective`` records ``failure_type`` / ``failure_message`` on
  failed trials.
- ``run_optimization`` catches per-trial exceptions and handles
  ``KeyboardInterrupt`` gracefully.

Back-compat surface kept intact for callers that still use
:class:`StudyConfig`, :func:`safe_n_jobs`, :func:`optimize`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

import optuna

warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)

from bowaka_lab.optuna.storage import StorageSpec, get_storage_url, resolve_storage


@dataclass
class StudyConfig:
    """Back-compat dataclass for callers that already passed this to
    :func:`create_study`. Prefer the keyword-arg signature for new code."""

    study_name: str = "bowaka_research"
    direction: str = "maximize"
    storage: str | None = None
    sampler_seed: int | None = 12345


def create_study(
    study_name_or_cfg: Union[str, StudyConfig],
    *,
    seed: int = 12345,
    storage_url: Optional[str] = None,
    n_startup_trials: int = 15,
    direction: str = "maximize",
    load_if_exists: bool = True,
) -> optuna.Study:
    """Create or load an Optuna study with the canonical bowaka_lab sampler.

    Accepts either a ``study_name`` string (preferred) or a legacy
    :class:`StudyConfig` instance for back-compat. The sampler is
    ``TPESampler(multivariate=True, n_startup_trials=...)`` and the pruner
    is ``MedianPruner(n_startup_trials=..., n_warmup_steps=1, interval_steps=1)``.
    ``load_if_exists=True`` so re-runs against Postgres resume seamlessly.
    """
    if isinstance(study_name_or_cfg, StudyConfig):
        cfg = study_name_or_cfg
        study_name = cfg.study_name
        if storage_url is None:
            storage_url = cfg.storage
        if cfg.sampler_seed is not None:
            seed = cfg.sampler_seed
        direction = cfg.direction or direction
    else:
        study_name = study_name_or_cfg

    if storage_url is None:
        storage_url = get_storage_url()

    sampler = optuna.samplers.TPESampler(
        seed=seed,
        multivariate=True,
        n_startup_trials=n_startup_trials,
        warn_independent_sampling=False,
    )
    pruner = optuna.pruners.MedianPruner(
        n_startup_trials=n_startup_trials,
        n_warmup_steps=1,
        interval_steps=1,
    )
    return optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction=direction,
        load_if_exists=load_if_exists,
        sampler=sampler,
        pruner=pruner,
    )


def _wrapped_objective(objective: Callable[[optuna.trial.Trial], float]) -> Callable:
    """Wrap ``objective`` to attach ``failure_type`` / ``failure_message`` user
    attrs to the trial when it raises. Re-raises so Optuna marks the trial FAIL.
    """

    def wrapper(trial: optuna.trial.Trial) -> float:
        try:
            return objective(trial)
        except Exception as exc:  # noqa: BLE001
            trial.set_user_attr("failure_type", type(exc).__name__)
            trial.set_user_attr("failure_message", str(exc)[:500])
            raise

    return wrapper


def run_optimization(
    study: optuna.Study,
    objective: Callable[[optuna.trial.Trial], float],
    n_trials: int = 100,
    timeout: Optional[int] = None,
    callbacks: Optional[list] = None,
) -> optuna.Study:
    """Run optimization trials with the wrapped objective + ``catch=(Exception,)``.

    Failed trials carry ``failure_type`` and ``failure_message`` user attrs
    for post-hoc diagnostics. ``KeyboardInterrupt`` returns the partial study
    instead of raising.
    """
    import logging

    _logger = logging.getLogger(__name__)
    try:
        study.optimize(
            _wrapped_objective(objective),
            n_trials=n_trials,
            timeout=timeout,
            callbacks=callbacks,
            catch=(Exception,),
        )
    except KeyboardInterrupt:
        _logger.warning("Optimization interrupted by user, returning partial study")
    return study


# ---------------------------------------------------------------------------
# Back-compat shims
# ---------------------------------------------------------------------------


def safe_n_jobs(requested: int, storage: Optional[str] = None) -> int:
    """Force ``n_jobs=1`` when running against SQLite, with a UserWarning."""
    spec = resolve_storage(storage)
    if spec.requires_n_jobs_1 and requested != 1:
        warnings.warn(
            "SQLite Optuna storage detected; forcing n_jobs=1 to avoid lock contention.",
            stacklevel=2,
        )
        return 1
    return requested


def optimize(
    study: optuna.Study,
    objective_fn: Callable[[optuna.trial.Trial], float],
    *,
    n_trials: int,
    n_jobs: int = 1,
    storage: Optional[str] = None,
) -> None:
    """Back-compat: clamp n_jobs and run study.optimize with gc_after_trial."""
    nj = safe_n_jobs(n_jobs, storage)
    study.optimize(objective_fn, n_trials=n_trials, n_jobs=nj, gc_after_trial=True)
