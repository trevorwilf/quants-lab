"""A trial with n_trades < min_trade_count gets a finite low-trade penalty.

Realism remediation Phase 9. A backtest with a handful of trades is
statistically uninformative — its net return could be luck. The objective
applies a low-trade-count penalty that ramps as ``n_trades`` falls toward 0.
The penalty MUST be finite (it must never be inf / NaN, which would corrupt the
study) and MUST shrink to 0 once the trade count clears the threshold.
"""
from __future__ import annotations

import math

from bowaka_v2_lab.optuna.objective import (
    DEFAULT_PENALTY_WEIGHTS,
    FoldResult,
    fold_penalties,
    fold_score,
)


def _fold(n_trades: int) -> FoldResult:
    return FoldResult(
        fold_id="f0", net_return=0.05, max_drawdown=0.0, turnover=0.0,
        concentration=0.0, n_trades=n_trades, worst_day_loss=0.0,
        quote_coverage=1.0, fill_rate=1.0,
    )


def test_low_trade_penalty_is_finite_for_a_sparse_fold() -> None:
    pen = fold_penalties(_fold(n_trades=2))
    assert math.isfinite(pen["low_trade_count"])
    assert pen["low_trade_count"] > 0.0


def test_zero_trade_fold_gets_the_maximum_penalty() -> None:
    pen = fold_penalties(_fold(n_trades=0))
    # ramps to the full weight at n_trades == 0.
    assert math.isclose(pen["low_trade_count"], DEFAULT_PENALTY_WEIGHTS.low_trade_count)


def test_penalty_vanishes_at_and_above_the_threshold() -> None:
    threshold = DEFAULT_PENALTY_WEIGHTS.min_trade_count
    assert fold_penalties(_fold(n_trades=threshold))["low_trade_count"] == 0.0
    assert fold_penalties(_fold(n_trades=threshold + 50))["low_trade_count"] == 0.0


def test_sparse_trial_scores_below_a_well_traded_one() -> None:
    """Same net return; the sparse-trade fold scores strictly lower."""
    threshold = DEFAULT_PENALTY_WEIGHTS.min_trade_count
    assert fold_score(_fold(n_trades=3)) < fold_score(_fold(n_trades=threshold))


def test_penalty_ramps_monotonically_as_trade_count_falls() -> None:
    p_many = fold_penalties(_fold(n_trades=20))["low_trade_count"]
    p_few = fold_penalties(_fold(n_trades=5))["low_trade_count"]
    p_none = fold_penalties(_fold(n_trades=0))["low_trade_count"]
    assert p_many < p_few < p_none
