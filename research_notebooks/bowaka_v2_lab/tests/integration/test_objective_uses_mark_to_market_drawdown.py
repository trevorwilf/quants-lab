"""The fold score uses the DAILY mark-to-market drawdown, not closed-trade DD.

Realism remediation Phase 9, audit §14.3. ``summary.max_drawdown_pct`` is built
from the closed-trade equity curve and can be shallow while the daily
mark-to-market equity curve sits in a deep unrealized hole. The objective MUST
penalize the daily curve.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.objective import (
    fold_result_from_report,
    fold_score,
    mark_to_market_drawdown,
)


def _report(daily_bankroll: list[float], **portfolio_metrics) -> dict:
    """A minimal Phase-8 report.json with a daily-equity curve."""
    metrics = {"net_return_pct": 0.0, **portfolio_metrics}
    return {
        "portfolio_and_risk": {
            "metrics": [{"metric": k, "value": v} for k, v in metrics.items()],
            "daily_equity": [
                {"session_date": f"2024-01-{i + 1:02d}", "bankroll": v}
                for i, v in enumerate(daily_bankroll)
            ],
        },
        "trade_performance": {"metrics": [{"metric": "n_trades", "value": 40}]},
        "execution_quality": {"metrics": [
            {"metric": "fill_rate", "value": 1.0},
            {"metric": "historical_quote_coverage_pct", "value": 100.0},
        ]},
    }


def test_mark_to_market_drawdown_uses_the_daily_curve() -> None:
    # peak 110_000 -> trough 88_000 = 20% drawdown.
    curve = [100_000, 110_000, 88_000, 95_000]
    assert abs(mark_to_market_drawdown(curve) - 0.20) < 1e-9


def test_mark_to_market_drawdown_zero_for_monotone_curve() -> None:
    assert mark_to_market_drawdown([100_000, 101_000, 102_000]) == 0.0


def test_fold_result_drawdown_comes_from_daily_equity_not_summary() -> None:
    """report.json daily curve has a 20% DD; summary claims a tiny closed-trade DD."""
    report = _report([100_000, 110_000, 88_000, 95_000])
    summary = {"max_drawdown_pct": 0.01, "net_return_pct": 0.0}  # closed-trade — ignored
    fold = fold_result_from_report("f0", report, summary)
    # The fold's drawdown is the DAILY mark-to-market 20%, NOT the 1% closed-trade.
    assert abs(fold.max_drawdown - 0.20) < 1e-9
    assert fold.max_drawdown != 0.01


def test_deep_daily_drawdown_scores_below_shallow_one() -> None:
    """Two folds, identical net return; the deeper DAILY drawdown scores lower."""
    shallow = fold_result_from_report("shallow", _report([100_000, 101_000, 100_500]))
    deep = fold_result_from_report("deep", _report([100_000, 130_000, 90_000]))
    assert fold_score(deep) < fold_score(shallow)
