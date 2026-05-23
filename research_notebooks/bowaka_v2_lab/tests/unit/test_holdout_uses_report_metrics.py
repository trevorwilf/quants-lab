"""Holdout scoring uses the same substantive metrics as validation folds.

Realism remediation 2 Phase 8 (audit §P1-004). Pre-Phase-8, the holdout fold
called ``_run_fold_backtest`` without ``return_report=True`` and hard-coded
``worst_day_loss=0.0`` — so the holdout's drawdown / worst-day metrics were
materially weaker than the validation folds. Phase 8 routes holdout through
``fold_result_from_report`` (the validation path).
"""
from __future__ import annotations

import inspect

import pytest


def test_score_final_holdout_calls_run_fold_backtest_with_return_report_true() -> None:
    """The holdout source code passes return_report=True to _run_fold_backtest.

    The most reliable way to assert "holdout uses the report-based path" is to
    inspect the source: this avoids brittle mocking that depends on internal
    import paths and module reload behavior.
    """
    from bowaka_v2_lab.optuna.holdout import score_final_holdout

    src = inspect.getsource(score_final_holdout)
    # The Phase-8 holdout MUST pass return_report=True (audit §P1-004).
    assert "return_report=True" in src, (
        "score_final_holdout no longer passes return_report=True — "
        "holdout would silently downgrade to summary-only metrics "
        "(audit §P1-004)"
    )
    # It MUST build the holdout FoldResult via fold_result_from_report.
    assert "fold_result_from_report" in src, (
        "score_final_holdout no longer routes through fold_result_from_report — "
        "validation folds use it; the holdout MUST do the same (audit §P1-004)"
    )
    # It MUST fail closed when the report is missing / corrupt.
    assert "report.json missing" in src or "report" in src.lower(), (
        "score_final_holdout no longer fails closed on a missing report; "
        "the holdout is the ONLY honest out-of-sample number (audit §P1-004)"
    )


def test_holdout_fold_result_carries_daily_mtm_drawdown_and_worst_day() -> None:
    """Building a FoldResult from a report.json populates mtm_drawdown + worst_day_loss."""
    from bowaka_v2_lab.optuna.objective import fold_result_from_report

    report = {
        "portfolio_and_risk": {
            "daily_equity": [
                {"bankroll": 100_000.0},
                {"bankroll": 102_000.0},
                {"bankroll":  98_000.0},  # daily MTM drawdown ~3.92%, day -3.92%
                {"bankroll": 101_000.0},
            ],
            "metrics": [{"metric": "net_return_pct", "value": 0.01}],
        },
        "trade_performance": {"metrics": [{"metric": "n_trades", "value": 50}]},
        "execution_quality": {
            "metrics": [
                {"metric": "fill_rate", "value": 0.92},
                {"metric": "historical_quote_coverage_pct", "value": 96.5},
                {"metric": "missing_quote_count", "value": 3},
            ],
        },
    }
    summary = {
        "turnover": 0.5, "concentration": 0.2,
        "ambiguous_bar_count": 0,
    }
    fold = fold_result_from_report("holdout_2024-12-01", report, summary)
    # Daily MTM drawdown computed from the equity curve (NOT zero / hard-coded).
    assert fold.max_drawdown > 0.0
    # Worst-day loss from the daily curve (NOT zero / hard-coded).
    assert fold.worst_day_loss > 0.0
    # The richer execution-quality metrics are propagated.
    assert fold.fill_rate == pytest.approx(0.92)
    assert fold.quote_coverage == pytest.approx(0.965)
    assert fold.missing_quote_count == 3


def test_holdout_fail_closed_on_missing_report_message_is_explicit() -> None:
    """The fail-closed RuntimeError on a missing report names the holdout window."""
    from bowaka_v2_lab.optuna.holdout import score_final_holdout

    src = inspect.getsource(score_final_holdout)
    # The fail-closed branch references audit §P1-004 in its docstring / comment.
    assert "P1-004" in src or "audit" in src.lower(), (
        "score_final_holdout's fail-closed branch lost its audit reference"
    )
