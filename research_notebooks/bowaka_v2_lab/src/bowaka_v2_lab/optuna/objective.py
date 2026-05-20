"""Walk-forward Optuna objective.

Per [Report §14.3]:
    objective       = median_fold_score - penalties
    fold_score      = net_return_after_conservative_costs
                       - 0.5 * max_drawdown_penalty
                       - turnover_penalty
                       - concentration_penalty
                       - low_trade_count_penalty
                       - ambiguity_penalty
                       - missing_quote_penalty

The IEX-feed flag also blocks promotion of an IEX-only study (per Phase 9 gate
this raises on attempted promotion in ``OptunaStudy.mark_promotion_eligible``).
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass
class FoldResult:
    fold_id: str
    net_return: float
    max_drawdown: float
    turnover: float
    concentration: float
    n_trades: int
    ambiguous_bar_count: int
    missing_quote_count: int


@dataclass
class ObjectiveResult:
    objective: float
    median_fold_score: float
    fold_scores: list[float]
    penalty_breakdown: dict[str, float]


def fold_score(fold: FoldResult, *, low_trade_count_threshold: int = 5) -> float:
    s = fold.net_return
    s -= 0.5 * fold.max_drawdown
    s -= fold.turnover
    s -= fold.concentration
    if fold.n_trades < low_trade_count_threshold:
        s -= 1.0 * (low_trade_count_threshold - fold.n_trades) / low_trade_count_threshold
    s -= 0.02 * fold.ambiguous_bar_count
    s -= 0.02 * fold.missing_quote_count
    return s


def compute_objective(folds: Iterable[FoldResult]) -> ObjectiveResult:
    fold_list = list(folds)
    if not fold_list:
        return ObjectiveResult(objective=0.0, median_fold_score=0.0, fold_scores=[], penalty_breakdown={})
    scores = [fold_score(f) for f in fold_list]
    med = float(statistics.median(scores))
    return ObjectiveResult(
        objective=med, median_fold_score=med, fold_scores=scores, penalty_breakdown={},
    )
