"""Phase 9: high fold-score variance penalized."""

from __future__ import annotations

from bowaka_lab.optuna.objective import FoldStats, evaluate_objective


def test_stable_folds_score_higher_than_unstable():
    # Same median fold score (0.04), but the unstable variant has high variance
    # — instability penalty should drag its score below the stable one.
    stable_folds = [
        FoldStats(test_returns=[0.04] * 15, trade_count=15),
        FoldStats(test_returns=[0.04] * 15, trade_count=15),
        FoldStats(test_returns=[0.04] * 15, trade_count=15),
    ]
    unstable_folds = [
        FoldStats(test_returns=[0.30] * 15, trade_count=15),
        FoldStats(test_returns=[-0.22] * 15, trade_count=15),
        FoldStats(test_returns=[0.04] * 15, trade_count=15),
    ]
    stable_score = evaluate_objective(folds=stable_folds, min_total_trades=30)
    unstable_score = evaluate_objective(folds=unstable_folds, min_total_trades=30)
    assert stable_score > unstable_score
