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


# ---------------------------------------------------------------------------
# Notebook smoke objective
# ---------------------------------------------------------------------------


def smoke_objective_from_candidates(candidates_df) -> Any:
    """Bind a small smoke-grade Optuna objective to a cached candidates table.

    Returns a callable ``objective(trial) -> float`` that can be passed to
    :meth:`optuna.study.Study.optimize`. The objective is intentionally cheap
    (no backtester replay) — it only filters the candidates table by the
    suggested gate thresholds and rewards median ``signal_strength`` weighted
    by candidate-count saturation up to 5,000.

    Production walk-forward objectives live in :func:`evaluate_objective`
    and run via the task runner; this helper is for sanity-checking the
    search space inside ``notebooks/10_optuna_walkforward.ipynb``.
    """
    import pandas as _pd

    from bowaka_lab.optuna.search_space import suggest_params

    def objective(trial) -> float:
        params = suggest_params(trial)
        if candidates_df is None or candidates_df.empty:
            return -1.0
        rvol_col = candidates_df.get("rvol", _pd.Series([0.0] * len(candidates_df)))
        atr_col = candidates_df.get("atr_pct", _pd.Series([0.0] * len(candidates_df)))
        rng_col = candidates_df.get("range_expansion", _pd.Series([0.0] * len(candidates_df)))
        mask = (
            (rvol_col.fillna(0) >= float(params.get("rvol_min", 0.0)))
            & (atr_col.fillna(0) >= float(params.get("atr_pct_min", 0.0)))
            & (rng_col.fillna(0) >= float(params.get("range_expansion_min", 0.0)))
        )
        eligible = candidates_df[mask]
        n = int(eligible.shape[0])
        if n == 0:
            return -1.0
        strength = eligible.get("signal_strength", _pd.Series([0.0])).fillna(0)
        median_strength = float(strength.median())
        return median_strength * min(n / 5_000.0, 1.0)

    return objective
