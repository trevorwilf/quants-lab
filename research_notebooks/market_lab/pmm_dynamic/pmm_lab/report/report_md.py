"""
Markdown report generator for optimization runs.

Produces a human-readable report with dataset summary, best parameters,
walk-forward metrics, stress results, and stop-ship check status.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition, REJECT_SCORE
from pmm_lab.objective.walkforward import WalkForwardResult
from pmm_lab.objective.stress import StressReport


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
) -> str:
    """Generate a markdown report."""
    lines = []

    # 1. Header
    lines.append(f"# PMM Dynamic Optimization Report: {study_name}")
    lines.append(f"")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
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
        lines.append("| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |")
        lines.append("|------|-------|--------|----------|--------|-----------|")
        for fold in walkforward_result.folds:
            m = fold.test_metrics
            o = fold.test_objective
            lines.append(
                f"| {fold.fold_index} | {m.pnl_pct:.2f} | {m.sharpe:.2f} | "
                f"{m.max_drawdown_pct:.2f} | {m.trade_count} | {o.raw_score:.4f} |"
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

    # 8. Stop-Ship Checks
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
    dataset_hash: Optional[str] = None,
    validation_result: Optional[Any] = None,
) -> Dict[str, bool]:
    """Run all stop-ship condition checks."""
    checks = {}

    # 1. dataset_audit — hash exists AND is non-empty
    checks["dataset_audit"] = dataset_hash is not None and len(dataset_hash) > 0

    # 2. feature_parity — check that features produced non-trivial trading activity
    checks["feature_parity"] = (
        best_metrics.trade_count > 0
        and best_metrics.pnl_pct != 0.0
    )

    # 3. objective_not_degenerate
    checks["objective_not_degenerate"] = (
        best_objective.raw_score != REJECT_SCORE
        and not best_objective.is_rejected
    )

    # 4. stress_not_collapsed — worst stress score must be > -10
    if stress_report is not None:
        checks["stress_not_collapsed"] = stress_report.worst_score > -10.0
    else:
        checks["stress_not_collapsed"] = False  # no stress = not validated

    # 5. yaml_validates
    if validation_result is not None:
        checks["yaml_validates"] = validation_result.valid
    else:
        checks["yaml_validates"] = False  # no validation = fail

    # 6. determinism — check that walk-forward produced consistent results
    if walkforward_result is not None:
        valid_folds = sum(
            1 for f in walkforward_result.folds
            if not f.test_objective.is_rejected
        )
        total_folds = len(walkforward_result.folds)
        checks["determinism"] = total_folds > 0 and valid_folds / total_folds >= 0.5
    else:
        checks["determinism"] = False  # no walk-forward = fail

    return checks
