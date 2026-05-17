"""Optuna study factory."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Callable

import optuna

from bowaka_lab.optuna.storage import StorageSpec, resolve_storage


@dataclass
class StudyConfig:
    study_name: str = "bowaka_research"
    direction: str = "maximize"
    storage: str | None = None
    sampler_seed: int | None = 42


def create_study(cfg: StudyConfig | None = None, *, load_if_exists: bool = True) -> optuna.study.Study:
    cfg = cfg or StudyConfig()
    spec = resolve_storage(cfg.storage)
    sampler = optuna.samplers.TPESampler(seed=cfg.sampler_seed)
    return optuna.create_study(
        study_name=cfg.study_name,
        direction=cfg.direction,
        storage=spec.url,
        load_if_exists=load_if_exists,
        sampler=sampler,
    )


def safe_n_jobs(requested: int, storage: str | None = None) -> int:
    """Force n_jobs=1 when running against SQLite, with a warning."""
    spec = resolve_storage(storage)
    if spec.requires_n_jobs_1 and requested != 1:
        warnings.warn(
            "SQLite Optuna storage detected; forcing n_jobs=1 to avoid lock contention.",
            stacklevel=2,
        )
        return 1
    return requested


def optimize(
    study: optuna.study.Study,
    objective_fn: Callable[[optuna.trial.Trial], float],
    *,
    n_trials: int,
    n_jobs: int = 1,
    storage: str | None = None,
) -> None:
    nj = safe_n_jobs(n_jobs, storage)
    study.optimize(objective_fn, n_trials=n_trials, n_jobs=nj, gc_after_trial=True)
