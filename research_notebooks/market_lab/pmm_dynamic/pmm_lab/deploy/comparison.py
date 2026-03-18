"""
Performance comparison — live vs backtest drift detection.

Compares live trading metrics against backtest predictions from
the deployment package. Flags significant deviations that may
indicate the strategy is no longer performing as expected.

Usage:
    report = compare_performance(package.expected, live_metrics)
    if report.drift_detected:
        print("Performance has drifted from backtest predictions")
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DriftCheck:
    """Result of one drift check."""
    metric_name: str
    expected: float
    actual: float
    deviation_pct: float        # (actual - expected) / |expected| * 100
    threshold_pct: float        # max acceptable deviation
    passed: bool                # True if within threshold
    severity: str               # "info", "warning", "critical"


@dataclass
class ComparisonReport:
    """Full comparison of live vs backtest performance."""
    trading_pair: str
    period_hours: float
    checks: List[DriftCheck]
    drift_detected: bool        # True if any critical check failed
    warnings: List[str]
    summary: str


def compare_performance(
    expected,  # ExpectedPerformance
    live,      # LivePerformanceMetrics
    thresholds: Optional[Dict[str, float]] = None,
) -> ComparisonReport:
    """Compare live metrics against backtest expectations.

    Parameters
    ----------
    expected : ExpectedPerformance
        Backtest-predicted metrics from deployment package.
    live : LivePerformanceMetrics
        Computed live metrics.
    thresholds : Dict[str, float], optional
        Per-metric deviation thresholds (percentage).
        Defaults to conservative thresholds.

    Returns
    -------
    ComparisonReport
    """
    if thresholds is None:
        thresholds = {
            "trade_rate": 50.0,       # live trade count can deviate ±50% from expected rate
            "fee_drag": 100.0,        # fees can be up to 2x expected
            "buy_sell_ratio": 30.0,   # buy/sell ratio shouldn't deviate too much
        }

    checks = []
    warnings = []

    # 1. Trade rate check
    # Normalize expected trades to the live observation period
    # Expected trade_count is from a much longer backtest, so scale by time
    if expected.trade_count > 0 and live.period_hours > 0:
        # Rough scaling: expected trades per hour from backtest
        # We can't know the backtest duration from ExpectedPerformance alone,
        # so just check that live has *some* trades
        if live.trade_count == 0:
            checks.append(DriftCheck(
                metric_name="trade_activity",
                expected=1.0, actual=0.0, deviation_pct=-100.0,
                threshold_pct=thresholds.get("trade_rate", 50.0),
                passed=False, severity="critical",
            ))
            warnings.append("No live trades detected — bot may not be trading")
        else:
            checks.append(DriftCheck(
                metric_name="trade_activity",
                expected=1.0, actual=1.0, deviation_pct=0.0,
                threshold_pct=thresholds.get("trade_rate", 50.0),
                passed=True, severity="info",
            ))

    # 2. Buy/sell balance check
    if live.trade_count > 0:
        buy_frac = live.buy_count / live.trade_count
        # Use expected buy fraction from backtest if available
        if getattr(expected, 'buy_fraction', None) is not None:
            expected_buy_frac = expected.buy_fraction
        else:
            expected_buy_frac = 0.5  # legacy fallback
        deviation = abs(buy_frac - expected_buy_frac) * 100

        passed = deviation <= thresholds.get("buy_sell_ratio", 30.0)
        checks.append(DriftCheck(
            metric_name="buy_sell_balance",
            expected=expected_buy_frac * 100, actual=buy_frac * 100,
            deviation_pct=deviation,
            threshold_pct=thresholds.get("buy_sell_ratio", 30.0),
            passed=passed,
            severity="warning" if not passed else "info",
        ))
        if not passed:
            warnings.append(
                f"Buy/sell imbalance: {buy_frac*100:.1f}% buys "
                f"(expected ~{expected_buy_frac*100:.0f}%, deviation {deviation:.1f}%)"
            )

    # 3. PnL direction check
    if live.estimated_pnl_quote != 0 and expected.pnl_pct != 0:
        # Check if signs match
        pnl_sign_match = (live.estimated_pnl_quote > 0) == (expected.pnl_pct > 0)
        checks.append(DriftCheck(
            metric_name="pnl_direction",
            expected=1.0 if expected.pnl_pct > 0 else -1.0,
            actual=1.0 if live.estimated_pnl_quote > 0 else -1.0,
            deviation_pct=0.0 if pnl_sign_match else 200.0,
            threshold_pct=100.0,
            passed=pnl_sign_match,
            severity="critical" if not pnl_sign_match else "info",
        ))
        if not pnl_sign_match:
            warnings.append(
                f"PnL sign mismatch: expected {'profit' if expected.pnl_pct > 0 else 'loss'}, "
                f"live shows {'profit' if live.estimated_pnl_quote > 0 else 'loss'}"
            )

    # 4. Fee drag check (if enough data)
    if live.total_fees_quote > 0 and live.total_volume_quote > 0:
        live_fee_rate = live.total_fees_quote / live.total_volume_quote * 100
        # Prefer volume-normalized expected fee rate (Phase 2 field)
        if getattr(expected, 'fee_rate_pct_of_volume', None) is not None and expected.fee_rate_pct_of_volume > 0:
            expected_fee_rate = expected.fee_rate_pct_of_volume
        elif expected.fee_drag_pct > 0:
            # Legacy fallback: fee_drag_pct is % of equity, not volume — rough approximation
            expected_fee_rate = expected.fee_drag_pct / 100
        else:
            expected_fee_rate = 0.1
        if expected_fee_rate > 0:
            fee_deviation = abs(live_fee_rate - expected_fee_rate) / expected_fee_rate * 100
            passed = fee_deviation <= thresholds.get("fee_drag", 100.0)
            checks.append(DriftCheck(
                metric_name="fee_rate",
                expected=expected_fee_rate,
                actual=live_fee_rate,
                deviation_pct=fee_deviation,
                threshold_pct=thresholds.get("fee_drag", 100.0),
                passed=passed,
                severity="warning" if not passed else "info",
            ))

    # Aggregate
    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    drift_detected = len(critical_failures) > 0

    # Summary
    n_pass = sum(1 for c in checks if c.passed)
    summary = (
        f"{live.trading_pair}: {n_pass}/{len(checks)} checks passed, "
        f"{live.trade_count} trades in {live.period_hours:.0f}h, "
        f"est PnL: {live.estimated_pnl_quote:.2f} quote"
    )
    if drift_detected:
        summary += " — DRIFT DETECTED"

    return ComparisonReport(
        trading_pair=live.trading_pair,
        period_hours=live.period_hours,
        checks=checks,
        drift_detected=drift_detected,
        warnings=warnings,
        summary=summary,
    )


def generate_comparison_report_md(report: ComparisonReport) -> str:
    """Generate a markdown comparison report."""
    lines = []
    lines.append(f"# Live vs Backtest Comparison: {report.trading_pair}")
    lines.append("")
    lines.append(f"Period: {report.period_hours:.0f} hours")
    lines.append(f"Drift detected: {'**YES**' if report.drift_detected else 'No'}")
    lines.append("")

    lines.append("## Checks")
    lines.append("")
    lines.append("| Metric | Expected | Actual | Deviation | Threshold | Status |")
    lines.append("|--------|----------|--------|-----------|-----------|--------|")
    for c in report.checks:
        status = "PASS" if c.passed else f"**{c.severity.upper()}**"
        lines.append(
            f"| {c.metric_name} | {c.expected:.2f} | {c.actual:.2f} | "
            f"{c.deviation_pct:.1f}% | {c.threshold_pct:.0f}% | {status} |"
        )
    lines.append("")

    if report.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(f"**Summary:** {report.summary}")
    return "\n".join(lines)
