"""Phase 9: below-min-trades trials return a strongly negative score."""

from __future__ import annotations

from bowaka_lab.optuna.objective import FoldStats, evaluate_objective, is_degenerate


def test_zero_folds_is_degenerate():
    assert is_degenerate(evaluate_objective(folds=[]))


def test_below_min_total_trades_is_degenerate():
    folds = [FoldStats(test_returns=[0.02, 0.03], trade_count=2)]
    score = evaluate_objective(folds=folds, min_total_trades=30)
    assert is_degenerate(score)


def test_below_min_per_fold_is_degenerate():
    folds = [FoldStats(test_returns=[0.02], trade_count=1), FoldStats(test_returns=[0.02] * 30, trade_count=30)]
    score = evaluate_objective(folds=folds, min_total_trades=10, min_trades_per_fold=3)
    assert is_degenerate(score)


def test_meeting_min_trades_returns_non_degenerate():
    folds = [
        FoldStats(test_returns=[0.02] * 15, trade_count=15),
        FoldStats(test_returns=[0.03] * 20, trade_count=20),
    ]
    score = evaluate_objective(folds=folds, min_total_trades=30, min_trades_per_fold=3)
    assert not is_degenerate(score)
