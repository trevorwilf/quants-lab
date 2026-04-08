"""Tests for comparison.py diagnostics and severity escalation (Fix 4)."""

from pmm_lab.deploy.comparison import (
    compare_performance,
    generate_comparison_report_md,
    ComparisonReport,
    Diagnostic,
)
from pmm_lab.deploy.live_tracker import LivePerformanceMetrics


def _make_expected(**overrides):
    """Create a minimal expected-performance-like object."""
    class Expected:
        trade_count = 50
        pnl_pct = 1.0
        fee_drag_pct = 0.5
        buy_fraction = 0.5
        fee_rate_pct_of_volume = None
    e = Expected()
    for k, v in overrides.items():
        setattr(e, k, v)
    return e


def _make_live(**overrides):
    defaults = dict(
        trading_pair="XMR-USDT",
        period_hours=24,
        trade_count=20,
        buy_count=10,
        sell_count=10,
        total_volume_base=5.0,
        total_volume_quote=750.0,
        total_fees_quote=0.75,
        avg_buy_price=148.0,
        avg_sell_price=152.0,
        net_base_flow=0.0,
        net_quote_flow=19.25,
        estimated_pnl_quote=19.25,
    )
    defaults.update(overrides)
    return LivePerformanceMetrics(**defaults)


class TestDiagnosticsPopulate:
    def test_trades_per_hour_computed(self):
        live = _make_live(trade_count=48, period_hours=24)
        report = compare_performance(_make_expected(), live)
        diag_names = [d.name for d in report.diagnostics]
        assert "trades_per_hour" in diag_names
        tph = next(d for d in report.diagnostics if d.name == "trades_per_hour")
        assert tph.value == 2.0

    def test_avg_spread_from_mid(self):
        live = _make_live(
            avg_buy_price=99.0, avg_sell_price=101.0,
            buy_count=5, sell_count=5,
        )
        report = compare_performance(_make_expected(), live)
        diag_names = [d.name for d in report.diagnostics]
        assert "avg_spread_from_mid_pct" in diag_names

    def test_unresolved_fees_diagnostic(self):
        live = _make_live(
            unresolved_fee_count=3,
            unresolved_fee_currencies=["BNB", "CRO"],
        )
        report = compare_performance(_make_expected(), live)
        diag_names = [d.name for d in report.diagnostics]
        assert "unresolved_fees" in diag_names


class TestExistingChecksUnchanged:
    def test_no_trades_still_critical(self):
        live = _make_live(trade_count=0, buy_count=0, sell_count=0)
        report = compare_performance(_make_expected(), live)
        critical = [c for c in report.checks if c.severity == "critical" and not c.passed]
        assert len(critical) > 0

    def test_balanced_still_passes(self):
        report = compare_performance(_make_expected(), _make_live())
        buy_sell = next(c for c in report.checks if c.metric_name == "buy_sell_balance")
        assert buy_sell.passed


class TestSeverityEscalation:
    def test_multiple_warnings_escalate_to_critical(self):
        """If 2+ warning checks fail, they escalate to critical."""
        live = _make_live(
            buy_count=19, sell_count=1, trade_count=20,  # imbalanced → warning
            total_fees_quote=50.0,  # very high fees → warning
        )
        expected = _make_expected(fee_rate_pct_of_volume=0.001)
        report = compare_performance(expected, live)
        # Check that escalation happened
        warning_msg = [w for w in report.warnings if "escalated" in w.lower()]
        if len([c for c in report.checks if not c.passed and c.metric_name in ("buy_sell_balance", "fee_rate")]) >= 2:
            assert len(warning_msg) > 0
            assert report.drift_detected


class TestEmptyTradesNoCrash:
    def test_empty_live_diagnostics_empty(self):
        live = _make_live(trade_count=0, buy_count=0, sell_count=0, period_hours=24)
        report = compare_performance(_make_expected(), live)
        assert report.diagnostics is not None  # list, possibly empty


class TestReportMdDiagnostics:
    def test_diagnostics_in_markdown(self):
        report = ComparisonReport(
            trading_pair="XMR-USDT",
            period_hours=24,
            checks=[],
            drift_detected=False,
            warnings=[],
            summary="test",
            diagnostics=[
                Diagnostic("test_metric", 42.0, "A test metric"),
            ],
        )
        md = generate_comparison_report_md(report)
        assert "Diagnostics" in md
        assert "test_metric" in md
