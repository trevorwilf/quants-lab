"""
Optuna callbacks for logging, early stopping, and degeneracy detection.
"""

import optuna
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DegeneracyCheckCallback:
    """Check for objective degeneracy after a configurable number of trials.

    If after check_after_n_trials, fewer than min_distinct_values distinct
    objective values exist, log a warning.
    """

    def __init__(
        self,
        check_after_n_trials: int = 30,
        min_distinct_values: int = 10,
    ):
        self.check_after_n_trials = check_after_n_trials
        self.min_distinct_values = min_distinct_values
        self._checked = False

    def __call__(self, study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        n_complete = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])

        if n_complete >= self.check_after_n_trials and not self._checked:
            self._checked = True
            values = [t.value for t in study.trials
                      if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None]
            distinct = len(set(round(v, 6) for v in values))

            if distinct < self.min_distinct_values:
                logger.warning(
                    f"DEGENERACY WARNING: Only {distinct} distinct objective values "
                    f"after {n_complete} trials (minimum expected: {self.min_distinct_values}). "
                    f"The objective may be collapsing to a constant. "
                    f"Check objective decomposition and search space."
                )


class TrialLoggingCallback:
    """Log trial results to the console at configurable intervals."""

    def __init__(self, log_every: int = 5):
        self.log_every = log_every

    def __call__(self, study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        n_complete = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        n_pruned = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])

        if n_complete % self.log_every == 0 or trial.number < 3:
            best_value = study.best_value if study.best_trial else None
            logger.info(
                f"Trial {trial.number}: value={trial.value:.4f} | "
                f"Complete: {n_complete}, Pruned: {n_pruned} | "
                f"Best so far: {best_value}"
            )
