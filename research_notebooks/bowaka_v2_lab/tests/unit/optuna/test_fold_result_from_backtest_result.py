"""``fold_result_from_backtest_result`` mirrors ``fold_result_from_report``.

Speedup report §5.1 / §11.2 Phase 1. The objective-minimal path consumes the
in-memory :class:`BacktestResult`; this test pins the converter so it produces
the same :class:`FoldResult` as the legacy ``report.json``-reading path for an
equivalent run.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from bowaka_v2_lab.optuna.objective import (
    FoldResult,
    fold_result_from_backtest_result,
    fold_result_from_report,
)


def _fake_backtest_result(
    *,
    summary: dict,
    daily_equity: list[dict],
    execution_quality_rows: list[dict],
) -> SimpleNamespace:
    return SimpleNamespace(
        summary=summary,
        daily_equity=daily_equity,
        execution_quality_rows=execution_quality_rows,
    )


def _equivalent_report(
    summary: dict, daily_equity: list[dict], eq_rows: list[dict]
) -> dict:
    return {
        "portfolio_and_risk": {
            "metrics": [
                {"metric": "net_return_pct", "value": summary.get("net_return_pct", 0.0)},
            ],
            "daily_equity": daily_equity,
        },
        "trade_performance": {
            "metrics": [{"metric": "n_trades", "value": summary.get("n_trades", 0)}],
        },
        "execution_quality": {"metrics": eq_rows},
    }


def test_converter_matches_report_path_on_trivial_run():
    summary = {
        "net_return_pct": 0.025, "n_trades": 7, "turnover": 0.4,
        "concentration": 0.1, "ambiguous_bar_count": 0,
        "missing_quote_count": 0, "fill_rate": 0.95,
        "historical_quote_coverage_pct": 99.5,
    }
    daily = [
        {"session_date": "2024-01-02", "bankroll": 100000.0},
        {"session_date": "2024-01-03", "bankroll": 100500.0},
        {"session_date": "2024-01-04", "bankroll": 99700.0},
        {"session_date": "2024-01-05", "bankroll": 102000.0},
    ]
    eq = [
        {"metric": "fill_rate", "value": 0.95},
        {"metric": "historical_quote_coverage_pct", "value": 99.5},
        {"metric": "missing_quote_count", "value": 0},
    ]

    bt = _fake_backtest_result(summary=summary, daily_equity=daily,
                                execution_quality_rows=eq)
    rpt = _equivalent_report(summary, daily, eq)

    fr_bt = fold_result_from_backtest_result("f0", bt)
    fr_rp = fold_result_from_report("f0", rpt, summary)

    assert fr_bt.fold_id == fr_rp.fold_id == "f0"
    assert fr_bt.net_return == pytest.approx(fr_rp.net_return)
    assert fr_bt.max_drawdown == pytest.approx(fr_rp.max_drawdown)
    assert fr_bt.worst_day_loss == pytest.approx(fr_rp.worst_day_loss)
    assert fr_bt.n_trades == fr_rp.n_trades
    assert fr_bt.quote_coverage == pytest.approx(fr_rp.quote_coverage)
    assert fr_bt.fill_rate == pytest.approx(fr_rp.fill_rate)
    assert fr_bt.missing_quote_count == fr_rp.missing_quote_count


def test_converter_extracts_drawdown_from_daily_equity_not_summary():
    """Confirms the converter ignores ``summary.max_drawdown_pct``."""
    # Summary claims 0 drawdown; daily equity actually shows a 5% drop.
    summary = {
        "net_return_pct": 0.0, "n_trades": 1, "max_drawdown_pct": 0.0,
        "fill_rate": 1.0, "historical_quote_coverage_pct": 100.0,
    }
    daily = [
        {"session_date": "2024-01-02", "bankroll": 100.0},
        {"session_date": "2024-01-03", "bankroll": 95.0},
    ]
    bt = _fake_backtest_result(summary=summary, daily_equity=daily, execution_quality_rows=[])
    fr = fold_result_from_backtest_result("f0", bt)
    assert fr.max_drawdown == pytest.approx(0.05)


def test_converter_handles_empty_daily_equity():
    summary = {"net_return_pct": 0.0, "n_trades": 0, "fill_rate": 1.0,
               "historical_quote_coverage_pct": 100.0}
    bt = _fake_backtest_result(summary=summary, daily_equity=[], execution_quality_rows=[])
    fr = fold_result_from_backtest_result("f_empty", bt)
    assert fr.max_drawdown == 0.0
    assert fr.worst_day_loss == 0.0
    assert fr.n_trades == 0


def test_converter_prefers_eq_rows_over_summary_for_overlapping_keys():
    """fill_rate / coverage / missing_quote come from execution_quality_rows
    when present, summary as fallback — same lookup order as the legacy path."""
    summary = {"net_return_pct": 0.01, "n_trades": 1, "fill_rate": 0.10,
               "historical_quote_coverage_pct": 50.0, "missing_quote_count": 99}
    eq = [
        {"metric": "fill_rate", "value": 0.99},
        {"metric": "historical_quote_coverage_pct", "value": 99.0},
        {"metric": "missing_quote_count", "value": 1},
    ]
    bt = _fake_backtest_result(summary=summary, daily_equity=[
        {"session_date": "2024-01-02", "bankroll": 100.0},
        {"session_date": "2024-01-03", "bankroll": 101.0},
    ], execution_quality_rows=eq)
    fr = fold_result_from_backtest_result("f_eq", bt)
    assert fr.fill_rate == pytest.approx(0.99)
    assert fr.quote_coverage == pytest.approx(0.99)
    assert fr.missing_quote_count == 1


def test_converter_returns_fold_result_type():
    summary = {"net_return_pct": 0.0, "n_trades": 0, "fill_rate": 1.0,
               "historical_quote_coverage_pct": 100.0}
    bt = _fake_backtest_result(summary=summary, daily_equity=[], execution_quality_rows=[])
    assert isinstance(fold_result_from_backtest_result("f0", bt), FoldResult)
