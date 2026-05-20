"""Each penalty fires on a constructed bad-score fixture."""
from __future__ import annotations

from bowaka_v2_lab.optuna.objective import FoldResult, compute_objective, fold_score


def _good_fold(**overrides) -> FoldResult:
    base = dict(
        fold_id="f0", net_return=0.02, max_drawdown=0.01, turnover=0.0,
        concentration=0.0, n_trades=20, ambiguous_bar_count=0, missing_quote_count=0,
    )
    base.update(overrides)
    return FoldResult(**base)


def test_drawdown_penalty_fires() -> None:
    base = fold_score(_good_fold())
    worse = fold_score(_good_fold(max_drawdown=0.20))
    assert worse < base


def test_turnover_penalty_fires() -> None:
    base = fold_score(_good_fold())
    worse = fold_score(_good_fold(turnover=0.05))
    assert worse < base


def test_concentration_penalty_fires() -> None:
    base = fold_score(_good_fold())
    worse = fold_score(_good_fold(concentration=0.1))
    assert worse < base


def test_low_trade_count_penalty_fires() -> None:
    base = fold_score(_good_fold(n_trades=20))
    sparse = fold_score(_good_fold(n_trades=1))
    assert sparse < base


def test_ambiguous_penalty_fires() -> None:
    base = fold_score(_good_fold())
    worse = fold_score(_good_fold(ambiguous_bar_count=10))
    assert worse < base


def test_missing_quote_penalty_fires() -> None:
    base = fold_score(_good_fold())
    worse = fold_score(_good_fold(missing_quote_count=10))
    assert worse < base


def test_compute_objective_returns_median() -> None:
    folds = [_good_fold(net_return=0.0), _good_fold(net_return=0.04), _good_fold(net_return=0.06)]
    r = compute_objective(folds)
    assert r.median_fold_score > 0
