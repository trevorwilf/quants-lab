"""Walk-forward runner that executes a config across the splits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from bowaka_lab.research.splits import WalkForwardPlan, WalkForwardSplit


@dataclass
class FoldResult:
    fold: int
    train_score: float | None
    test_score: float
    test_trade_count: int
    diagnostics: dict


@dataclass
class WalkForwardSummary:
    fold_results: list[FoldResult]
    aggregate_score: float
    test_trade_count: int
    score_variance: float


def run_walkforward(
    *,
    plan: WalkForwardPlan,
    evaluate_fn: Callable[[WalkForwardSplit], FoldResult],
) -> WalkForwardSummary:
    """Run ``evaluate_fn`` over each split and aggregate results."""
    results = [evaluate_fn(s) for s in plan.splits]
    if not results:
        return WalkForwardSummary(fold_results=[], aggregate_score=0.0, test_trade_count=0, score_variance=0.0)
    scores = pd.Series([r.test_score for r in results], dtype=float)
    trades = sum(r.test_trade_count for r in results)
    return WalkForwardSummary(
        fold_results=results,
        aggregate_score=float(scores.median()),
        test_trade_count=int(trades),
        score_variance=float(scores.var(ddof=0)),
    )
