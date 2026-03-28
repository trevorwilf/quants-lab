"""Test that generate_report() renders all validation sections when data is provided."""
import pytest
from unittest.mock import MagicMock
from pmm_lab.report.report_md import generate_report, run_stop_ship_checks


def _make_mock_metrics():
    """Build a mock Metrics that supports :.4f formatting on all numeric fields."""
    from pmm_lab.metrics.metrics import Metrics
    return Metrics(
        pnl_pct=1.5,
        net_pnl_quote=15.0,
        max_drawdown_pct=5.0,
        sharpe=0.8,
        trade_count=20,
        fill_count=40,
        n_winning=12,
        n_losing=8,
        gross_win_quote=20.0,
        gross_loss_quote=5.0,
        profit_factor=1.3,
        total_fees_quote=0.5,
        maker_fees_quote=0.3,
        taker_fees_quote=0.2,
        fee_drag_pct=0.05,
        inventory_exposure_mean=0.01,
        inventory_exposure_max=0.05,
        expected_shortfall_5pct=-2.0,
        volume_zero_bar_count=0,
        volume_zero_bar_fraction=0.0,
        median_trade_pnl_quote=0.5,
        inventory_exposure_p95=0.04,
        open_trade_count=0,
    )


def _make_mock_objective():
    from pmm_lab.objective.objective import ObjectiveDecomposition
    return ObjectiveDecomposition(
        raw_score=0.75,
        pnl_component=0.5,
        sharpe_component=0.1,
        drawdown_component=-0.05,
        fee_drag_component=-0.02,
        inventory_component=-0.01,
        trade_count_penalty=0.0,
        es_component=-0.01,
        is_rejected=False,
        reject_reason=None,
    )


def _make_mock_recent_window():
    rw = MagicMock()
    rw.passed = True
    rw.reason = "all gates met"
    rw.metrics = _make_mock_metrics()
    rw.objective = _make_mock_objective()
    return rw


def test_report_contains_recent_window_objective_score():
    rw = _make_mock_recent_window()
    report = generate_report(
        study_name="test",
        dataset_summary={"connector": "test", "trading_pair": "BTC-USDT", "interval": "5m", "n_candles": 1000, "dataset_hash": "abc"},
        best_params={},
        best_metrics=_make_mock_metrics(),
        best_objective=_make_mock_objective(),
        recent_window_result=rw,
    )
    assert "Objective score" in report
    assert "0.75" in report


def test_report_contains_validation_manifest_when_all_provided():
    report = generate_report(
        study_name="test",
        dataset_summary={"connector": "test", "trading_pair": "BTC-USDT", "interval": "5m", "n_candles": 1000, "dataset_hash": "abc"},
        best_params={},
        best_metrics=_make_mock_metrics(),
        best_objective=_make_mock_objective(),
        dataset_audit=MagicMock(passed_strict=True),
        recent_window_result=_make_mock_recent_window(),
    )
    assert "Validation Execution Manifest" in report


def test_stop_ship_checks_all_kwargs_accepted():
    """Verify run_stop_ship_checks accepts all validation kwargs without error."""
    checks = run_stop_ship_checks(
        best_metrics=_make_mock_metrics(),
        best_objective=_make_mock_objective(),
        dataset_audit=MagicMock(passed_strict=True),
        validation_result=MagicMock(valid=True),
        holdout_report=MagicMock(exported_holdout_passed=True, exported_holdout_collapse=False),
        sensitivity_penalty=0.1,
        recent_window_result=MagicMock(passed=True),
        parity_result=MagicMock(passed=True),
        cluster_report=MagicMock(is_clustered=True),
        long_parity_result=MagicMock(passed=True),
    )
    assert isinstance(checks, dict)
    # All checks should pass with these inputs
    for name, passed in checks.items():
        if name in ("walkforward_robust", "walkforward_positive_majority", "stress_not_collapsed"):
            continue  # These require actual WF/stress data
        assert passed, f"Check '{name}' should PASS with valid mock inputs"
