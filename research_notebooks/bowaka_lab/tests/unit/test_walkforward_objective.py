"""Phase fidelity-8: walk-forward objective wiring + holdout reservation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.optuna.walkforward_objective import (
    WalkforwardObjectiveContext,
    build_walkforward_objective,
)


@dataclass
class _FakeTrade:
    pnl_pct: float


def _fake_result(returns):
    return SimpleNamespace(
        trades=[_FakeTrade(pnl_pct=r) for r in returns],
        max_drawdown_pct=0.0,
        turnover=0.0,
    )


def _base_cfg():
    return BowakaBacktestConfig.model_validate({
        "data": {"vendor": "alpaca", "feed": "iex",
                 "start_date": "2026-01-01", "end_date": "2026-05-15"},
    })


def test_walkforward_objective_runs_per_fold_and_returns_finite():
    """Three train/test folds + a holdout. Objective should run on
    folds[:-1] only."""
    cfg = _base_cfg()
    folds = [
        (date(2026, 1, 1),  date(2026, 1, 31), date(2026, 2, 1),  date(2026, 2, 28)),
        (date(2026, 1, 15), date(2026, 2, 15), date(2026, 2, 16), date(2026, 3, 15)),
        (date(2026, 2, 1),  date(2026, 3, 1),  date(2026, 3, 2),  date(2026, 4, 1)),
        (date(2026, 3, 1),  date(2026, 4, 1),  date(2026, 4, 2),  date(2026, 5, 1)),  # holdout
    ]
    calls: list[date] = []

    def runner(sub_cfg):
        calls.append(sub_cfg.data.end_date)
        return _fake_result([0.05, 0.02, -0.01, 0.10, 0.03, -0.02,
                              0.04, 0.06, -0.03, 0.07] * 3)
    ctx = WalkforwardObjectiveContext(
        base_cfg=cfg, folds=folds, backtest_runner=runner,
    )
    objective = build_walkforward_objective(ctx)

    # Build a trivial trial that returns provided suggestions.
    import optuna
    study = optuna.create_study(direction="maximize")
    trial = study.ask()
    score = objective(trial)
    assert isinstance(score, float)
    # CRITICAL: only folds[:-1] should be evaluated.
    assert len(calls) == 3
    holdout_end = folds[-1][3]
    assert holdout_end not in calls


def test_walkforward_objective_refuses_to_tune_on_holdout():
    """Build a context with TWO folds where folds[1] is the holdout.
    The runner must be called exactly once (on folds[0])."""
    cfg = _base_cfg()
    folds = [
        (date(2026, 1, 1), date(2026, 1, 31), date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 4, 1), date(2026, 4, 2), date(2026, 5, 1)),
    ]
    call_count = 0

    def runner(sub_cfg):
        nonlocal call_count
        call_count += 1
        return _fake_result([0.05] * 50)

    ctx = WalkforwardObjectiveContext(
        base_cfg=cfg, folds=folds, backtest_runner=runner,
    )
    objective = build_walkforward_objective(ctx)
    import optuna
    study = optuna.create_study(direction="maximize")
    objective(study.ask())
    assert call_count == 1


def test_walkforward_context_requires_at_least_two_folds():
    cfg = _base_cfg()
    ctx = WalkforwardObjectiveContext(
        base_cfg=cfg, folds=[(date(2026, 1, 1), date(2026, 1, 31),
                              date(2026, 2, 1), date(2026, 2, 28))],
        backtest_runner=lambda c: _fake_result([]),
    )
    with pytest.raises(ValueError, match="at least 2 folds"):
        build_walkforward_objective(ctx)


def test_walkforward_objective_requires_runner():
    cfg = _base_cfg()
    folds = [
        (date(2026, 1, 1), date(2026, 1, 31), date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 4, 1), date(2026, 4, 2), date(2026, 5, 1)),
    ]
    ctx = WalkforwardObjectiveContext(base_cfg=cfg, folds=folds, backtest_runner=None)
    objective = build_walkforward_objective(ctx)
    import optuna
    study = optuna.create_study(direction="maximize")
    with pytest.raises(NotImplementedError, match="requires ctx.backtest_runner"):
        objective(study.ask())
