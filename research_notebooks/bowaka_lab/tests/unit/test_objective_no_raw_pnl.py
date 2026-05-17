"""Phase 9: objective uses median, not sum/mean, of raw PnL."""

from __future__ import annotations

import numpy as np

from bowaka_lab.optuna.objective import FoldStats, evaluate_objective


def test_single_outlier_does_not_dominate():
    # 14 returns at 1%, 1 return at 99% — sum/mean would inflate but median is 1%.
    returns = [0.01] * 14 + [0.99]
    folds = [FoldStats(test_returns=returns, trade_count=15) for _ in range(3)]
    score = evaluate_objective(folds=folds, min_total_trades=30)
    # Median of fold scores is 0.01; if the objective used mean, score would be ~0.075.
    assert 0.0 <= score <= 0.05


def test_median_preserves_uniform_returns():
    folds = [FoldStats(test_returns=[0.05] * 20, trade_count=20) for _ in range(3)]
    score = evaluate_objective(folds=folds, min_total_trades=30)
    assert abs(score - 0.05) < 1e-9
