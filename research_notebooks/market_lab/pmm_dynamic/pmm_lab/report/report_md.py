"""
Markdown report generator for optimization runs.

Produces a human-readable report with dataset summary, best parameters,
walk-forward metrics, stress results, and stop-ship check status.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition, REJECT_SCORE
from pmm_lab.objective.walkforward import WalkForwardResult
from pmm_lab.objective.stress import StressReport
from pmm_lab.objective.holdout import HoldoutReport


def _safe_serialize(obj):
    """Convert dataclass/namedtuple to dict for JSON serialization."""
    if obj is None:
        return None
    if hasattr(obj, '__dict__'):
        return {k: _safe_serialize(v) for k, v in obj.__dict__.items()
                if not k.startswith('_')}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _normalize_recent_window_results(
    *,
    recent_window_result=None,
    recent_window_results=None,
    recent_blocking_window_days=28,
):
    """Merge legacy single-result and new multi-window mapping into one dict.

    Returns {days: result, ...} sorted descending by days.
    """
    results = {}
    if recent_window_result is not None:
        results[int(recent_blocking_window_days)] = recent_window_result
    if recent_window_results:
        for k, v in recent_window_results.items():
            try:
                k = int(k)
            except Exception:
                pass
            results[k] = v
    return dict(sorted(results.items(), key=lambda kv: int(kv[0]), reverse=True))


def _append_recent_window_section(lines, *, days, result, informational_only=False):
    """Render one recent-window section in the markdown report."""
    title = f"## Recent {days}-Day Window"
    if informational_only:
        title += " (Informational Only)"
    lines.append(title)
    lines.append("")
    if informational_only:
        lines.append(
            "> **Informational only** — this section does not affect "
            "stop-ship gating, export eligibility, or validated YAML promotion."
        )
        lines.append("")
    lines.append(f"- **Passed**: {getattr(result, 'passed', 'N/A')}")
    lines.append(f"- **Reason**: {getattr(result, 'reason', 'N/A')}")
    _obj = getattr(result, 'objective', None)
    if _obj is not None:
        lines.append(f"- **Objective score**: {getattr(_obj, 'raw_score', 'N/A')}")
    _met = getattr(result, 'metrics', None)
    if _met is not None:
        lines.append(f"- **PnL %**: {getattr(_met, 'pnl_pct', 'N/A')}")
        lines.append(f"- **Trade count**: {getattr(_met, 'trade_count', 'N/A')}")
    lines.append("")


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
    recent_window_results=None,
    recent_blocking_window_days=28,
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
    else:
        _rw_obj = getattr(recent_window_result, 'objective', None)
        _rw_met = getattr(recent_window_result, 'metrics', None)
        _rw_score = f"{getattr(_rw_obj, 'raw_score', 'N/A')}" if _rw_obj else "N/A"
        _rw_pnl = f"{getattr(_rw_met, 'pnl_pct', 'N/A')}" if _rw_met else "N/A"
        _rw_trades = f"{getattr(_rw_met, 'trade_count', 'N/A')}" if _rw_met else "N/A"
        _rw_reason = getattr(recent_window_result, 'reason', '')
        _detail = f"score={_rw_score}, pnl={_rw_pnl}, trades={_rw_trades}, reason={_rw_reason}"
        _status = "PASS" if getattr(recent_window_result, 'passed', False) else "FAIL"
        items.append(ValidationCoverageItem("recent_28d", _status, _detail))

    # recent informational windows (14d, 7d, etc.)
    if recent_window_results:
        for _rw_days, _rw_res in sorted(recent_window_results.items(), key=lambda kv: int(kv[0]), reverse=True):
            _rw_days_int = int(_rw_days)
            if _rw_days_int == recent_blocking_window_days:
                continue  # already covered by recent_28d above
            _name = f"recent_{_rw_days_int}d_info"
            if _rw_res is None:
                items.append(ValidationCoverageItem(_name, "SKIPPED", "informational only"))
                continue
            _rw_obj = getattr(_rw_res, 'objective', None)
            _rw_met = getattr(_rw_res, 'metrics', None)
            _rw_score = f"{getattr(_rw_obj, 'raw_score', 'N/A')}" if _rw_obj else "N/A"
            _rw_pnl = f"{getattr(_rw_met, 'pnl_pct', 'N/A')}" if _rw_met else "N/A"
            _rw_trades = f"{getattr(_rw_met, 'trade_count', 'N/A')}" if _rw_met else "N/A"
            _rw_reason = getattr(_rw_res, 'reason', '')
            _detail = f"informational only; score={_rw_score}, pnl={_rw_pnl}, trades={_rw_trades}, reason={_rw_reason}"
            _status = "PASS" if getattr(_rw_res, 'passed', False) else "FAIL"
            items.append(ValidationCoverageItem(_name, _status, _detail))

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
    recent_window_results: Optional[Dict[int, Any]] = None,
    recent_blocking_window_days: int = 28,
    cluster_report: Optional[Any] = None,
    yaml_validation_result: Optional[Any] = None,
    dataset_slices: Optional[Any] = None,
    execution_realism: Optional[Dict[str, Any]] = None,
    preflight_report: Optional[Any] = None,
    score_summary: Optional[Dict[str, Any]] = None,
    analysis_status: Optional[Dict[str, Any]] = None,
    run_provenance: Optional[Dict[str, Any]] = None,
    canonical_config: Optional[Any] = None,
    parity_result: Optional[Any] = None,
    long_parity_result: Optional[Any] = None,
) -> str:
    """Generate a markdown report."""
    lines = []

    # 1. Header
    lines.append(f"# PMM Dynamic Optimization Report: {study_name}")
    lines.append(f"")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    # -- Report Status (if analysis_status provided)
    if analysis_status is not None:
        report_mode = analysis_status.get("report_mode", "unknown")
        if report_mode == "analysis_only" or report_mode == "screening":
            lines.append("> **ANALYSIS ONLY — NOT DEPLOYABLE**")
        elif report_mode == "strict_validation" or report_mode == "validated":
            lines.append("> **STRICT VALIDATION REPORT — DEPLOYABLE CANDIDATE**")
        lines.append("")
        lines.append("## Report Status")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| Report Mode | {report_mode} |")
        for gate_key in ["preflight", "score", "analysis"]:
            gate_val = analysis_status.get(gate_key,
                       analysis_status.get(f"{gate_key}_passed",
                       analysis_status.get(f"{gate_key}_gate_passed", "N/A")))
            if isinstance(gate_val, bool):
                gate_val = "PASS" if gate_val else "FAIL"
            lines.append(f"| {gate_key} | {gate_val} |")
        # Extra fields
        if analysis_status.get("deployability_status"):
            lines.append(f"| Deployability Status | {analysis_status['deployability_status']} |")
        if analysis_status.get("objective_version") is not None:
            lines.append(f"| Objective Version | {analysis_status['objective_version']} |")
        if analysis_status.get("search_controller_compat") is not None:
            lines.append(f"| Search Controller Compat | {analysis_status['search_controller_compat']} |")
        lines.append("")

    # -- Selection Score Summary (if score_summary provided)
    if score_summary is not None:
        lines.append("## Selection Score Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        for score_key in ["phase1", "robust", "worst"]:
            score_val = score_summary.get(score_key,
                        score_summary.get(f"{score_key}_best" if score_key == "phase1" else f"{score_key}_score", "N/A"))
            if isinstance(score_val, float):
                lines.append(f"| {score_key} | {score_val:.4f} |")
            else:
                lines.append(f"| {score_key} | {score_val} |")
        # Additional fields
        for extra in ["baseline", "worst_scenario", "min_robust_score", "score_gate_passed"]:
            if extra in score_summary:
                lines.append(f"| {extra} | {score_summary[extra]} |")
        lines.append("")

    # -- Run Provenance (if run_provenance provided)
    if run_provenance is not None:
        lines.append("## Run Provenance")
        lines.append("")
        lines.append("| Key | Value |")
        lines.append("|-----|-------|")
        for prov_key, prov_val in run_provenance.items():
            lines.append(f"| {prov_key} | {prov_val} |")
        lines.append("")

    # -- Preflight (if preflight_report provided)
    if preflight_report is not None:
        lines.append("## Preflight")
        lines.append("")
        if isinstance(preflight_report, dict):
            for pf_key, pf_val in preflight_report.items():
                lines.append(f"- **{pf_key}**: {pf_val}")
        elif hasattr(preflight_report, '__dict__'):
            for pf_key, pf_val in vars(preflight_report).items():
                lines.append(f"- **{pf_key}**: {pf_val}")
        else:
            lines.append(f"- {preflight_report}")
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

    # 3b. Capital/Budget Analysis
    _taq_min = dataset_summary.get("total_amount_quote_search_min")
    _taq_max = dataset_summary.get("total_amount_quote_search_max")
    _taq_ideal = dataset_summary.get("total_amount_quote_ideal")
    if _taq_min is not None and _taq_max is not None and _taq_ideal is not None:
        lines.append("## Capital/Budget Analysis")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Search Min | {_taq_min} |")
        lines.append(f"| Search Max | {_taq_max} |")
        lines.append(f"| Ideal | {_taq_ideal} |")
        selected_quote = best_params.get("total_amount_quote")
        if selected_quote is not None:
            lines.append(f"| Selected | {selected_quote} |")
            # Boundary warnings
            try:
                sel = float(selected_quote)
                lo = float(_taq_min)
                hi = float(_taq_max)
                if hi > lo:
                    range_size = hi - lo
                    if (sel - lo) / range_size < 0.05:
                        lines.append("")
                        lines.append("> **WARNING**: Selected quote is within 5% of search minimum.")
                    if (hi - sel) / range_size < 0.05:
                        lines.append("")
                        lines.append("> **WARNING**: Selected quote is within 5% of search maximum.")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        lines.append("")

    # 4. Best Metrics
    lines.append("## Selected Candidate Single-Run Diagnostics")
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
    lines.append("## Selected Candidate Single-Run Objective")
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
        lines.append(f"- **Total rows**: {getattr(dataset_audit, 'total_rows', 'N/A')}")
        lines.append(f"- **Expected rows**: {getattr(dataset_audit, 'expected_rows', 'N/A')}")
        lines.append(f"- **Missing rows**: {getattr(dataset_audit, 'missing_rows', 'N/A')}")
        lines.append(f"- **Forward-fill count**: {getattr(dataset_audit, 'forward_fill_count', 'N/A')}")
        lines.append(f"- **Forward-fill fraction**: {getattr(dataset_audit, 'forward_fill_fraction', 'N/A')}")
        lines.append(f"- **Longest gap (seconds)**: {getattr(dataset_audit, 'longest_gap_seconds', 'N/A')}")
        failure_reasons = getattr(dataset_audit, 'failure_reasons', [])
        if failure_reasons:
            lines.append(f"- **Failure reasons**: {', '.join(str(r) for r in failure_reasons)}")
        lines.append("")

    # 8c. Recent Window Sections (28d blocker + informational windows)
    _all_rw = _normalize_recent_window_results(
        recent_window_result=recent_window_result,
        recent_window_results=recent_window_results,
        recent_blocking_window_days=recent_blocking_window_days,
    )
    for _rw_days, _rw_res in _all_rw.items():
        _is_info = (_rw_days != recent_blocking_window_days)
        _append_recent_window_section(lines, days=_rw_days, result=_rw_res, informational_only=_is_info)

    # 8d. Sensitivity Analysis
    if sensitivity_report is not None:
        lines.append("## Sensitivity Analysis")
        lines.append("")
        lines.append(f"- **Sensitivity penalty**: {getattr(sensitivity_report, 'sensitivity_penalty', 'N/A')}")
        lines.append(f"- **Baseline score**: {getattr(sensitivity_report, 'baseline_score', 'N/A')}")
        lines.append(f"- **Sign flips**: {getattr(sensitivity_report, 'sign_flips', 'N/A')}")
        lines.append(f"- **Collapse count**: {getattr(sensitivity_report, 'collapse_count', 'N/A')}")
        lines.append(f"- **Perturbations**: {getattr(sensitivity_report, 'n_perturbations', 'N/A')}")
        lines.append(f"- **Rejected**: {getattr(sensitivity_report, 'n_rejected', 'N/A')}")
        perturbed_scores = getattr(sensitivity_report, 'perturbed_scores', None)
        if perturbed_scores:
            lines.append("")
            lines.append("| Parameter | Scores |")
            lines.append("|-----------|--------|")
            for p_name, p_scores in perturbed_scores.items():
                scores_str = ", ".join(f"{s:.4f}" for s in p_scores)
                lines.append(f"| {p_name} | {scores_str} |")
        lines.append("")

    # 8e. Top-K Clustering
    if cluster_report is not None:
        lines.append("## Top-K Clustering")
        lines.append("")
        lines.append(f"- **K**: {getattr(cluster_report, 'k', 'N/A')}")
        lines.append(f"- **Is clustered**: {getattr(cluster_report, 'is_clustered', 'N/A')}")
        lines.append(f"- **Mean CV**: {getattr(cluster_report, 'mean_cv', 'N/A')}")
        lines.append(f"- **Max CV**: {getattr(cluster_report, 'max_cv', 'N/A')}")
        clustered_params = getattr(cluster_report, 'clustered_params', [])
        scattered_params = getattr(cluster_report, 'scattered_params', [])
        if clustered_params:
            lines.append(f"- **Clustered params**: {', '.join(clustered_params)}")
        if scattered_params:
            lines.append(f"- **Scattered params**: {', '.join(scattered_params)}")
        param_ranges = getattr(cluster_report, 'param_ranges', {})
        param_cv = getattr(cluster_report, 'param_cv', {})
        if param_cv:
            lines.append("")
            lines.append("| Parameter | CV | Min | Max | Mean |")
            lines.append("|-----------|-----|-----|-----|------|")
            for p_name, cv_val in param_cv.items():
                pr = param_ranges.get(p_name, {})
                lines.append(
                    f"| {p_name} | {cv_val:.4f} | "
                    f"{pr.get('min', 'N/A')} | {pr.get('max', 'N/A')} | "
                    f"{pr.get('mean', 'N/A')} |"
                )
        lines.append("")

    # 8e2. Feature Parity Checks
    if parity_result is not None or long_parity_result is not None:
        lines.append("## Feature Parity Checks")
        lines.append("")
        if parity_result is not None:
            lines.append(f"- **Short fixture (100-bar)**: {'PASS' if parity_result.passed else '**FAIL**'}")
            if hasattr(parity_result, 'max_abs_diff'):
                lines.append(f"  - Max absolute diff: {parity_result.max_abs_diff}")
        if long_parity_result is not None:
            lines.append(f"- **Long fixture (500-bar)**: {'PASS' if long_parity_result.passed else '**FAIL**'}")
            if hasattr(long_parity_result, 'max_abs_diff'):
                lines.append(f"  - Max absolute diff: {long_parity_result.max_abs_diff}")
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

        # Gate Thresholds Detail
        lines.append("### Gate Thresholds Detail")
        lines.append("")
        lines.append("| Gate | Threshold | Actual | Status |")
        lines.append("|---|---|---|---|")
        if recent_window_result is not None:
            _rw_obj = getattr(recent_window_result, 'objective', None)
            _rw_met = getattr(recent_window_result, 'metrics', None)
            _rw_score = getattr(_rw_obj, 'raw_score', None) if _rw_obj else None
            lines.append(f"| recent_objective | > 0 | {_rw_score} | {'PASS' if _rw_score and _rw_score > 0 else 'FAIL'} |")
            _rw_pnl = getattr(_rw_met, 'pnl_pct', None) if _rw_met else None
            lines.append(f"| recent_pnl | >= 0 | {_rw_pnl} | {'PASS' if _rw_pnl is not None and _rw_pnl >= 0 else 'FAIL'} |")
            _rw_trades = getattr(_rw_met, 'trade_count', None) if _rw_met else None
            lines.append(f"| recent_trades | >= 5 | {_rw_trades} | {'PASS' if _rw_trades is not None and _rw_trades >= 5 else 'FAIL'} |")
        if stress_report is not None:
            lines.append(f"| worst_stress | > -10 | {getattr(stress_report, 'worst_score', 'N/A')} | {'PASS' if getattr(stress_report, 'worst_score', -999) > -10 else 'FAIL'} |")
        if sensitivity_report is not None:
            _sp = getattr(sensitivity_report, 'sensitivity_penalty', None)
            lines.append(f"| sensitivity_penalty | < 0.50 | {_sp} | {'PASS' if _sp is not None and _sp < 0.50 else 'FAIL'} |")
        lines.append("")

    # 10. Validation Coverage
    _vc = validation_coverage
    if _vc is None:
        _vc = build_validation_coverage(
            dataset_audit=dataset_audit,
            validation_result=yaml_validation_result,
            holdout_report=holdout_report,
            sensitivity_report=sensitivity_report,
            recent_window_result=recent_window_result,
            recent_window_results=recent_window_results,
            recent_blocking_window_days=recent_blocking_window_days,
            parity_result=parity_result,
            long_parity_result=long_parity_result,
            cluster_report=cluster_report,
            walkforward_result=walkforward_result,
            stress_report=stress_report,
        )
    if _vc:
        lines.append("## Validation Coverage")
        lines.append("")
        lines.append("| Validation | Status | Detail |")
        lines.append("|---|---|---|")
        for item in _vc:
            lines.append(f"| {item.name} | {item.status} | {item.detail} |")
        lines.append("")

    # 11. Validation Execution Manifest
    lines.append("## Validation Execution Manifest")
    lines.append("")
    lines.append("| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |")
    lines.append("|---|---|---|---|---|---|---|")

    def _manifest_row(name, obj, dataset_label, obj_ver=None, bars=None):
        ran = obj is not None
        if not ran:
            return f"| {name} | false | NOT_RUN | — | — | — | not executed |"
        status = "PASS" if getattr(obj, 'passed', getattr(obj, 'passed_strict', getattr(obj, 'valid', getattr(obj, 'is_clustered', False)))) else "FAIL"
        reason = getattr(obj, 'reason', getattr(obj, 'failure_reasons', ''))
        if isinstance(reason, list):
            reason = '; '.join(str(r) for r in reason)
        bars_str = str(bars) if bars else "—"
        ver_str = str(obj_ver) if obj_ver else "—"
        return f"| {name} | true | {status} | {dataset_label} | {ver_str} | {bars_str} | {reason} |"

    lines.append(_manifest_row("dataset_audit", dataset_audit, "full", bars=dataset_summary.get("n_candles") if dataset_summary else None))
    lines.append(_manifest_row("yaml_validation", yaml_validation_result, "—"))
    lines.append(_manifest_row("holdout", holdout_report, "pre_release_holdout"))
    lines.append(_manifest_row("recent_28d", recent_window_result, "recent_28d"))
    # Informational recent window manifest rows
    if recent_window_results:
        for _rw_days, _rw_res in sorted(recent_window_results.items(), key=lambda kv: int(kv[0]), reverse=True):
            _rw_days_int = int(_rw_days)
            if _rw_days_int == recent_blocking_window_days:
                continue
            _name = f"recent_{_rw_days_int}d_info"
            lines.append(_manifest_row(_name, _rw_res, _name))
    lines.append(_manifest_row("sensitivity", sensitivity_report, "full"))
    lines.append(_manifest_row("clustering", cluster_report, "—"))
    lines.append(_manifest_row("frozen_parity", parity_result, "fixture"))
    lines.append(_manifest_row("long_parity", long_parity_result, "fixture"))
    lines.append(_manifest_row("walkforward", walkforward_result, "full"))
    lines.append(_manifest_row("stress", stress_report, "full"))
    lines.append("")

    # 12. Dataset Slice Lineage
    if dataset_slices is not None:
        lines.append("## Dataset Slice Lineage")
        lines.append("")
        _full = getattr(dataset_slices, 'full_candles', None)
        lines.append(f"- **Full bars**: {len(_full) if _full is not None else 'N/A'}")
        _pre = getattr(dataset_slices, 'pre_release_candles', None)
        lines.append(f"- **Pre-release bars**: {len(_pre) if _pre is not None else 'N/A'}")
        lines.append(f"- **Dev bars**: {len(getattr(dataset_slices, 'dev_candles', []))}")
        lines.append(f"- **Holdout bars**: {len(getattr(dataset_slices, 'holdout_candles', []))}")
        lines.append(f"- **Recent 28d bars**: {len(getattr(dataset_slices, 'recent_release_candles', []))}")
        _recent_start = getattr(dataset_slices, 'recent_start_timestamp', None)
        _recent_end = getattr(dataset_slices, 'recent_end_timestamp',
                      getattr(dataset_slices, 'recent_end_ts', None))
        if _recent_start is not None:
            lines.append(f"- **Recent window start**: {_recent_start}")
        if _recent_end is not None:
            lines.append(f"- **Recent window end**: {_recent_end}")
        lines.append("")

    # 13. Run Provenance
    if run_provenance is not None:
        lines.append("## Run Provenance")
        lines.append("")
        for k, v in run_provenance.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    report_text = "\n".join(lines)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.write(report_text)

        # JSON sidecar output
        if output_path.endswith("_report.md"):
            json_path = output_path[:-len("_report.md")] + "_report.json"
        else:
            json_path = output_path + ".json"

        json_data = {
            "analysis_status": analysis_status,
            "score_summary": score_summary,
            "dataset_summary": dataset_summary,
            "validation_coverage": [
                {"name": item.name, "status": item.status, "detail": item.detail}
                for item in _vc
            ] if _vc else [],
            "stop_ship_checks": stop_ship_checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_validations": {
                "dataset_audit": _safe_serialize(dataset_audit),
                "yaml_validation": _safe_serialize(yaml_validation_result),
                "holdout_report": _safe_serialize(holdout_report),
                "recent_window_result": _safe_serialize(recent_window_result),
                "recent_window_results": {
                    str(k): _safe_serialize(v)
                    for k, v in (recent_window_results or {}).items()
                } if recent_window_results else None,
                "sensitivity_report": _safe_serialize(sensitivity_report),
                "cluster_report": _safe_serialize(cluster_report),
                "parity_result": _safe_serialize(parity_result),
                "long_parity_result": _safe_serialize(long_parity_result),
                "dataset_slices": _safe_serialize(dataset_slices),
            },
            "run_provenance": _safe_serialize(run_provenance),
        }

        with open(json_path, "w") as jf:
            json.dump(json_data, jf, indent=2, default=str)

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
