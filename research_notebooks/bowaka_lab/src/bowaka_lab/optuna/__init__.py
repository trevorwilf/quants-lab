"""Optuna integration: storage, study creation, preflight, callbacks, dispatch."""

from bowaka_lab.optuna.callbacks import (
    DegeneracyCheckCallback,
    TqdmProgressCallback,
    TrialLoggingCallback,
)
from bowaka_lab.optuna.dispatcher import run_optimization_dispatch
from bowaka_lab.optuna.notebook_dispatch import optimize_study_for_notebook
from bowaka_lab.optuna.parallel import WorkerResult, run_parallel_optimization
from bowaka_lab.optuna.preflight import (
    PreflightReport,
    print_environment,
    run_preflight,
)
from bowaka_lab.optuna.storage import (
    StorageSpec,
    get_storage_type,
    get_storage_url,
    require_postgres,
    resolve_storage,
)
from bowaka_lab.optuna.study import (
    StudyConfig,
    create_study,
    optimize,
    run_optimization,
    safe_n_jobs,
)

__all__ = [
    "StorageSpec",
    "get_storage_url",
    "get_storage_type",
    "require_postgres",
    "resolve_storage",
    "StudyConfig",
    "create_study",
    "run_optimization",
    "safe_n_jobs",
    "optimize",
    "PreflightReport",
    "print_environment",
    "run_preflight",
    "DegeneracyCheckCallback",
    "TrialLoggingCallback",
    "TqdmProgressCallback",
    "WorkerResult",
    "run_parallel_optimization",
    "run_optimization_dispatch",
    "optimize_study_for_notebook",
]
