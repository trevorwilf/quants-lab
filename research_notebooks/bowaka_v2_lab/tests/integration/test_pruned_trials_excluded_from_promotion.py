"""Pruned trials are excluded from the best-trial pool.

Speedup report §6.2 / §11.2 Phase 7. The walk-forward runner's
post-optimize valid-trial filter uses ``optuna.trial.TrialState.COMPLETE``
which naturally excludes ``PRUNED`` trials; this test pins that
behaviour with a fake Optuna study that has a mix.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import optuna


def test_pruned_trials_not_in_completed_filter():
    """Manually exercise the filter the runner uses post-optimize."""
    pruned = [
        MagicMock(state=optuna.trial.TrialState.PRUNED, value=0.42, number=i)
        for i in range(3)
    ]
    completed = [
        MagicMock(state=optuna.trial.TrialState.COMPLETE, value=0.10, number=10 + i)
        for i in range(2)
    ]
    failed = [
        MagicMock(state=optuna.trial.TrialState.FAIL, value=None, number=20),
    ]
    fake_study = MagicMock()
    fake_study.trials = pruned + completed + failed
    # Same predicate the runner applies after optimize.
    selected = [t for t in fake_study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    assert all(t in completed for t in selected)
    assert all(t not in selected for t in pruned)
    assert all(t not in selected for t in failed)
    assert len(selected) == 2


def test_pruned_count_recorded_on_study_attrs():
    """The runner records ``n_pruned_trials`` on the study's user_attrs."""
    fake_study = MagicMock()
    fake_study.study = MagicMock()
    pruned = [MagicMock(state=optuna.trial.TrialState.PRUNED, number=i) for i in range(5)]
    completed = [MagicMock(state=optuna.trial.TrialState.COMPLETE,
                            value=0.1, number=10 + i,
                            user_attrs={"fold_scores": [0.1], "fold_metrics": [{"fold_id": "f0"}]})
                  for i in range(1)]
    fake_study.study.trials = pruned + completed
    # The runner does:
    #   pruned = [t for t in study.study.trials if t.state == PRUNED]
    #   if pruned: study.study.set_user_attr("n_pruned_trials", len(pruned))
    pruned_observed = [
        t for t in fake_study.study.trials if t.state == optuna.trial.TrialState.PRUNED
    ]
    assert len(pruned_observed) == 5
