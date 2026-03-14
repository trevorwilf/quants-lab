"""Tests for deployment monitoring."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pmm_lab.deploy.monitor import (
    MonitoringResult,
    run_monitoring_check,
    monitor_all_deployments,
    generate_monitoring_summary,
)
from pmm_lab.deploy.comparison import ComparisonReport, DriftCheck
from pmm_lab.deploy.live_tracker import LivePerformanceMetrics


def _create_mock_package(path, trading_pair="XMR-USDT"):
    """Create a minimal package.json for testing."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    data = {
        "study_name": "test", "connector": "nonkyc",
        "trading_pair": trading_pair, "interval": "5m",
        "created_at": "2025-01-01T00:00:00+00:00",
        "config_dict": {}, "sim_config_params": {},
        "expected": {
            "pnl_pct": 5.0, "max_drawdown_pct": 10.0, "trade_count": 100,
            "sharpe": 1.5, "profit_factor": 2.0, "fee_drag_pct": 1.0,
            "median_trade_pnl_quote": 0.5,
        },
        "dataset_hash": "abc", "dataset_bars": 500,
        "objective_score": 0.5, "objective_version": 2,
    }
    with open(p / "package.json", "w") as f:
        json.dump(data, f)


def _make_comparison(drift=False):
    """Create a mock ComparisonReport."""
    checks = [
        DriftCheck(
            metric_name="trade_activity", expected=1.0, actual=1.0,
            deviation_pct=0.0, threshold_pct=50.0, passed=True, severity="info",
        ),
    ]
    if drift:
        checks.append(DriftCheck(
            metric_name="pnl_direction", expected=1.0, actual=-1.0,
            deviation_pct=200.0, threshold_pct=100.0, passed=False, severity="critical",
        ))
    return ComparisonReport(
        trading_pair="XMR-USDT", period_hours=24.0,
        checks=checks, drift_detected=drift,
        warnings=["PnL sign mismatch"] if drift else [],
        summary="XMR-USDT: 1/2 checks" if drift else "XMR-USDT: 1/1 checks",
    )


def _make_live_metrics(trade_count=10, pnl=2.0):
    return LivePerformanceMetrics(
        trading_pair="XMR-USDT", period_hours=24.0,
        trade_count=trade_count, buy_count=5, sell_count=5,
        total_volume_base=1.0, total_volume_quote=200.0,
        total_fees_quote=0.02, avg_buy_price=195.0, avg_sell_price=198.0,
        net_base_flow=0.0, net_quote_flow=pnl, estimated_pnl_quote=pnl,
    )


class TestMonitoringResultDriftProperty:
    def test_monitoring_result_drift_property(self):
        result = MonitoringResult(
            package_dir="/tmp", study_name="test",
            trading_pair="XMR-USDT", connector="nonkyc",
            comparison=_make_comparison(drift=True),
            live_metrics=_make_live_metrics(),
            checked_at="2025-01-01T00:00:00+00:00",
        )
        assert result.drift_detected is True


class TestMonitoringResultNoComparison:
    def test_monitoring_result_no_comparison(self):
        result = MonitoringResult(
            package_dir="/tmp", study_name="test",
            trading_pair="XMR-USDT", connector="nonkyc",
            comparison=None, live_metrics=None,
            checked_at="2025-01-01T00:00:00+00:00",
        )
        assert result.drift_detected is False


class TestMonitoringResultErrorSummary:
    def test_monitoring_result_error_summary(self):
        result = MonitoringResult(
            package_dir="/tmp", study_name="test",
            trading_pair="XMR-USDT", connector="nonkyc",
            comparison=None, live_metrics=None,
            error="Database connection failed",
            checked_at="2025-01-01T00:00:00+00:00",
        )
        assert "ERROR" in result.summary
        assert "Database connection failed" in result.summary


class TestRunMonitoringCheckMissingPackage:
    def test_run_monitoring_check_missing_package(self, tmp_path):
        result = run_monitoring_check(str(tmp_path / "nonexistent"))
        assert result.error is not None
        assert "Failed to load package" in result.error
        assert result.study_name == "unknown"


class TestMonitorAllEmptyDir:
    def test_monitor_all_empty_dir(self, tmp_path):
        results = monitor_all_deployments(str(tmp_path))
        assert results == []


class TestMonitorAllFindsPackages:
    def test_monitor_all_finds_packages(self, tmp_path):
        # Create 2 mock package dirs
        _create_mock_package(tmp_path / "pkg1")
        _create_mock_package(tmp_path / "pkg2", trading_pair="BTC-USDT")

        # Mock the tracker to return error (DB unreachable)
        with patch("pmm_lab.deploy.monitor.LivePerformanceTracker") as mock_cls:
            mock_tracker = MagicMock()
            mock_tracker.ping.return_value = False
            mock_cls.return_value = mock_tracker

            results = monitor_all_deployments(str(tmp_path))

        assert len(results) == 2
        pairs = {r.trading_pair for r in results}
        assert "XMR-USDT" in pairs
        assert "BTC-USDT" in pairs
        # Both should have errors since DB is unreachable
        assert all(r.error is not None for r in results)


class TestGenerateMonitoringSummaryFormat:
    def test_generate_monitoring_summary_format(self):
        results = [
            MonitoringResult(
                package_dir="/tmp/a", study_name="study_a",
                trading_pair="XMR-USDT", connector="nonkyc",
                comparison=_make_comparison(drift=False),
                live_metrics=_make_live_metrics(),
                checked_at="2025-01-01",
            ),
        ]
        summary = generate_monitoring_summary(results)
        assert "# Deployment Monitoring Summary" in summary
        assert "| Pair |" in summary
        assert "XMR-USDT" in summary


class TestGenerateMonitoringSummaryCounts:
    def test_generate_monitoring_summary_counts(self):
        results = [
            # OK
            MonitoringResult(
                package_dir="/a", study_name="s1",
                trading_pair="A-USDT", connector="x",
                comparison=_make_comparison(drift=False),
                live_metrics=_make_live_metrics(),
            ),
            # OK
            MonitoringResult(
                package_dir="/b", study_name="s2",
                trading_pair="B-USDT", connector="x",
                comparison=_make_comparison(drift=False),
                live_metrics=_make_live_metrics(),
            ),
            # Drift
            MonitoringResult(
                package_dir="/c", study_name="s3",
                trading_pair="C-USDT", connector="x",
                comparison=_make_comparison(drift=True),
                live_metrics=_make_live_metrics(),
            ),
            # Error
            MonitoringResult(
                package_dir="/d", study_name="s4",
                trading_pair="D-USDT", connector="x",
                comparison=None, live_metrics=None,
                error="DB down",
            ),
        ]
        summary = generate_monitoring_summary(results)
        assert "OK: 2" in summary
        assert "Drift detected: 1" in summary
        assert "Errors: 1" in summary
