"""
Deployment monitoring.

Loads a deployment package's expected metrics and compares them
against live performance from the Hummingbot database.

Usage:
    report = run_monitoring_check("artifacts/deploy/XMR_USDT_5m/deploy")
    if report.drift_detected:
        print("ALERT:", report.summary)

    # Or check all deployed packages:
    reports = monitor_all_deployments("artifacts/")
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from pmm_lab.deploy.package import load_deployment_package, DeploymentPackage
from pmm_lab.deploy.live_tracker import LivePerformanceTracker, LivePerformanceMetrics
from pmm_lab.deploy.comparison import compare_performance, ComparisonReport, generate_comparison_report_md

logger = logging.getLogger(__name__)


@dataclass
class MonitoringResult:
    """Result of monitoring one deployment."""
    package_dir: str
    study_name: str
    trading_pair: str
    connector: str
    comparison: Optional[ComparisonReport]
    live_metrics: Optional[LivePerformanceMetrics]
    error: Optional[str] = None
    checked_at: str = ""

    @property
    def drift_detected(self) -> bool:
        return self.comparison.drift_detected if self.comparison else False

    @property
    def summary(self) -> str:
        if self.error:
            return f"{self.trading_pair}: ERROR — {self.error}"
        if self.comparison:
            return self.comparison.summary
        return f"{self.trading_pair}: no comparison available"


def run_monitoring_check(
    package_dir: str,
    hours: float = 24.0,
    db_url: Optional[str] = None,
) -> MonitoringResult:
    """Run a monitoring check on one deployment package.

    Parameters
    ----------
    package_dir : str
        Path to the deployment package directory.
    hours : float
        Look back period for live data.
    db_url : str, optional
        Hummingbot PostgreSQL URL. Auto-detected if None.

    Returns
    -------
    MonitoringResult
    """
    checked_at = datetime.now(timezone.utc).isoformat()

    try:
        package = load_deployment_package(package_dir)
    except Exception as e:
        return MonitoringResult(
            package_dir=package_dir,
            study_name="unknown", trading_pair="unknown", connector="unknown",
            comparison=None, live_metrics=None,
            error=f"Failed to load package: {e}",
            checked_at=checked_at,
        )

    try:
        tracker = LivePerformanceTracker(db_url)
        if not tracker.ping():
            return MonitoringResult(
                package_dir=package_dir,
                study_name=package.study_name,
                trading_pair=package.trading_pair,
                connector=package.connector,
                comparison=None, live_metrics=None,
                error="Hummingbot database not reachable",
                checked_at=checked_at,
            )

        live_metrics = tracker.get_performance(
            package.connector, package.trading_pair, hours,
        )

        comparison = compare_performance(package.expected, live_metrics)

        return MonitoringResult(
            package_dir=package_dir,
            study_name=package.study_name,
            trading_pair=package.trading_pair,
            connector=package.connector,
            comparison=comparison,
            live_metrics=live_metrics,
            checked_at=checked_at,
        )

    except Exception as e:
        return MonitoringResult(
            package_dir=package_dir,
            study_name=package.study_name,
            trading_pair=package.trading_pair,
            connector=package.connector,
            comparison=None, live_metrics=None,
            error=f"Monitoring failed: {e}",
            checked_at=checked_at,
        )


def monitor_all_deployments(
    artifacts_dir: str,
    hours: float = 24.0,
    db_url: Optional[str] = None,
) -> List[MonitoringResult]:
    """Monitor all deployment packages in a directory.

    Scans for directories containing package.json and runs
    monitoring checks on each.

    Parameters
    ----------
    artifacts_dir : str
        Base artifacts directory.
    hours : float
        Look back period.
    db_url : str, optional
        Database URL.

    Returns
    -------
    List[MonitoringResult]
    """
    results = []
    base = Path(artifacts_dir)

    # Find all package.json files
    for package_json in base.rglob("package.json"):
        package_dir = str(package_json.parent)
        logger.info("Monitoring: %s", package_dir)
        result = run_monitoring_check(package_dir, hours, db_url)
        results.append(result)

    if not results:
        logger.warning("No deployment packages found in %s", artifacts_dir)

    return results


def generate_monitoring_summary(results: List[MonitoringResult]) -> str:
    """Generate a summary of all monitoring results.

    Returns
    -------
    str
        Markdown summary.
    """
    lines = []
    lines.append("# Deployment Monitoring Summary")
    lines.append("")
    lines.append(f"Checked at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Deployments checked: {len(results)}")
    lines.append("")

    drift_count = sum(1 for r in results if r.drift_detected)
    error_count = sum(1 for r in results if r.error)
    ok_count = len(results) - drift_count - error_count

    lines.append(f"- OK: {ok_count}")
    lines.append(f"- Drift detected: {drift_count}")
    lines.append(f"- Errors: {error_count}")
    lines.append("")

    lines.append("## Details")
    lines.append("")
    lines.append("| Pair | Study | Status | Trades | Est PnL | Notes |")
    lines.append("|------|-------|--------|--------|---------|-------|")

    for r in results:
        if r.error:
            lines.append(f"| {r.trading_pair} | {r.study_name} | ERROR | — | — | {r.error[:50]} |")
        elif r.live_metrics and r.comparison:
            status = "DRIFT" if r.drift_detected else "OK"
            lines.append(
                f"| {r.trading_pair} | {r.study_name} | {status} | "
                f"{r.live_metrics.trade_count} | "
                f"{r.live_metrics.estimated_pnl_quote:.2f} | "
                f"{'; '.join(r.comparison.warnings[:2]) if r.comparison.warnings else '—'} |"
            )
        else:
            lines.append(f"| {r.trading_pair} | {r.study_name} | UNKNOWN | — | — | — |")

    lines.append("")
    return "\n".join(lines)
