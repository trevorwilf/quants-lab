"""Objective unit consistency: every term is in DECIMAL returns (audit §P1-008).

Realism remediation 2 Phase 8. ``MetricUnits`` enforces that every per-fold
metric is in decimal returns (``0.03`` for 3%) — not percent (``3.0`` for 3%).
Mixed units silently swap which penalty dominates the objective. The toy fold
in :func:`test_known_toy_fold_produces_expected_objective` has hand-computed
penalties: a change in any term's units (or weight) breaks the test.
"""
from __future__ import annotations

import math

import pytest

from bowaka_v2_lab.optuna.objective import (
    DEFAULT_PENALTY_WEIGHTS,
    FoldResult,
    MetricUnits,
    MetricUnitsError,
    compute_objective,
    fold_penalties,
    fold_score,
    validate_metric_units,
)


# --------------------------------------------------------------------------
# MetricUnits — per-field range validation.
# --------------------------------------------------------------------------
def test_metric_units_rejects_percent_units_for_net_return() -> None:
    """net_return=3.0 (i.e. 3.0 in PERCENT units, 300% in decimal) is rejected."""
    with pytest.raises(MetricUnitsError, match="net_return"):
        MetricUnits.build(
            net_return=3.0,  # 3.0 looks like 300% in decimal — clearly wrong
            max_drawdown=0.05, worst_day_loss=0.02,
            quote_coverage=0.95, fill_rate=0.9,
        )


def test_metric_units_rejects_percent_units_for_drawdown() -> None:
    """max_drawdown=8.0 (a percent input, meant 0.08) is rejected."""
    with pytest.raises(MetricUnitsError):
        MetricUnits.build(
            net_return=0.01, max_drawdown=8.0,  # plainly out of [0, 1]
            worst_day_loss=0.02, quote_coverage=0.95, fill_rate=0.9,
        )


def test_metric_units_rejects_percent_units_for_quote_coverage() -> None:
    """quote_coverage=95.0 (a percent input, meant 0.95) is rejected."""
    with pytest.raises(MetricUnitsError):
        MetricUnits.build(
            net_return=0.01, max_drawdown=0.05, worst_day_loss=0.02,
            quote_coverage=95.0, fill_rate=0.9,
        )


def test_metric_units_admits_clean_decimal_inputs() -> None:
    """Plain decimal inputs pass the validator."""
    # No raise.
    MetricUnits.build(
        net_return=0.03, max_drawdown=0.05, worst_day_loss=0.02,
        quote_coverage=0.95, fill_rate=0.92, turnover=0.5,
        concentration=0.3, n_trades=50, missing_quote_count=2,
    )


def test_metric_units_admits_negative_net_return() -> None:
    """A loss (negative decimal) is admissible — it's just a bad fold, not a unit bug."""
    MetricUnits.build(
        net_return=-0.05, max_drawdown=0.10, worst_day_loss=0.04,
        quote_coverage=0.95, fill_rate=0.92,
    )


def test_validate_metric_units_on_fold_result() -> None:
    """validate_metric_units accepts a clean FoldResult unchanged."""
    fold = FoldResult(
        fold_id="t",
        net_return=0.02, max_drawdown=0.04, turnover=0.1, concentration=0.2,
        n_trades=40, worst_day_loss=0.01, quote_coverage=0.98, fill_rate=0.95,
    )
    assert validate_metric_units(fold) is fold


def test_validate_metric_units_raises_on_percent_input() -> None:
    """validate_metric_units on a percent-units FoldResult raises."""
    fold = FoldResult(
        fold_id="t",
        net_return=3.0,  # PERCENT — should have been 0.03
        max_drawdown=0.04, turnover=0.1, concentration=0.2,
        n_trades=40, worst_day_loss=0.01, quote_coverage=0.98, fill_rate=0.95,
    )
    with pytest.raises(MetricUnitsError, match="net_return"):
        validate_metric_units(fold)


# --------------------------------------------------------------------------
# Hand-computed toy fold — exact expected objective.
# --------------------------------------------------------------------------
def test_known_toy_fold_produces_expected_objective() -> None:
    """A toy fold with hand-computed penalties yields the exact expected objective.

    Inputs (audit §P1-008 spec):
      net_return=0.03, max_drawdown=0.05, worst_day_loss=0.02, fill_rate=0.85,
      quote_coverage=1.0, turnover=0.0, concentration=0.0, n_trades=50.

    Default weights:
      drawdown=0.5, cvar=0.5, fill_rate=0.5,
      turnover=1.0, concentration=1.0, missing_quote=0.02, missing_coverage=1.0,
      low_trade_count=1.0 (ramp from 0 at >=30 trades, so 0 here at n_trades=50),
      fold_variance=0.5.

    Hand-computed fold penalties:
      drawdown:        0.5 * 0.05 = 0.025
      cvar:            0.5 * 0.02 = 0.010
      turnover:        1.0 * 0.0  = 0.0
      concentration:   1.0 * 0.0  = 0.0
      low_trade_count: 0.0 (n_trades=50 >= 30)
      missing_quote:   0.02 * 0   = 0.0
      missing_coverage:1.0 * 0.0  = 0.0
      fill_rate:       0.5 * (1 - 0.85) = 0.075
      sum             = 0.110
      fold_score      = 0.03 - 0.110 = -0.08

    Single fold → variance=0 → objective = median - 0 = -0.08.
    """
    fold = FoldResult(
        fold_id="toy",
        net_return=0.03, max_drawdown=0.05, turnover=0.0, concentration=0.0,
        n_trades=50, worst_day_loss=0.02, quote_coverage=1.0, fill_rate=0.85,
    )
    penalties = fold_penalties(fold)
    assert penalties["drawdown"] == pytest.approx(0.025, abs=1e-12)
    assert penalties["cvar"] == pytest.approx(0.010, abs=1e-12)
    assert penalties["fill_rate"] == pytest.approx(0.075, abs=1e-12)
    assert penalties["low_trade_count"] == pytest.approx(0.0, abs=1e-12)
    assert penalties["missing_coverage"] == pytest.approx(0.0, abs=1e-12)

    expected_fold_score = 0.03 - (0.025 + 0.010 + 0.075)
    assert fold_score(fold) == pytest.approx(expected_fold_score, abs=1e-12)

    result = compute_objective([fold])
    assert result.objective == pytest.approx(expected_fold_score, abs=1e-12)
    assert result.median_fold_score == pytest.approx(expected_fold_score, abs=1e-12)
    assert result.fold_variance == 0.0  # one fold, no cross-fold variance


def test_compute_objective_validates_units_by_default() -> None:
    """compute_objective raises MetricUnitsError on a percent-units fold."""
    bad = FoldResult(
        fold_id="bad",
        net_return=3.0,  # PERCENT
        max_drawdown=5.0,  # PERCENT
        turnover=0.0, concentration=0.0, n_trades=50,
        worst_day_loss=0.02, quote_coverage=1.0, fill_rate=0.85,
    )
    with pytest.raises(MetricUnitsError):
        compute_objective([bad])


def test_compute_objective_validate_units_false_skips_check() -> None:
    """validate_units=False is the escape hatch for fixture-driven edge tests."""
    # 5.0 drawdown is in percent (50000% in decimal); without unit validation
    # the math still proceeds and the test asserts the numbers compose.
    # (Real production code MUST pass validate_units=True.)
    fold = FoldResult(
        fold_id="edge",
        net_return=0.5,  # 50% — at the boundary of admissible
        max_drawdown=0.5, turnover=0.0, concentration=0.0, n_trades=100,
        worst_day_loss=0.2, quote_coverage=1.0, fill_rate=0.9,
    )
    result = compute_objective([fold], validate_units=False)
    assert math.isfinite(result.objective)
