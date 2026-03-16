"""Tests for pmm_lab.report.report_md — report generation and stop-ship checks."""

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass

from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition, REJECT_SCORE
from pmm_lab.objective.holdout import HoldoutReport
from pmm_lab.features.regime import RegimeClassification
from pmm_lab.config.params import AuditResult
from pmm_lab.report.report_md import generate_report, run_stop_ship_checks


def _make_metrics(**overrides) -> Metrics:
    defaults = dict(
        pnl_pct=5.0, net_pnl_quote=5.0, max_drawdown_pct=10.0, sharpe=1.5,
        trade_count=20, fill_count=40, n_winning=12, n_losing=8,
        gross_win_quote=30.0, gross_loss_quote=15.0, profit_factor=2.0,
        total_fees_quote=1.0, maker_fees_quote=0.5, taker_fees_quote=0.5,
        fee_drag_pct=1.0, inventory_exposure_mean=0.05, inventory_exposure_max=0.1,
        expected_shortfall_5pct=-0.001, volume_zero_bar_count=0, volume_zero_bar_fraction=0.0,
        median_trade_pnl_quote=0.5, inventory_exposure_p95=0.08,
    )
    defaults.update(overrides)
    return Metrics(**defaults)


def _make_objective(**overrides) -> ObjectiveDecomposition:
    defaults = dict(
        raw_score=5.0, pnl_component=3.0, sharpe_component=1.0,
        drawdown_component=0.5, fee_drag_component=0.2,
        inventory_component=0.1, trade_count_penalty=0.0,
        es_component=0.0, is_rejected=False,
    )
    defaults.update(overrides)
    return ObjectiveDecomposition(**defaults)


def _make_holdout_report(passed=True, collapse=False):
    regime = RegimeClassification(
        volatility="low_vol", trend="ranging", label="low_vol_ranging",
        natr_mean=0.001, natr_median=0.001,
        efficiency_ratio=0.1, total_return_pct=0.5,
    )
    return HoldoutReport(
        holdout_bars=100,
        holdout_start_timestamp=1756833000,
        holdout_end_timestamp=1756863000,
        regime=regime,
        candidates=[],
        best_holdout_rank=0,
        best_holdout_score=3.0 if passed else -1.0,
        dev_vs_holdout_collapse=collapse,
        passed=passed,
    )


def _make_walkforward_result(n_folds=3, all_positive=True):
    """Create a mock WalkForwardResult."""
    mock = MagicMock()
    folds = []
    for i in range(n_folds):
        fold = MagicMock()
        fold.fold_index = i
        fold.test_metrics = _make_metrics(pnl_pct=5.0 if all_positive else -5.0)
        fold.test_objective = _make_objective(is_rejected=False)
        folds.append(fold)
    mock.folds = folds
    mock.aggregate_score = 4.0
    return mock


def _make_stress_report(worst_score=-2.0):
    mock = MagicMock()
    mock.worst_score = worst_score
    mock.worst_scenario = "high_fees"
    mock.scenario_results = []
    return mock


@dataclass
class _FakeValidation:
    valid: bool = True


def _make_audit_result(passed_strict=True):
    return AuditResult(
        total_rows=500, first_timestamp=1756833000, last_timestamp=1756983000,
        expected_rows=500, missing_rows=0, duplicate_count=0,
        null_counts={}, ohlc_violations=0, ohlc_violation_details={},
        volume_zero_count=0, volume_zero_fraction=0.0,
        forward_fill_count=0, forward_fill_fraction=0.0,
        dataset_hash="abc123", interval_seconds=300,
        gap_histogram={}, longest_gap_seconds=300,
        passed_strict=passed_strict, failure_reasons=[],
    )


# ── Report generation tests ──────────────────────────────────


class TestGenerateReportBasic:
    def test_generate_report_basic(self):
        report = generate_report(
            study_name="test_study",
            dataset_summary={"bars": 500, "pair": "BTC-USDT"},
            best_params={"buy_spread_base": 1.0},
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
        )
        assert "# PMM Dynamic Optimization Report" in report
        assert "test_study" in report
        assert "Best Parameters" in report
        assert "Best Metrics" in report


class TestGenerateReportWithHoldout:
    def test_generate_report_with_holdout(self):
        holdout = _make_holdout_report()
        report = generate_report(
            study_name="test_study",
            dataset_summary={"bars": 500},
            best_params={"x": 1},
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
            holdout_report=holdout,
        )
        assert "Holdout Validation" in report
        assert "low_vol_ranging" in report


class TestGenerateReportWritesFile:
    def test_generate_report_writes_file(self, tmp_path):
        out = str(tmp_path / "report.md")
        report = generate_report(
            study_name="test_study",
            dataset_summary={"bars": 500},
            best_params={"x": 1},
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
            output_path=out,
        )
        import os
        assert os.path.exists(out)
        with open(out) as f:
            content = f.read()
        assert content == report


# ── Stop-ship checks tests ───────────────────────────────────


class TestStopShipChecksAllFailWhenEmpty:
    def test_stop_ship_checks_all_fail_when_empty(self):
        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(trade_count=0, pnl_pct=0.0),
            best_objective=_make_objective(raw_score=REJECT_SCORE, is_rejected=True),
        )
        assert checks["runtime_sanity"] is False
        assert checks["objective_not_degenerate"] is False
        assert checks["stress_not_collapsed"] is False
        assert checks["yaml_validates"] is False
        assert checks["walkforward_robust"] is False
        assert checks["holdout_passed"] is False
        assert checks["sensitivity_stable"] is False


class TestStopShipChecksAllPass:
    def test_stop_ship_checks_all_pass(self):
        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
            walkforward_result=_make_walkforward_result(),
            stress_report=_make_stress_report(),
            dataset_audit=_make_audit_result(passed_strict=True),
            validation_result=_FakeValidation(valid=True),
            holdout_report=_make_holdout_report(passed=True),
            sensitivity_penalty=0.1,
        )
        for check_name, passed in checks.items():
            assert passed, f"Check '{check_name}' unexpectedly failed"


class TestStopShipChecksHoldoutCollapseFails:
    def test_stop_ship_checks_holdout_collapse_fails(self):
        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
            holdout_report=_make_holdout_report(passed=False, collapse=True),
        )
        assert checks["holdout_no_collapse"] is False
        assert checks["holdout_passed"] is False


class TestStopShipChecksSensitivityHighFails:
    def test_stop_ship_checks_sensitivity_high_fails(self):
        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
            sensitivity_penalty=0.8,
        )
        assert checks["sensitivity_stable"] is False


class TestStopShipChecksBackwardCompat:
    def test_stop_ship_checks_backward_compat(self):
        """Calling without new params works but fails those checks."""
        checks = run_stop_ship_checks(
            best_metrics=_make_metrics(),
            best_objective=_make_objective(),
        )
        assert checks["holdout_passed"] is False
        assert checks["holdout_no_collapse"] is False
        assert checks["sensitivity_stable"] is False
        # But core checks can still pass
        assert checks["runtime_sanity"] is True
        assert checks["objective_not_degenerate"] is True
