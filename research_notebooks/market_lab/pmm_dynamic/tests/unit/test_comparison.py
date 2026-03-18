"""Tests for performance comparison (live vs backtest drift detection)."""

import pytest

from pmm_lab.deploy.package import ExpectedPerformance
from pmm_lab.deploy.live_tracker import LivePerformanceMetrics
from pmm_lab.deploy.comparison import (
    compare_performance,
    generate_comparison_report_md,
    ComparisonReport,
    DriftCheck,
)


def _make_expected(**overrides):
    defaults = dict(
        pnl_pct=5.0, max_drawdown_pct=10.0, trade_count=100,
        sharpe=1.5, profit_factor=2.0, fee_drag_pct=1.0,
        median_trade_pnl_quote=0.5,
    )
    defaults.update(overrides)
    return ExpectedPerformance(**defaults)


def _make_live(**overrides):
    defaults = dict(
        trading_pair="XMR-USDT", period_hours=24.0,
        trade_count=15, buy_count=8, sell_count=7,
        total_volume_base=1.0, total_volume_quote=200.0,
        total_fees_quote=0.02,  # fee rate = 0.01% matches expected_fee_rate
        avg_buy_price=195.0, avg_sell_price=198.0,
        net_base_flow=0.1, net_quote_flow=2.0,
        estimated_pnl_quote=2.6,
    )
    defaults.update(overrides)
    return LivePerformanceMetrics(**defaults)


class TestComparisonNoTradesCritical:
    def test_comparison_no_trades_critical(self):
        expected = _make_expected()
        live = _make_live(
            trade_count=0, buy_count=0, sell_count=0,
            total_volume_base=0.0, total_volume_quote=0.0,
            total_fees_quote=0.0, avg_buy_price=0.0, avg_sell_price=0.0,
            net_base_flow=0.0, net_quote_flow=0.0, estimated_pnl_quote=0.0,
        )
        report = compare_performance(expected, live)
        assert report.drift_detected is True
        critical = [c for c in report.checks if c.severity == "critical" and not c.passed]
        assert len(critical) > 0
        assert any("trade" in c.metric_name for c in critical)


class TestComparisonBalancedPasses:
    def test_comparison_balanced_passes(self):
        expected = _make_expected()
        live = _make_live()
        report = compare_performance(expected, live)
        assert report.drift_detected is False
        assert all(c.passed for c in report.checks)


class TestComparisonImbalancedWarns:
    def test_comparison_imbalanced_warns(self):
        expected = _make_expected()
        # 90% buys
        live = _make_live(trade_count=20, buy_count=18, sell_count=2)
        report = compare_performance(expected, live)
        balance_checks = [c for c in report.checks if c.metric_name == "buy_sell_balance"]
        assert len(balance_checks) == 1
        assert not balance_checks[0].passed
        assert balance_checks[0].severity == "warning"


class TestComparisonPnlSignMismatchCritical:
    def test_comparison_pnl_sign_mismatch_critical(self):
        expected = _make_expected(pnl_pct=5.0)  # positive backtest
        live = _make_live(estimated_pnl_quote=-3.0)  # negative live
        report = compare_performance(expected, live)
        pnl_checks = [c for c in report.checks if c.metric_name == "pnl_direction"]
        assert len(pnl_checks) == 1
        assert not pnl_checks[0].passed
        assert pnl_checks[0].severity == "critical"
        assert report.drift_detected is True


class TestComparisonPnlSignMatchPasses:
    def test_comparison_pnl_sign_match_passes(self):
        expected = _make_expected(pnl_pct=5.0)
        live = _make_live(estimated_pnl_quote=2.0)
        report = compare_performance(expected, live)
        pnl_checks = [c for c in report.checks if c.metric_name == "pnl_direction"]
        assert len(pnl_checks) == 1
        assert pnl_checks[0].passed


class TestComparisonReportMdFormat:
    def test_comparison_report_md_format(self):
        expected = _make_expected()
        live = _make_live()
        report = compare_performance(expected, live)
        md = generate_comparison_report_md(report)
        assert "# Live vs Backtest Comparison" in md
        assert "XMR-USDT" in md
        assert "## Checks" in md
        assert "| Metric |" in md
        assert "**Summary:**" in md


class TestComparisonCustomThresholds:
    def test_comparison_custom_thresholds(self):
        expected = _make_expected()
        # 80% buys — normally a warning at 30% threshold
        live = _make_live(trade_count=10, buy_count=8, sell_count=2)
        # With a loose threshold, should pass
        report = compare_performance(expected, live, thresholds={
            "trade_rate": 50.0,
            "fee_drag": 100.0,
            "buy_sell_ratio": 50.0,  # looser than default 30%
        })
        balance_checks = [c for c in report.checks if c.metric_name == "buy_sell_balance"]
        assert len(balance_checks) == 1
        assert balance_checks[0].passed


class TestComparisonEmptyLiveNoCrash:
    def test_comparison_empty_live_no_crash(self):
        expected = _make_expected()
        live = _make_live(
            trade_count=0, buy_count=0, sell_count=0,
            total_volume_base=0.0, total_volume_quote=0.0,
            total_fees_quote=0.0, avg_buy_price=0.0, avg_sell_price=0.0,
            net_base_flow=0.0, net_quote_flow=0.0, estimated_pnl_quote=0.0,
        )
        report = compare_performance(expected, live)
        assert isinstance(report, ComparisonReport)
        assert isinstance(report.summary, str)


class TestComparisonUsesVolumeNormalizedFeeRate:
    """Fee comparison should use fee_rate_pct_of_volume when available."""

    def test_volume_fee_rate_used_when_available(self):
        expected = _make_expected(fee_drag_pct=1.0)
        expected.fee_rate_pct_of_volume = 0.15
        live = _make_live(total_fees_quote=0.30, total_volume_quote=200.0)
        report = compare_performance(expected, live)
        fee_checks = [c for c in report.checks if c.metric_name == "fee_rate"]
        if fee_checks:
            assert fee_checks[0].expected == 0.15, \
                "Should use fee_rate_pct_of_volume, not fee_drag_pct"


class TestComparisonUsesExpectedBuyFraction:
    """Buy/sell balance should use expected buy_fraction when available."""

    def test_no_false_alarm_with_correct_buy_fraction(self):
        expected = _make_expected()
        expected.buy_fraction = 0.8
        live = _make_live(trade_count=20, buy_count=16, sell_count=4)
        report = compare_performance(expected, live)
        balance_checks = [c for c in report.checks if c.metric_name == "buy_sell_balance"]
        assert len(balance_checks) == 1
        assert balance_checks[0].passed, \
            "Should not warn when live buy fraction matches expected"
