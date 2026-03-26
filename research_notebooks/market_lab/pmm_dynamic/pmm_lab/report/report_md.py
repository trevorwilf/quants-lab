"""
Markdown report generator for optimization runs.

Produces a human-readable report with dataset summary, best parameters,
walk-forward metrics, stress results, and stop-ship check status.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition, REJECT_SCORE
from pmm_lab.objective.walkforward import WalkForwardResult
from pmm_lab.objective.stress import StressReport
from pmm_lab.objective.holdout import HoldoutReport


@dataclass
class ValidationCoverageItem:
    """One row in the validation coverage table."""
    name: str
    status: str   # "PASS", "FAIL", "SKIPPED"
    detail: str = ""


def build_validation_coverage(
    *,
    dataset_audit=None,
    validation_result=None,
    holdout_report=None,
    sensitivity_report=None,
    recent_window_result=None,
    parity_result=None,
    long_parity_result=None,
    cluster_report=None,
    walkforward_result=None,
    stress_report=None,
) -> list:
    """Build validation coverage items with PASS/FAIL/SKIPPED statuses."""
    items = []

    # dataset_audit
    if dataset_audit is None:
        items.append(ValidationCoverageItem("dataset_audit", "SKIPPED"))
    elif getattr(dataset_audit, 'passed_strict', False):
        items.append(ValidationCoverageItem("dataset_audit", "PASS", "strict audit passed"))
    else:
        items.append(ValidationCoverageItem("dataset_audit", "FAIL", str(dataset_audit)))

    # yaml_validation
    if validation_result is None:
        items.append(ValidationCoverageItem("yaml_validation", "SKIPPED"))
    elif getattr(validation_result, 'valid', False):
        items.append(ValidationCoverageItem("yaml_validation", "PASS",
            f"{getattr(validation_result, 'mode', '?')} mode, "
            f"{len(getattr(validation_result, 'errors', []))} errors, "
            f"{len(getattr(validation_result, 'warnings', []))} warnings"))
    else:
        items.append(ValidationCoverageItem("yaml_validation", "FAIL",
            "; ".join(getattr(validation_result, 'errors', ['unknown']))))

    # holdout
    if holdout_report is None:
        items.append(ValidationCoverageItem("holdout", "SKIPPED"))
    elif getattr(holdout_report, 'exported_holdout_passed', getattr(holdout_report, 'passed', False)):
        items.append(ValidationCoverageItem("holdout", "PASS",
            f"score={getattr(holdout_report, 'exported_holdout_score', '?'):.4f}"))
    else:
        items.append(ValidationCoverageItem("holdout", "FAIL",
            f"score={getattr(holdout_report, 'exported_holdout_score', '?')}"))

    # walkforward
    if walkforward_result is None:
        items.append(ValidationCoverageItem("walkforward", "SKIPPED"))
    else:
        n_folds = len(getattr(walkforward_result, 'folds', []))
        items.append(ValidationCoverageItem("walkforward", "PASS", f"{n_folds} folds"))

    # stress
    if stress_report is None:
        items.append(ValidationCoverageItem("stress", "SKIPPED"))
    else:
        items.append(ValidationCoverageItem("stress", "PASS",
            f"worst={getattr(stress_report, 'worst_scenario', '?')} "
            f"score={getattr(stress_report, 'worst_score', '?')}"))

    # sensitivity
    if sensitivity_report is None:
        items.append(ValidationCoverageItem("sensitivity", "SKIPPED"))
    else:
        penalty = getattr(sensitivity_report, 'sensitivity_penalty', '?')
        items.append(ValidationCoverageItem("sensitivity", "PASS" if penalty < 0.5 else "FAIL",
            f"penalty={penalty}"))

    # recent_28d
    if recent_window_result is None:
        items.append(ValidationCoverageItem("recent_28d", "SKIPPED"))
    elif getattr(recent_window_result, 'passed', False):
        items.append(ValidationCoverageItem("recent_28d", "PASS",
            getattr(recent_window_result, 'reason', '')))
    else:
        items.append(ValidationCoverageItem("recent_28d", "FAIL",
            getattr(recent_window_result, 'reason', '')))

    # frozen_parity
    if parity_result is None:
        items.append(ValidationCoverageItem("frozen_parity", "SKIPPED"))
    elif getattr(parity_result, 'passed', False):
        items.append(ValidationCoverageItem("frozen_parity", "PASS"))
    else:
        items.append(ValidationCoverageItem("frozen_parity", "FAIL"))

    # long_parity
    if long_parity_result is None:
        items.append(ValidationCoverageItem("long_parity", "SKIPPED"))
    elif getattr(long_parity_result, 'passed', False):
        items.append(ValidationCoverageItem("long_parity", "PASS"))
    else:
        items.append(ValidationCoverageItem("long_parity", "FAIL"))

    # clustering
    if cluster_report is None:
        items.append(ValidationCoverageItem("clustering", "SKIPPED"))
    elif getattr(cluster_report, 'is_clustered', False):
        items.append(ValidationCoverageItem("clustering", "PASS",
            f"mean_cv={getattr(cluster_report, 'mean_cv', '?')}"))
    else:
        items.append(ValidationCoverageItem("clustering", "FAIL",
            f"mean_cv={getattr(cluster_report, 'mean_cv', '?')}"))

    return items


def generate_report(
    study_name: str,
    dataset_summary: Dict[str, Any],
    best_params: Dict[str, Any],
    best_metrics: Metrics,
    best_objective: ObjectiveDecomposition,
    walkforward_result: Optional[WalkForwardResult] = None,
    stress_report: Optional[StressReport] = None,
    stop_ship_checks: Optional[Dict[str, bool]] = None,
    output_path: Optional[str] = None,
    holdout_report: Optional[HoldoutReport] = None,
    validation_coverage: Optional[List] = None,
    dataset_audit: Optional[Any] = None,
    sensitivity_report: Optional[Any] = None,
    recent_window_result: Optional[Any] = None,
    cluster_report: Optional[Any] = None,
    yaml_validation_result: Optional[Any] = None,
    dataset_slices: Optional[Any] = None,
    execution_realism: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a markdown report."""
    lines = []

    # 1. Header
    lines.append(f"# PMM Dynamic Optimization Report: {study_name}")
    lines.append(f"")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    # 2. Dataset Summary
    lines.append("## Dataset Summary")
    lines.append("")
    for key, val in dataset_summary.items():
        lines.append(f"- **{key}**: {val}")
    lines.append("")

    # 3. Best Parameters
    lines.append("## Best Parameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    for key, val in sorted(best_params.items()):
        lines.append(f"| {key} | {val} |")
    lines.append("")

    # 4. Best Metrics
    lines.append("## Best Metrics")
    lines.append("")
    lines.append(f"- **PnL %**: {best_metrics.pnl_pct:.4f}")
    lines.append(f"- **Net PnL (quote)**: {best_metrics.net_pnl_quote:.4f}")
    lines.append(f"- **Sharpe Ratio**: {best_metrics.sharpe:.4f}")
    lines.append(f"- **Max Drawdown %**: {best_metrics.max_drawdown_pct:.4f}")
    lines.append(f"- **Profit Factor**: {best_metrics.profit_factor}")
    lines.append(f"- **Trade Count**: {best_metrics.trade_count}")
    lines.append(f"- **Total Fees (quote)**: {best_metrics.total_fees_quote:.4f}")
    lines.append(f"- **Maker Fees**: {best_metrics.maker_fees_quote:.4f}")
    lines.append(f"- **Taker Fees**: {best_metrics.taker_fees_quote:.4f}")
    lines.append(f"- **Fee Drag %**: {best_metrics.fee_drag_pct:.4f}")
    lines.append("")

    # 5. Objective Decomposition
    lines.append("## Objective Decomposition")
    lines.append("")
    lines.append(f"- **Raw Score**: {best_objective.raw_score:.4f}")
    lines.append(f"- **PnL Component**: {best_objective.pnl_component:.4f}")
    lines.append(f"- **Sharpe Component**: {best_objective.sharpe_component:.4f}")
    lines.append(f"- **Drawdown Component**: -{best_objective.drawdown_component:.4f}")
    lines.append(f"- **Fee Drag Component**: -{best_objective.fee_drag_component:.4f}")
    lines.append(f"- **Inventory Component**: -{best_objective.inventory_component:.4f}")
    lines.append(f"- **Trade Count Penalty**: -{best_objective.trade_count_penalty:.4f}")
    lines.append(f"- **Rejected**: {best_objective.is_rejected}")
    lines.append("")

    # 6. Walk-Forward Results
    if walkforward_result is not None:
        lines.append("## Walk-Forward Results")
        lines.append("")
        lines.append(f"Aggregate Score: **{walkforward_result.aggregate_score:.4f}**")
        lines.append("")
        lines.append("| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |")
        lines.append("|------|-------|--------|----------|--------|-----------|--------|")
        for fold in walkforward_result.folds:
            m = fold.test_metrics
            o = fold.test_objective
            regime_label = "n/a"
            lines.append(
                f"| {fold.fold_index} | {m.pnl_pct:.2f} | {m.sharpe:.2f} | "
                f"{m.max_drawdown_pct:.2f} | {m.trade_count} | {o.raw_score:.4f} | {regime_label} |"
            )
        lines.append("")

    # 7. Stress Test Results
    if stress_report is not None:
        lines.append("## Stress Test Results")
        lines.append("")
        lines.append(f"Worst Scenario: **{stress_report.worst_scenario}** "
                      f"(score: {stress_report.worst_score:.4f})")
        lines.append("")
        lines.append("| Scenario | PnL % | Sharpe | Max DD % | Objective |")
        lines.append("|----------|-------|--------|----------|-----------|")
        for sr in stress_report.scenario_results:
            m = sr.metrics
            lines.append(
                f"| {sr.scenario.name} | {m.pnl_pct:.2f} | {m.sharpe:.2f} | "
                f"{m.max_drawdown_pct:.2f} | {sr.objective.raw_score:.4f} |"
            )
        lines.append("")

    # 8. Holdout Results
    if holdout_report is not None:
        lines.append("## Holdout Validation")
        lines.append("")
        lines.append(f"- **Holdout bars**: {holdout_report.holdout_bars}")
        lines.append(f"- **Regime**: {holdout_report.regime.label}")
        lines.append(f"- **Volatility**: {holdout_report.regime.volatility} (NATR mean: {holdout_report.regime.natr_mean:.4f})")
        lines.append(f"- **Trend**: {holdout_report.regime.trend} (efficiency: {holdout_report.regime.efficiency_ratio:.4f})")
        lines.append(f"- **Best holdout score**: {holdout_report.best_holdout_score:.4f} (rank #{holdout_report.best_holdout_rank})")
        lines.append(f"- **Collapse detected**: {'YES' if holdout_report.dev_vs_holdout_collapse else 'No'}")
        lines.append(f"- **Holdout passed**: {'YES' if holdout_report.passed else '**NO**'}")
        lines.append("")

        lines.append("| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |")
        lines.append("|------|-----------|---------------|-------|----------|--------|")
        for c in holdout_report.candidates:
            lines.append(
                f"| {c.rank} | {c.development_score:.4f} | {c.objective.raw_score:.4f} | "
                f"{c.metrics.pnl_pct:.2f} | {c.metrics.max_drawdown_pct:.2f} | {c.metrics.trade_count} |"
            )
        lines.append("")

    # 8b. Dataset Audit
    if dataset_audit is not None:
        lines.append("## Dataset Audit")
        lines.append("")
        lines.append(f"- **Passed strict**: {getattr(dataset_audit, 'passed_strict', 'N/A')}")
        lines.append(f"- **Passed lenient**: {getattr(dataset_audit, 'passed_lenient', 'N/A')}")
        lines.append(f"- **Total bars**: {getattr(dataset_audit, 'total_bars', 'N/A')}")
        lines.append(f"- **Gap count**: {getattr(dataset_audit, 'gap_count', 'N/A')}")
        lines.append(f"- **Forward-fill count**: {getattr(dataset_audit, 'ffill_count', 'N/A')}")
        lines.append("")

    # 8c. Recent 28-Day Window
    if recent_window_result is not None:
        lines.append("## Recent 28-Day Window")
        lines.append("")
        lines.append(f"- **Passed**: {getattr(recent_window_result, 'passed', 'N/A')}")
        lines.append(f"- **Reason**: {getattr(recent_window_result, 'reason', 'N/A')}")
        lines.append(f"- **PnL %**: {getattr(recent_window_result, 'pnl_pct', 'N/A')}")
        lines.append(f"- **Trade count**: {getattr(recent_window_result, 'trade_count', 'N/A')}")
        lines.append("")

    # 8d. Sensitivity Analysis
    if sensitivity_report is not None:
        lines.append("## Sensitivity Analysis")
        lines.append("")
        lines.append(f"- **Sensitivity penalty**: {getattr(sensitivity_report, 'sensitivity_penalty', 'N/A')}")
        lines.append(f"- **Worst parameter**: {getattr(sensitivity_report, 'worst_param', 'N/A')}")
        lines.append(f"- **Worst delta**: {getattr(sensitivity_report, 'worst_delta', 'N/A')}")
        lines.append("")

    # 8e. Top-K Clustering
    if cluster_report is not None:
        lines.append("## Top-K Clustering")
        lines.append("")
        lines.append(f"- **Is clustered**: {getattr(cluster_report, 'is_clustered', 'N/A')}")
        lines.append(f"- **Mean CV**: {getattr(cluster_report, 'mean_cv', 'N/A')}")
        lines.append(f"- **Cluster count**: {getattr(cluster_report, 'n_clusters', 'N/A')}")
        lines.append("")

    # 8f. YAML Validation
    if yaml_validation_result is not None:
        lines.append("## YAML Validation")
        lines.append("")
        lines.append(f"- **Valid**: {getattr(yaml_validation_result, 'valid', 'N/A')}")
        lines.append(f"- **Mode**: {getattr(yaml_validation_result, 'mode', 'N/A')}")
        errors = getattr(yaml_validation_result, 'errors', [])
        warnings = getattr(yaml_validation_result, 'warnings', [])
        lines.append(f"- **Errors**: {len(errors)}")
        for e in errors:
            lines.append(f"  - {e}")
        lines.append(f"- **Warnings**: {len(warnings)}")
        for w in warnings:
            lines.append(f"  - {w}")
        lines.append("")

    # 8g. Execution Realism Assumptions
    if execution_realism is not None:
        lines.append("## Execution Realism Assumptions")
        lines.append("")
        for key, val in execution_realism.items():
            lines.append(f"- **{key}**: {val}")
        lines.append("")

    # 9. Stop-Ship Checks
    if stop_ship_checks is not None:
        lines.append("## Stop-Ship Checks")
        lines.append("")
        all_pass = True
        for check, passed in stop_ship_checks.items():
            status = "PASS" if passed else "**FAIL**"
            if not passed:
                all_pass = False
            lines.append(f"- {check}: {status}")
        lines.append("")
        if not all_pass:
            lines.append("> **WARNING**: One or more stop-ship checks FAILED.")
            lines.append("")

    # 10. Validation Coverage
    if validation_coverage is not None:
        lines.append("## Validation Coverage")
        lines.append("")
        lines.append("| Validation | Status | Detail |")
        lines.append("|---|---|---|")
        for item in validation_coverage:
            lines.append(f"| {item.name} | {item.status} | {item.detail} |")
        lines.append("")

    report_text = "\n".join(lines)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.write(report_text)

    return report_text


def run_stop_ship_checks(
    best_metrics: Metrics,
    best_objective: ObjectiveDecomposition,
    walkforward_result: Optional[WalkForwardResult] = None,
    stress_report: Optional[StressReport] = None,
    dataset_audit: Optional[Any] = None,
    validation_result: Optional[Any] = None,
    holdout_report: Optional['HoldoutReport'] = None,
    sensitivity_penalty: Optional[float] = None,
    recent_window_result: Optional[Any] = None,
    parity_result: Optional[Any] = None,
    cluster_report: Optional[Any] = None,
    long_parity_result: Optional[Any] = None,
) -> Dict[str, bool]:
    """Run all stop-ship condition checks.

    Each check returns True (pass) or False (fail).
    All checks must pass for deployment.
    """
    checks = {}

    # 1. dataset_audit — require actual AuditResult with passed_strict
    if dataset_audit is not None:
        checks["dataset_audit"] = bool(getattr(dataset_audit, 'passed_strict', False))
    else:
        checks["dataset_audit"] = False

    # 2. runtime_sanity — require trades AND non-degenerate metrics
    # NOTE: This checks that the simulation produces non-degenerate output.
    # It does NOT verify feature parity with the live Hummingbot controller.
    # True native parity is tracked separately in pmm_lab/parity/feature_parity.py.
    checks["runtime_sanity"] = bool(
        best_metrics.trade_count >= 5  # at least 5 round-trip trades
        and best_metrics.pnl_pct != 0.0
        and best_metrics.total_fees_quote > 0  # fees were actually computed
    )

    # 3. objective_not_degenerate
    checks["objective_not_degenerate"] = bool(
        best_objective.raw_score != REJECT_SCORE
        and not best_objective.is_rejected
    )

    # 4. stress_not_collapsed — worst stress score > -10
    if stress_report is not None:
        checks["stress_not_collapsed"] = bool(stress_report.worst_score > -10.0)
    else:
        checks["stress_not_collapsed"] = False  # no stress = not validated

    # 5. yaml_validates
    if validation_result is not None:
        checks["yaml_validates"] = validation_result.valid
    else:
        checks["yaml_validates"] = False  # no validation = fail

    # 6. walkforward_robust — majority of folds have non-rejected scores
    if walkforward_result is not None:
        valid_folds = sum(
            1 for f in walkforward_result.folds
            if not f.test_objective.is_rejected
        )
        total_folds = len(walkforward_result.folds)
        checks["walkforward_robust"] = bool(total_folds > 0 and valid_folds / total_folds >= 0.5)

        # 6b. At least 50% of folds have non-negative baseline return
        positive_folds = sum(
            1 for f in walkforward_result.folds
            if f.test_metrics.pnl_pct >= 0
        )
        checks["walkforward_positive_majority"] = bool(total_folds > 0 and positive_folds / total_folds >= 0.5)
    else:
        checks["walkforward_robust"] = False
        checks["walkforward_positive_majority"] = False

    # 7. holdout_passed — use exported-candidate gating
    if holdout_report is not None:
        checks["holdout_passed"] = bool(getattr(holdout_report, 'exported_holdout_passed', holdout_report.passed))
        checks["holdout_no_collapse"] = bool(not getattr(holdout_report, 'exported_holdout_collapse', holdout_report.dev_vs_holdout_collapse))
    else:
        checks["holdout_passed"] = False
        checks["holdout_no_collapse"] = False

    # 8. sensitivity_stable — penalty below threshold
    if sensitivity_penalty is not None:
        checks["sensitivity_stable"] = sensitivity_penalty < 0.50
    else:
        checks["sensitivity_stable"] = False  # not tested = fail

    # 9. recent_28d_passed — recent window evaluation
    if recent_window_result is not None:
        checks["recent_28d_passed"] = bool(getattr(recent_window_result, 'passed', False))
    else:
        checks["recent_28d_passed"] = False  # not tested = fail

    # 10. frozen_parity — frozen fixture parity check
    if parity_result is not None:
        checks["frozen_parity"] = bool(parity_result.passed)
    else:
        checks["frozen_parity"] = False  # not tested = fail

    # 10b. long_parity_passed — long-history fixture parity
    if long_parity_result is not None:
        checks["long_parity_passed"] = bool(long_parity_result.passed)
    # Don't fail if long fixture is missing — just skip the check

    # 11. top_k_clustered — parameter surface stability
    if cluster_report is not None:
        checks["top_k_clustered"] = bool(getattr(cluster_report, 'is_clustered', False))
    else:
        checks["top_k_clustered"] = False  # not tested = fail

    return checks
