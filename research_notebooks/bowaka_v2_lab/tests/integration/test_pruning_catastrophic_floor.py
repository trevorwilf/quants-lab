"""Conservative pruning fires only when running score breaches the floor.

Speedup report §6.2 / §11.2 Phase 7. With ``enabled: true`` and a
``catastrophic_floor=-0.5``, a trial whose first fold returns
``objective=-1.0`` IS pruned; a trial whose first fold is ``+0.1`` is
not.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import optuna
import pytest

from bowaka_v2_lab.optuna.objective import FoldResult


@pytest.fixture
def patched_run_validation_folds(monkeypatch):
    """Yield a setter that swaps in a fake ``_run_validation_folds`` that
    drives the prune callback deterministically over a fixed fold list.
    The patch persists for the entire test (no premature restore)."""
    import bowaka_v2_lab.optuna.walkforward_runner as wf_mod
    from bowaka_v2_lab.optuna.objective import compute_objective

    fold_holder: dict[str, list[FoldResult]] = {"folds": []}

    def fake(*args, **kwargs):
        cb = kwargs.get("prune_callback")
        out: list[FoldResult] = []
        for i, fr in enumerate(fold_holder["folds"]):
            out.append(fr)
            if cb is not None:
                cb(i, compute_objective(out).objective)
        return out

    monkeypatch.setattr(wf_mod, "_run_validation_folds", fake)

    def set_folds(fold_results: list[FoldResult]) -> None:
        fold_holder["folds"] = list(fold_results)

    return set_folds


def _make_obj(*, fold_results: list[FoldResult], pruning_cfg: dict,
              n_completed_in_study: int, set_folds):
    from bowaka_v2_lab.optuna.walkforward_runner import make_walkforward_objective

    plan = MagicMock()
    plan.splits = [MagicMock(val_start=None, val_end=None) for _ in fold_results]
    set_folds(fold_results)
    obj = make_walkforward_objective(
        {"optuna": {"pruning": pruning_cfg}}, plan,
        lake_root=None, feed="iex", symbols=["AAA"],
        paths=MagicMock(), holdout_guard=MagicMock(), log=MagicMock(),
    )

    trial = MagicMock()
    trial.number = 42
    trial.report = MagicMock()
    stub_completed = [
        MagicMock(state=optuna.trial.TrialState.COMPLETE)
        for _ in range(n_completed_in_study)
    ]
    trial.study = MagicMock()
    trial.study.get_trials = MagicMock(return_value=stub_completed)
    return obj, trial


def _bad_fold(i: int) -> FoldResult:
    return FoldResult(
        fold_id=f"f{i}", net_return=-1.0, max_drawdown=0.9,
        turnover=0.0, concentration=0.0, n_trades=0,
    )


def _good_fold(i: int) -> FoldResult:
    return FoldResult(
        fold_id=f"f{i}", net_return=0.1, max_drawdown=0.0,
        turnover=0.0, concentration=0.0, n_trades=50,
    )


def test_catastrophic_trial_is_pruned(patched_run_validation_folds):
    """First fold's running score below floor → TrialPruned."""
    obj, trial = _make_obj(
        fold_results=[_bad_fold(0), _bad_fold(1)],
        pruning_cfg={"enabled": True, "catastrophic_floor": -0.5,
                      "min_completed_trials_before_pruning": 0},
        n_completed_in_study=10,
        set_folds=patched_run_validation_folds,
    )
    with pytest.raises(optuna.TrialPruned):
        obj(trial)


def test_good_trial_is_not_pruned(patched_run_validation_folds):
    """First fold above floor → trial completes normally."""
    obj, trial = _make_obj(
        fold_results=[_good_fold(0), _good_fold(1)],
        pruning_cfg={"enabled": True, "catastrophic_floor": -0.5,
                      "min_completed_trials_before_pruning": 0},
        n_completed_in_study=10,
        set_folds=patched_run_validation_folds,
    )
    # No exception raised.
    obj(trial)
    # The trial DID report progress (good or bad).
    assert trial.report.call_count >= 1


def test_pruning_respects_startup_window(patched_run_validation_folds):
    """Even a catastrophic trial is NOT pruned before the startup window."""
    obj, trial = _make_obj(
        fold_results=[_bad_fold(0)],
        pruning_cfg={"enabled": True, "catastrophic_floor": -0.5,
                      "min_completed_trials_before_pruning": 30},
        n_completed_in_study=5,  # below the 30-trial floor
        set_folds=patched_run_validation_folds,
    )
    obj(trial)  # must NOT raise
    # trial.report not called either, because the startup window blocks all
    # pruning work for this trial.
    trial.report.assert_not_called()


def test_pruning_runs_after_startup_window(patched_run_validation_folds):
    """Once n_completed reaches the floor, pruning fires."""
    obj, trial = _make_obj(
        fold_results=[_bad_fold(0)],
        pruning_cfg={"enabled": True, "catastrophic_floor": -0.5,
                      "min_completed_trials_before_pruning": 30},
        n_completed_in_study=30,  # at the floor
        set_folds=patched_run_validation_folds,
    )
    with pytest.raises(optuna.TrialPruned):
        obj(trial)


def test_pruned_user_attrs_are_set(patched_run_validation_folds):
    """The objective records the pruning fold index + running score."""
    obj, trial = _make_obj(
        fold_results=[_bad_fold(0)],
        pruning_cfg={"enabled": True, "catastrophic_floor": -0.5,
                      "min_completed_trials_before_pruning": 0},
        n_completed_in_study=10,
        set_folds=patched_run_validation_folds,
    )
    with pytest.raises(optuna.TrialPruned):
        obj(trial)
    # ``set_user_attr`` called with the pruning markers.
    set_calls = {c.args[0] for c in trial.set_user_attr.call_args_list}
    assert "pruned" in set_calls
    assert "pruned_at_fold" in set_calls
    assert "pruned_running_score" in set_calls
