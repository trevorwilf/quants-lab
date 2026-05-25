"""Pruning is off by default; trials never raise ``TrialPruned``.

Speedup report §6.2 / §11.2 Phase 7. The default config carries no
``optuna.pruning`` block; the objective must never invoke
``trial.report`` / raise ``TrialPruned`` in that case.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bowaka_v2_lab.optuna.objective import FoldResult


@pytest.fixture
def patched_run_validation_folds(monkeypatch):
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


def _make_obj(base_cfg: dict, *, fold_results: list[FoldResult], set_folds):
    from bowaka_v2_lab.optuna.walkforward_runner import make_walkforward_objective

    plan = MagicMock()
    plan.splits = [MagicMock(val_start=None, val_end=None) for _ in fold_results]
    set_folds(fold_results)
    return make_walkforward_objective(
        base_cfg, plan, lake_root=None, feed="iex", symbols=["AAA"],
        paths=MagicMock(), holdout_guard=MagicMock(), log=MagicMock(),
    )


def test_default_no_pruning_completes_normally(patched_run_validation_folds):
    """Without an ``optuna.pruning`` block the trial never reports/prunes."""
    trial = MagicMock()
    trial.number = 5
    trial.study = MagicMock()
    trial.study.get_trials = MagicMock(return_value=[])
    trial.report = MagicMock()

    obj = _make_obj({"optuna": {}}, fold_results=[
        FoldResult(
            fold_id=f"f{i}", net_return=-1.0, max_drawdown=0.5,
            turnover=0.0, concentration=0.0, n_trades=0,
        ) for i in range(3)
    ], set_folds=patched_run_validation_folds)
    # No TrialPruned raised even with very negative folds.
    obj(trial)
    # trial.report not called when pruning is disabled.
    trial.report.assert_not_called()


def test_disabled_pruning_block_still_no_op(patched_run_validation_folds):
    """``enabled: false`` keeps the no-op path."""
    trial = MagicMock()
    trial.number = 5
    trial.study = MagicMock()
    trial.study.get_trials = MagicMock(return_value=[])
    trial.report = MagicMock()
    obj = _make_obj(
        {"optuna": {"pruning": {"enabled": False,
                                  "catastrophic_floor": 0.5,
                                  "min_completed_trials_before_pruning": 0}}},
        fold_results=[
            FoldResult(
                fold_id=f"f{i}", net_return=-1.0, max_drawdown=0.5,
                turnover=0.0, concentration=0.0, n_trades=0,
            ) for i in range(3)
        ],
        set_folds=patched_run_validation_folds,
    )
    obj(trial)
    trial.report.assert_not_called()
