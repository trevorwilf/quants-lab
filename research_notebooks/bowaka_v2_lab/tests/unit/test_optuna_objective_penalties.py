"""Each realistic-objective penalty fires on a constructed bad-score fixture.

Realism remediation Phase 9: the objective is rebuilt around real metrics. The
penalty set is drawdown / CVaR / turnover / concentration / low-trade-count /
missing-quote / missing-coverage / fill-rate, plus a cross-fold variance term.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.objective import (
    FoldResult,
    compute_objective,
    fold_penalties,
    fold_score,
)


def _good_fold(**overrides) -> FoldResult:
    base = dict(
        fold_id="f0", net_return=0.02, max_drawdown=0.01, turnover=0.0,
        concentration=0.0, n_trades=40, ambiguous_bar_count=0, missing_quote_count=0,
        worst_day_loss=0.0, quote_coverage=1.0, fill_rate=1.0,
    )
    base.update(overrides)
    return FoldResult(**base)


def test_drawdown_penalty_fires() -> None:
    assert fold_score(_good_fold(max_drawdown=0.20)) < fold_score(_good_fold())


def test_cvar_worst_day_penalty_fires() -> None:
    assert fold_score(_good_fold(worst_day_loss=0.10)) < fold_score(_good_fold())


def test_turnover_penalty_fires() -> None:
    assert fold_score(_good_fold(turnover=0.05)) < fold_score(_good_fold())


def test_concentration_penalty_fires() -> None:
    assert fold_score(_good_fold(concentration=0.1)) < fold_score(_good_fold())


def test_low_trade_count_penalty_fires() -> None:
    assert fold_score(_good_fold(n_trades=1)) < fold_score(_good_fold(n_trades=40))


def test_missing_quote_penalty_fires() -> None:
    assert fold_score(_good_fold(missing_quote_count=10)) < fold_score(_good_fold())


def test_missing_coverage_penalty_fires() -> None:
    assert fold_score(_good_fold(quote_coverage=0.5)) < fold_score(_good_fold())


def test_fill_rate_penalty_fires() -> None:
    assert fold_score(_good_fold(fill_rate=0.4)) < fold_score(_good_fold())


def test_penalty_breakdown_keys_present() -> None:
    pen = fold_penalties(_good_fold(max_drawdown=0.1, turnover=0.01))
    for key in ("drawdown", "cvar", "turnover", "concentration",
                "low_trade_count", "missing_quote", "missing_coverage", "fill_rate"):
        assert key in pen
        assert pen[key] >= 0.0


def test_compute_objective_returns_median() -> None:
    folds = [_good_fold(net_return=0.0), _good_fold(net_return=0.04),
             _good_fold(net_return=0.06)]
    r = compute_objective(folds)
    assert r.median_fold_score > 0


def test_fold_variance_penalty_lowers_objective() -> None:
    """A high fold-score spread is penalized below the median."""
    spread = [_good_fold(net_return=-0.10), _good_fold(net_return=0.02),
              _good_fold(net_return=0.20)]
    r = compute_objective(spread)
    assert r.objective < r.median_fold_score
    assert r.fold_variance > 0.0
