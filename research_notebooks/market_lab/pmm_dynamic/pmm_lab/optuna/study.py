"""
Optuna study creation and optimization orchestration.
"""

import optuna
import warnings
warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)
from typing import Optional, Callable

from pmm_lab.optuna.storage import get_storage_url


def create_study(
    study_name: str,
    seed: int = 12345,
    storage_url: Optional[str] = None,
    n_startup_trials: int = 15,
    pruner: Optional["optuna.pruners.BasePruner"] = None,
) -> optuna.Study:
    """Create or load an Optuna study.

    Parameters
    ----------
    study_name : str
        Study name. Convention: "{connector}_{pair}_{interval}_pmm_dynamic_v1"
    seed : int
        Random seed for the TPE sampler.
    storage_url : str, optional
        Override the storage URL. If None, uses get_storage_url().
    n_startup_trials : int
        Number of random trials before TPE kicks in.
    pruner : optuna.pruners.BasePruner, optional
        Override the pruner. Default: MedianPruner (historical behavior).
        The range_ladder walk-forward notebook passes a HyperbandPruner.
    """
    if storage_url is None:
        storage_url = get_storage_url()

    sampler = optuna.samplers.TPESampler(
        seed=seed,
        multivariate=True,
        n_startup_trials=n_startup_trials,
        warn_independent_sampling=False,
    )

    if pruner is None:
        pruner = optuna.pruners.MedianPruner(
            n_startup_trials=n_startup_trials,
            n_warmup_steps=1,
            interval_steps=1,
        )

    study = optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction="maximize",
        load_if_exists=True,
        sampler=sampler,
        pruner=pruner,
    )

    return study


def _wrapped_objective(objective):
    """Wrap objective to record exception info on failed trials."""
    def wrapper(trial):
        try:
            return objective(trial)
        except Exception as e:
            trial.set_user_attr("failure_type", type(e).__name__)
            trial.set_user_attr("failure_message", str(e)[:500])
            raise
    return wrapper


def run_optimization(
    study: optuna.Study,
    objective: Callable,
    n_trials: int = 100,
    timeout: Optional[int] = None,
    callbacks: Optional[list] = None,
) -> optuna.Study:
    """Run optimization trials.

    Failed trials will have ``failure_type`` and ``failure_message``
    user attributes for post-hoc diagnostics.
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
