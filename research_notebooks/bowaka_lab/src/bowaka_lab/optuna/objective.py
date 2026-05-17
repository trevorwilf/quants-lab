"""Objective function for Optuna: median fold score minus weighted penalties.

Penalties:

- low_trade_count_penalty: trial returns a strongly negative score when total
  trades < min_total_trades_gate OR any test fold has < min_trades_per_fold.
- instability_penalty: large fold-score variance is penalized.
- drawdown_penalty: max drawdown deeper than threshold is penalized.
- turnover_penalty: outliers in turnover are penalized.
- tail_loss_penalty: max single-trade loss beyond threshold is penalized.

The total uses median, not sum/mean, of raw PnL to avoid single-trade dominance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


_DEGENERATE_SCORE = -1.0e6


@dataclass
class ObjectiveWeights:
    drawdown: float = 0.50
    turnover: float = 0.25
    instability: float = 0.50
    tail_loss: float = 0.25


@dataclass
class FoldStats:
    test_returns: Sequence[float]
    trade_count: int
    max_drawdown_pct: float = 0.0
    turnover: float = 0.0
    worst_trade_pct: float = 0.0


def evaluate_objective(
    *,
    folds: Sequence[FoldStats],
    weights: ObjectiveWeights | None = None,
    min_total_trades: int = 30,
    min_trades_per_fold: int = 3,
    drawdown_threshold: float = 0.10,
    tail_loss_threshold: float = -0.20,
) -> float:
    """Compute the Bowaka objective from a list of fold statistics."""
    if not folds:
        return _DEGENERATE_SCORE

    weights = weights or ObjectiveWeights()
    total_trades = sum(f.trade_count for f in folds)
    if total_trades < min_total_trades:
        return _DEGENERATE_SCORE
    if any(f.trade_count < min_trades_per_fold for f in folds):
        return _DEGENERATE_SCORE

    fold_scores = []
    for f in folds:
        if not f.test_returns:
            return _DEGENERATE_SCORE
        fold_scores.append(float(np.median(list(f.test_returns))))

    median_fold_score = float(np.median(fold_scores))
    variance = float(np.var(fold_scores))
    drawdown_penalty = max(0.0, max(f.max_drawdown_pct for f in folds) - drawdown_threshold) ** 2
    turnover_penalty = max(0.0, max(f.turnover for f in folds) - 5.0)
    tail_loss_penalty = max(0.0, abs(min(f.worst_trade_pct for f in folds)) - abs(tail_loss_threshold))
    instability_penalty = variance

    return (
        median_fold_score
        - weights.drawdown * drawdown_penalty
        - weights.turnover * turnover_penalty
        - weights.instability * instability_penalty
        - weights.tail_loss * tail_loss_penalty
    )


def is_degenerate(score: float) -> bool:
    return score <= _DEGENERATE_SCORE / 2.0
