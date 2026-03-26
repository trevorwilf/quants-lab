"""Shared finalist validation for pipeline and notebook paths."""
import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import numpy as np

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition

logger = logging.getLogger(__name__)


@dataclass
class FinalistValidationResult:
    """Complete result of finalist validation."""
    config: SimConfig
    dev_metrics: Metrics
    dev_objective: ObjectiveDecomposition
    stop_ship_checks: Dict[str, bool]
    all_passed: bool
    yaml_path: str
    report_path: str
    output_dir: str
    selection_mode: str = "strict"  # for compatibility


def validate_finalist(
    *,
    study_name: str,
    connector: str,
    trading_pair: str,
    interval: str,
    full_candles: np.ndarray,
    dataset_hash: str,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    study,
    best_trial,
    ranked_trials: list,
    reference_price: float,
    objective_version: int = 2,
    fixed_quote: Optional[float] = 100.0,
    train_days: float = 42.0,
    test_days: float = 14.0,
    step_days: float = 14.0,
    holdout_fraction: float = 0.20,
    reserve_recent_days: int = 28,
    top_k: int = 5,
    run_stress: bool = True,
    run_sensitivity: bool = True,
    run_recent_window: bool = True,
    search_controller_compat: bool = False,
    validation_controller_compat: bool = True,
    output_dir: str = "artifacts",
    run_id: str = "",
    seed: int = 42,
    export_params=None,
) -> FinalistValidationResult:
    """Validate a finalist candidate with full strict checks.

    This is the shared contract used by both the pipeline runner and notebooks.
    It performs the following steps:

    1. Split dataset into dev / holdout / recent-release slices
    2. Canonicalize best trial params
    3. Compute dev metrics and objective
    4. Run walk-forward cross-validation
    5. Evaluate holdout with top-k candidates
    6. Run stress tests
    7. Compute sensitivity analysis
    8. Evaluate recent release window
    9. Check feature parity with frozen fixtures
    10. Cluster analysis of top-k
    11. Export YAML config
    12. Validate exported YAML
    13. Run stop-ship checks
    14. Write artifacts (report, JSON sidecar, rejection marker)
    """
    from dataclasses import replace as _replace
    from pmm_lab.objective.dataset_split import split_for_release_gate
    from pmm_lab.optuna.canonicalizer import canonicalize_params
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.objective.objective import (
        objective_v1, objective_v2, ObjectiveWeights, ObjectiveWeightsV2,
    )
    from pmm_lab.objective.walkforward import run_walk_forward
    from pmm_lab.objective.holdout import evaluate_holdout
    from pmm_lab.objective.stress import run_stress_tests
    from pmm_lab.optuna.sensitivity import compute_sensitivity
    from pmm_lab.optuna.clustering import analyze_top_k
    from pmm_lab.export.hb_yaml import export_yaml, ExportParams
    from pmm_lab.export.validate_export import validate_yaml_file
    from pmm_lab.report.report_md import run_stop_ship_checks, generate_report
    from pmm_lab.data.hashing import hash_candles
    from pmm_lab.data.candles import validate_candles

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Split dataset
    slices = split_for_release_gate(
        full_candles, recent_days=reserve_recent_days,
        holdout_fraction=holdout_fraction,
        min_pre_release_bars=200, min_holdout_bars=50,
    )
    dev_candles = slices.dev_candles
    holdout_candles = slices.holdout_candles
    dev_hash = hash_candles(dev_candles)

    # 2. Canonicalize best params
    best_params = dict(best_trial.params)
    if fixed_quote is not None:
        best_params["total_amount_quote"] = fixed_quote
    best_config, reject = canonicalize_params(
        best_params, pair_rules, reference_price
    )
    if best_config is None:
        raise ValueError(f"Best trial failed canonicalization: {reject}")

    val_config = _replace(best_config, controller_compat=validation_controller_compat)

    # 3. Dev metrics
    runner = CandleSimRunner(val_config, pair_rules)
    dev_signals = runner.compute_signals(dev_candles)
    sim_result = runner.run_with_signals(dev_candles, dev_signals)
    dev_metrics = compute_metrics(
        sim_result, val_config.total_amount_quote, dev_candles, bar_interval_seconds
    )

    if objective_version == 2:
        dev_objective = objective_v2(dev_metrics, ObjectiveWeightsV2())
    else:
        dev_objective = objective_v1(dev_metrics)

    # 4. Walk-forward
    wf_result = run_walk_forward(
        dev_candles, val_config, pair_rules, bar_interval_seconds, dev_hash,
        train_days=train_days, test_days=test_days, step_days=step_days,
        objective_version=objective_version, include_train_metrics=False,
        precomputed_signals=dev_signals,
    )

    # 5. Holdout (exported config = candidate 0)
    holdout_candidates = [(val_config, best_trial.value or 0.0)]
    for t in ranked_trials[1:top_k]:
        p = dict(t.params)
        if fixed_quote is not None:
            p["total_amount_quote"] = fixed_quote
        cfg, rej = canonicalize_params(p, pair_rules, reference_price)
        if cfg is not None:
            cfg = _replace(cfg, controller_compat=validation_controller_compat)
            holdout_candidates.append((cfg, t.value or 0.0))

    holdout_report = evaluate_holdout(
        holdout_candles, holdout_candidates, pair_rules, bar_interval_seconds,
        run_stress=run_stress, objective_version=objective_version,
        full_candles=slices.pre_release_candles,
        holdout_start_idx=slices.holdout_start_idx_in_pre_release,
    )

    # 6. Stress
    stress_report = None
    if run_stress:
        stress_report = run_stress_tests(
            dev_candles, val_config, pair_rules, bar_interval_seconds,
            objective_version=objective_version,
            precomputed_signals=dev_signals,
            baseline_result=sim_result,
            baseline_metrics=dev_metrics,
            baseline_objective=dev_objective,
        )

    # 7. Sensitivity
    sensitivity_penalty = 0.0
    sens_report = None
    if run_sensitivity:
        sens_report = compute_sensitivity(
            best_params, dev_candles, pair_rules, bar_interval_seconds,
            reference_price,
            objective_version=objective_version,
            controller_compat=validation_controller_compat,
        )
        sensitivity_penalty = sens_report.sensitivity_penalty

    # 8. Recent window on untouched release slice
    recent_window_result = None
    if run_recent_window and len(slices.recent_release_candles) > 0:
        from pmm_lab.objective.recent_window import evaluate_recent_window
        recent_window_result = evaluate_recent_window(
            full_candles, val_config, pair_rules, bar_interval_seconds,
            recent_days=reserve_recent_days, run_stress=run_stress,
            objective_version=objective_version,
        )

    # 9. Parity
    parity_result = None
    long_parity_result = None
    try:
        from pmm_lab.parity.feature_parity import check_feature_parity_frozen
        from pmm_lab.parity.fixtures import load_frozen_fixture
        fixture_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "fixtures" / "short_100bar_compat"
        )
        if fixture_dir.is_dir():
            fixture = load_frozen_fixture(str(fixture_dir))
            parity_result = check_feature_parity_frozen(
                fixture.candles, fixture.expected_features, fixture.config_params
            )
        long_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "fixtures" / "long_500bar_compat"
        )
        if long_dir.is_dir():
            long_fixture = load_frozen_fixture(str(long_dir))
            long_parity_result = check_feature_parity_frozen(
                long_fixture.candles, long_fixture.expected_features,
                long_fixture.config_params,
            )
    except Exception as e:
        logger.warning("Parity check failed: %s", e)

    # 10. Clustering
    cluster_report = analyze_top_k(study, k=top_k)

    # 11. Export
    if export_params is None:
        export_params = ExportParams(
            connector_name=connector, trading_pair=trading_pair,
            candles_connector=connector, candles_trading_pair=trading_pair,
            interval=interval,
        )
    yaml_path = str(out_path / "config.yml")
    export_yaml(val_config, yaml_path, export_params)

    # 12. Validate YAML
    audit = validate_candles(full_candles, interval, strict=False)
    validation_result = validate_yaml_file(yaml_path)

    # 13. Stop-ship
    stop_ship = run_stop_ship_checks(
        best_metrics=dev_metrics, best_objective=dev_objective,
        walkforward_result=wf_result, stress_report=stress_report,
        dataset_audit=audit, validation_result=validation_result,
        holdout_report=holdout_report, sensitivity_penalty=sensitivity_penalty,
        recent_window_result=recent_window_result,
        parity_result=parity_result, cluster_report=cluster_report,
        long_parity_result=long_parity_result,
    )
    all_passed = all(stop_ship.values())

    # 14. Write artifacts
    if all_passed:
        deploy_dir = out_path / "deploy"
    else:
        deploy_dir = out_path / "rejected"
    deploy_dir.mkdir(parents=True, exist_ok=True)

    # Report
    dataset_summary = {
        "connector": connector, "trading_pair": trading_pair,
        "interval": interval, "total_bars": len(full_candles),
        "dev_bars": len(dev_candles), "holdout_bars": len(holdout_candles),
        "recent_bars": len(slices.recent_release_candles),
        "dataset_hash": dataset_hash[:16],
    }
    report_path = str(out_path / "report.md")
    generate_report(
        study_name=study_name, dataset_summary=dataset_summary,
        best_params=best_params, best_metrics=dev_metrics,
        best_objective=dev_objective, walkforward_result=wf_result,
        stress_report=stress_report, stop_ship_checks=stop_ship,
        holdout_report=holdout_report, output_path=report_path,
    )

    # JSON sidecar
    json_path = str(out_path / "report.json")
    json_data = {
        "study_name": study_name, "connector": connector,
        "trading_pair": trading_pair, "interval": interval,
        "run_id": run_id, "all_passed": all_passed,
        "stop_ship_checks": stop_ship,
        "dev_pnl_pct": dev_metrics.pnl_pct,
        "dev_sharpe": dev_metrics.sharpe,
        "dev_trade_count": dev_metrics.trade_count,
        "wf_fold_count": len(wf_result.folds),
        "holdout_passed": holdout_report.exported_holdout_passed,
        "stress_worst": stress_report.worst_score if stress_report else None,
        "sensitivity_penalty": sensitivity_penalty,
        "dataset_bars": len(full_candles),
        "dev_bars": len(dev_candles),
        "recent_bars": len(slices.recent_release_candles),
    }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2, default=str)

    if not all_passed:
        marker = deploy_dir / "REJECTION_REASON.txt"
        failed = [k for k, v in stop_ship.items() if not v]
        marker.write_text(
            f"Failed checks: {', '.join(failed)}\n"
            f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        )

    return FinalistValidationResult(
        config=val_config, dev_metrics=dev_metrics,
        dev_objective=dev_objective, stop_ship_checks=stop_ship,
        all_passed=all_passed, yaml_path=yaml_path,
        report_path=report_path, output_dir=str(out_path),
    )
