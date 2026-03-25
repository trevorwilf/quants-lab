"""
Full pipeline runner.

Orchestrates the complete optimization-to-deployment workflow:
1. Load and validate candle data
2. Split holdout
3. Run Optuna optimization on development data
4. Walk-forward cross-validation on development data
5. Holdout evaluation
6. Stress testing
7. Sensitivity analysis (on top candidate)
8. Top-k clustering analysis
9. Export YAML + create deployment package
10. Generate report + stop-ship checks

Usage:
    result = run_full_pipeline(
        connector="nonkyc", trading_pair="XMR-USDT", interval="5m",
        n_trials=200, output_dir="artifacts/XMR_USDT_5m",
    )
    if result.stop_ship_passed:
        print(f"Ready to deploy: {result.package_dir}")
"""

import logging
import os
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.data.mongo import MongoCandleLoader

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    # Identity
    study_name: str
    connector: str
    trading_pair: str
    interval: str

    # Timing
    started_at: str
    completed_at: str
    elapsed_seconds: float

    # Data
    total_bars: int
    dev_bars: int
    holdout_bars: int
    dataset_hash: str

    # Optimization
    n_trials: int
    best_trial_number: int
    best_score: float
    objective_version: int

    # Validation
    wf_aggregate_score: float
    wf_fold_count: int
    holdout_score: float
    holdout_passed: bool
    stress_worst_score: float
    sensitivity_penalty: float
    top_k_clustered: bool

    # Stop-ship
    stop_ship_checks: Dict[str, bool]
    stop_ship_passed: bool

    # Deployability
    deployable: bool = False          # True only if stop-ship passed

    # Output paths
    package_dir: Optional[str] = None
    report_path: Optional[str] = None
    yaml_path: Optional[str] = None


def run_full_pipeline(
    connector: str = "nonkyc",
    trading_pair: str = "XMR-USDT",
    interval: str = "5m",
    n_trials: int = 200,
    n_jobs: int = 1,  # Default to 1; use process-based workers for real parallelism
    output_dir: str = "artifacts",
    study_name: Optional[str] = None,
    holdout_fraction: float = 0.20,
    objective_version: int = 2,
    fixed_quote: float = 100.0,
    train_days: float = 42.0,
    test_days: float = 14.0,
    step_days: float = 14.0,
    top_k: int = 5,
    run_stress: bool = True,
    run_sensitivity: bool = True,
    run_recent_window: bool = True,
    mongo_loader_kwargs: Optional[Dict[str, Any]] = None,
    certified: bool = False,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
    search_controller_compat: bool = True,
    validation_controller_compat: bool = True,
) -> PipelineResult:
    """Run the full optimization-to-deployment pipeline.

    Parameters
    ----------
    connector : str
        Exchange connector name.
    trading_pair : str
        Trading pair.
    interval : str
        Candle interval.
    n_trials : int
        Number of Optuna trials.
    n_jobs : int
        Parallel jobs for Optuna.
    output_dir : str
        Base output directory.
    study_name : str, optional
        Study name. Auto-generated if None.
    holdout_fraction : float
        Fraction of data for holdout.
    objective_version : int
        1 or 2.
    fixed_quote : float
        Fixed quote budget (v2 only).
    train_days, test_days, step_days : float
        Walk-forward parameters.
    top_k : int
        Number of top candidates for holdout + clustering.
    run_stress : bool
        Whether to run stress tests.
    run_sensitivity : bool
        Whether to run sensitivity analysis on best candidate.
    mongo_loader_kwargs : dict, optional
        Extra kwargs for MongoCandleLoader.

    Returns
    -------
    PipelineResult
    """
    from pmm_lab.config.params import DataQuery, PairRules
    from pmm_lab.config.defaults import INTERVAL_SECONDS
    from pmm_lab.data.candles import validate_candles
    from pmm_lab.data.hashing import hash_candles
    from pmm_lab.objective.holdout import split_holdout, evaluate_holdout
    from pmm_lab.objective.stress import run_stress_tests
    from pmm_lab.objective.walkforward import run_walk_forward
    from pmm_lab.optuna.study import create_study
    from pmm_lab.optuna.objective_wrapper import create_objective
    from pmm_lab.optuna.canonicalizer import canonicalize_params
    from pmm_lab.optuna.sensitivity import compute_sensitivity
    from pmm_lab.optuna.clustering import analyze_top_k
    from pmm_lab.export.hb_yaml import export_yaml, ExportParams
    from pmm_lab.deploy.package import create_deployment_package, save_deployment_package
    from pmm_lab.report.report_md import generate_report, run_stop_ship_checks
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.utils.reproducibility import seed_everything, save_environment_snapshot, get_environment_snapshot, compute_snapshot_hash

    # Certified mode: override n_jobs for determinism
    if certified:
        n_jobs = 1
        logger.info("  Certified mode: forcing n_jobs=1 for determinism")

    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.time()

    # Auto-generate study name
    if study_name is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        study_name = f"{connector}_{trading_pair}_{interval}_{ts}"

    # Setup output
    out_dir = Path(output_dir) / study_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Seed for reproducibility
    seed_everything(42)
    snapshot = get_environment_snapshot(seed=42)
    env_hash = compute_snapshot_hash(snapshot)
    save_environment_snapshot(str(out_dir / "environment.json"), seed=42)

    logger.info("=== Pipeline: %s ===", study_name)

    # ---- Step 1: Load data ----
    logger.info("Step 1: Loading data")
    loader_kwargs = mongo_loader_kwargs or {}
    loader = MongoCandleLoader(**loader_kwargs)
    query = DataQuery(connector=connector, trading_pair=trading_pair, interval=interval,
                      start_ts=start_ts, end_ts=end_ts)
    candles = loader.load_range(query)
    bar_interval = INTERVAL_SECONDS[interval]

    _dup_count = getattr(loader, 'last_raw_duplicate_count', 0)
    if isinstance(_dup_count, int) and _dup_count > 0:
        logger.warning("  Raw data had %d duplicate timestamps (removed before audit)",
                       _dup_count)

    audit = validate_candles(candles, interval, strict=True)
    if not audit.passed_strict:
        raise ValueError(f"Data audit failed: {audit}")

    dataset_hash = hash_candles(candles)
    logger.info("  Loaded %d bars, hash=%s", len(candles), dataset_hash[:16])

    # ---- Step 2: Holdout split ----
    logger.info("Step 2: Holdout split (%.0f%%)", holdout_fraction * 100)
    dev_candles, holdout_candles = split_holdout(candles, holdout_fraction)
    logger.info("  Dev: %d bars, Holdout: %d bars", len(dev_candles), len(holdout_candles))

    # ---- Step 3: Resolve pair rules ----
    rules_data = load_exchange_rules()
    pair_rules = resolve_pair_rules(rules_data, connector, trading_pair)
    reference_price = float(np.median(dev_candles["close"]))

    # ---- Step 4: Optimize ----
    logger.info("Step 4: Optimization (%d trials, %d jobs)", n_trials, n_jobs)
    dev_hash = hash_candles(dev_candles)
    study = create_study(study_name=study_name)
    if search_controller_compat != validation_controller_compat:
        logger.info(
            "  NOTE: Search uses controller_compat=%s, validation uses controller_compat=%s. "
            "Candidates will be re-scored in validation mode.",
            search_controller_compat, validation_controller_compat,
        )

    from pmm_lab.optuna.dispatcher import run_optimization_dispatch
    from pmm_lab.optuna.storage import get_storage_url

    factory_kwargs = dict(
        candles=dev_candles,
        pair_rules=pair_rules,
        bar_interval_seconds=bar_interval,
        dataset_hash=dev_hash,
        reference_price=reference_price,
        run_stress=run_stress,
        objective_version=objective_version,
        fixed_quote=fixed_quote,
        train_days=train_days,
        test_days=test_days,
        step_days=step_days,
        controller_compat=search_controller_compat,
    )
    study = run_optimization_dispatch(
        study=study,
        study_name=study_name,
        objective_factory=create_objective,
        factory_kwargs=factory_kwargs,
        n_trials=n_trials,
        n_jobs=n_jobs,
        certified=certified,
        storage_url=get_storage_url(),
    )
    logger.info("  Optimization complete: %d trials", len(study.trials))

    # Guard against zero completed trials
    import optuna
    completed_trials = [
        t for t in study.trials
        if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None
    ]
    if not completed_trials:
        # Build a non-deployable result instead of crashing
        logger.error("  No completed trials — optimization produced no usable results")
        elapsed = time.time() - t0
        completed_at = datetime.now(timezone.utc).isoformat()
        return PipelineResult(
            study_name=study_name,
            connector=connector, trading_pair=trading_pair, interval=interval,
            started_at=started_at, completed_at=completed_at, elapsed_seconds=elapsed,
            total_bars=len(candles), dev_bars=len(dev_candles), holdout_bars=len(holdout_candles),
            dataset_hash=dataset_hash,
            n_trials=n_trials, best_trial_number=-1,
            best_score=float("-inf"), objective_version=objective_version,
            wf_aggregate_score=0.0, wf_fold_count=0,
            holdout_score=0.0, holdout_passed=False,
            stress_worst_score=0.0, sensitivity_penalty=0.0,
            top_k_clustered=False,
            stop_ship_checks={"no_completed_trials": False},
            stop_ship_passed=False,
            deployable=False,
            package_dir=None, report_path=None, yaml_path=None,
        )

    best_trial = max(completed_trials, key=lambda t: t.value)
    logger.info("  Best trial #%d, score=%.4f", best_trial.number, best_trial.value)

    # ---- Step 5: Canonicalize best config ----
    best_params = dict(best_trial.params)  # COPY to avoid mutating trial object
    if fixed_quote is not None:
        best_params["total_amount_quote"] = fixed_quote
    best_config, reject = canonicalize_params(best_params, pair_rules, reference_price)
    if best_config is None:
        raise ValueError(f"Best trial failed canonicalization: {reject}")

    # ---- Step 6: Full-dataset metrics ----
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.objective.objective import objective_v1, objective_v2, ObjectiveWeights
    from dataclasses import replace as _replace
    from pmm_lab.objective.signal_cache import SharedSignalCache

    # Shared signal cache across pipeline steps
    _shared_cache = SharedSignalCache()

    # Apply validation controller_compat setting
    val_config = _replace(best_config, controller_compat=validation_controller_compat)
    _step6_signals = _shared_cache.get_or_compute(val_config, "dev", dev_candles, pair_rules)
    runner = CandleSimRunner(val_config, pair_rules)
    sim_result = runner.run_with_signals(dev_candles, _step6_signals)
    metrics = compute_metrics(sim_result, val_config.total_amount_quote, dev_candles, bar_interval)

    if objective_version == 2:
        from pmm_lab.objective.objective import ObjectiveWeightsV2
        obj_decomp = objective_v2(metrics, ObjectiveWeightsV2())
    else:
        obj_decomp = objective_v1(metrics)

    # ---- Step 7: Walk-forward ----
    logger.info("Step 7: Walk-forward validation")
    wf_result = run_walk_forward(
        dev_candles, val_config, pair_rules, bar_interval, dev_hash,
        train_days=train_days, test_days=test_days, step_days=step_days,
        objective_version=objective_version,
        include_train_metrics=False,
        precomputed_signals=_step6_signals,
    )
    wf_pnls = [f.test_metrics.pnl_pct for f in wf_result.folds]
    wf_sharpes = [f.test_metrics.sharpe for f in wf_result.folds]
    wf_median_pnl = float(np.median(wf_pnls)) if wf_pnls else 0.0
    wf_median_sharpe = float(np.median(wf_sharpes)) if wf_sharpes else 0.0
    logger.info("  WF aggregate=%.4f, %d folds", wf_result.aggregate_score, len(wf_result.folds))

    # ---- Step 8: Holdout ----
    logger.info("Step 8: Holdout evaluation")
    # Evaluate holdout ONLY on the exported config to prevent config mismatch
    # best_config was already canonicalized from the dev winner above
    holdout_candidates = [(val_config, best_trial.value or 0.0)]

    # Optionally evaluate additional top-k for diagnostic purposes only
    import optuna as _optuna
    _completed = [t for t in study.trials if t.state == _optuna.trial.TrialState.COMPLETE]
    _completed.sort(key=lambda t: t.value if t.value is not None else float('-inf'), reverse=True)
    for t in _completed[1:top_k]:  # skip rank 0, already added
        p = dict(t.params)
        if fixed_quote is not None:
            p["total_amount_quote"] = fixed_quote
        cfg, rej = canonicalize_params(p, pair_rules, reference_price)
        if cfg is not None:
            cfg = _replace(cfg, controller_compat=validation_controller_compat)
            holdout_candidates.append((cfg, t.value or 0.0))

    holdout_report = evaluate_holdout(
        holdout_candles, holdout_candidates, pair_rules, bar_interval,
        run_stress=run_stress, objective_version=objective_version,
        full_candles=candles,
        holdout_start_idx=len(dev_candles),
        shared_signal_cache=_shared_cache,
        dataset_key="full",
    )
    # The exported config is always candidate index 0
    logger.info("  Holdout: exported_score=%.4f, exported_passed=%s, best_rank=%d",
                holdout_report.exported_holdout_score,
                holdout_report.exported_holdout_passed,
                holdout_report.best_holdout_rank)

    # ---- Step 9: Stress ----
    stress_report = None
    stress_worst = 0.0
    if run_stress:
        logger.info("Step 9: Stress testing")
        stress_report = run_stress_tests(dev_candles, val_config, pair_rules, bar_interval,
                                          objective_version=objective_version,
                                          precomputed_signals=_step6_signals,
                                          baseline_result=sim_result,
                                          baseline_metrics=metrics,
                                          baseline_objective=obj_decomp)
        stress_worst = stress_report.worst_score
        logger.info("  Worst scenario: %s (%.4f)", stress_report.worst_scenario, stress_worst)

    # ---- Step 10: Sensitivity ----
    sensitivity_penalty = 0.0
    if run_sensitivity:
        logger.info("Step 10: Sensitivity analysis")
        sens_report = compute_sensitivity(
            best_params, dev_candles, pair_rules, bar_interval, reference_price,
            objective_version=objective_version,
            controller_compat=validation_controller_compat,
            shared_signal_cache=_shared_cache,
            dataset_key="dev",
        )
        sensitivity_penalty = sens_report.sensitivity_penalty
        logger.info("  Sensitivity penalty=%.4f", sensitivity_penalty)

    # ---- Step 10b: Recent-window evaluation ----
    recent_window_result = None
    if run_recent_window:
        logger.info("Step 10b: Recent-window evaluation")
        from pmm_lab.objective.recent_window import evaluate_recent_window
        recent_window_result = evaluate_recent_window(
            candles, val_config, pair_rules, bar_interval,  # full candles, NOT dev_candles
            recent_days=28,
            run_stress=run_stress,
            objective_version=objective_version,
            shared_signal_cache=_shared_cache,
            dataset_key="full",
        )
        logger.info("  Recent window uses full dataset (last timestamp: %d)",
                    int(candles["timestamp"][-1]))
        logger.info("  Recent 28d: passed=%s, reason=%s",
                    recent_window_result.passed, recent_window_result.reason)

    # ---- Step 10c: Frozen feature parity ----
    logger.info("Step 10c: Frozen feature parity check")
    from pmm_lab.parity.feature_parity import check_feature_parity_frozen
    from pmm_lab.parity.fixtures import load_frozen_fixture
    from pathlib import Path as _Path

    parity_result = None
    fixture_dir = _Path(__file__).resolve().parent.parent.parent / "fixtures" / "short_100bar_compat"
    if fixture_dir.is_dir():
        try:
            fixture = load_frozen_fixture(str(fixture_dir))
            parity_result = check_feature_parity_frozen(
                fixture.candles, fixture.expected_features, fixture.config_params,
            )
            logger.info("  Frozen parity: passed=%s, max_abs_diff=%.2e",
                        parity_result.passed, parity_result.max_abs_diff)
        except Exception as e:
            logger.warning("  Frozen parity check failed: %s", e)
    else:
        logger.warning("  Frozen fixture not found at %s — skipping parity", fixture_dir)

    # Long-history parity check (catches divergence beyond max_records window)
    long_fixture_dir = _Path(__file__).resolve().parent.parent.parent / "fixtures" / "long_500bar_compat"
    long_parity_result = None
    if long_fixture_dir.is_dir():
        try:
            long_fixture = load_frozen_fixture(str(long_fixture_dir))
            long_parity_result = check_feature_parity_frozen(
                long_fixture.candles, long_fixture.expected_features, long_fixture.config_params,
            )
            logger.info("  Long-history parity: passed=%s, max_abs_diff=%.2e",
                        long_parity_result.passed, long_parity_result.max_abs_diff)
        except Exception as e:
            logger.warning("  Long-history parity check failed: %s", e)
    else:
        logger.warning("  Long fixture not found at %s — skipping", long_fixture_dir)

    # ---- Step 11: Clustering ----
    logger.info("Step 11: Top-k clustering")
    cluster_report = analyze_top_k(study, k=top_k)
    logger.info("  Clustered=%s, mean CV=%.3f", cluster_report.is_clustered, cluster_report.mean_cv)

    # ---- Step 12: Export ----
    logger.info("Step 12: Export + package")
    export_params = ExportParams(
        connector_name=connector,
        trading_pair=trading_pair,
        candles_connector=connector,
        candles_trading_pair=trading_pair,
        interval=interval,
    )
    yaml_path = str(out_dir / "config.yml")
    export_yaml(val_config, yaml_path, export_params)

    # Validate the export
    from pmm_lab.export.validate_export import validate_yaml_file
    validation_result = validate_yaml_file(yaml_path)

    # ---- Step 13: Stop-ship checks ----
    stop_ship = run_stop_ship_checks(
        best_metrics=metrics,
        best_objective=obj_decomp,
        walkforward_result=wf_result,
        stress_report=stress_report,
        dataset_audit=audit,
        validation_result=validation_result,
        holdout_report=holdout_report,
        sensitivity_penalty=sensitivity_penalty,
        recent_window_result=recent_window_result,
        parity_result=parity_result,
        cluster_report=cluster_report,
        long_parity_result=long_parity_result,
    )
    all_passed = all(stop_ship.values())
    logger.info("  Stop-ship: %s (%d/%d passed)",
                "ALL PASS" if all_passed else "FAIL",
                sum(stop_ship.values()), len(stop_ship))

    # ---- Step 14: Deployment package ----
    if all_passed:
        package_dir = str(out_dir / "deploy")
        logger.info("  Stop-ship PASSED — writing deployment package")
    else:
        package_dir = str(out_dir / "rejected")
        logger.warning("  Stop-ship FAILED — writing to rejected/ (NOT deployable)")

    package = create_deployment_package(
        config=val_config, metrics=metrics, objective=obj_decomp,
        study_name=study_name, dataset_hash=dataset_hash,
        dataset_bars=len(candles), export_params=export_params,
        objective_version=objective_version,
        wf_median_pnl=wf_median_pnl, wf_median_sharpe=wf_median_sharpe,
        wf_fold_count=len(wf_result.folds),
        holdout_pnl_pct=(
            holdout_report.candidates[0].metrics.pnl_pct
            if holdout_report.candidates
            else None
        ),
        holdout_score=(
            holdout_report.candidates[0].objective.raw_score
            if holdout_report.candidates
            else 0.0
        ),
        stress_worst_score=stress_worst,
        sensitivity_penalty=sensitivity_penalty,
        stop_ship_checks=stop_ship,
        environment_hash=env_hash,
        certified=certified,
        n_jobs=n_jobs,
        dev_dataset_hash=dev_hash,
        holdout_fraction=holdout_fraction,
        holdout_bars=len(holdout_candles),
        start_ts=start_ts,
        end_ts=end_ts,
    )
    save_deployment_package(package, package_dir)

    if not all_passed:
        marker = Path(package_dir) / "STOP_SHIP_FAILED.txt"
        failed_checks = [k for k, v in stop_ship.items() if not v]
        marker.write_text(
            f"This config FAILED stop-ship checks and must NOT be deployed.\n"
            f"Failed checks: {', '.join(failed_checks)}\n"
            f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        )

    # ---- Step 15: Report ----
    logger.info("Step 15: Generating report")
    dataset_summary = {
        "connector": connector, "trading_pair": trading_pair, "interval": interval,
        "total_bars": len(candles), "dev_bars": len(dev_candles),
        "holdout_bars": len(holdout_candles), "dataset_hash": dataset_hash[:16],
    }
    report_path = str(out_dir / "report.md")
    report_text = generate_report(
        study_name=study_name, dataset_summary=dataset_summary,
        best_params=best_params, best_metrics=metrics,
        best_objective=obj_decomp, walkforward_result=wf_result,
        stress_report=stress_report, stop_ship_checks=stop_ship,
        holdout_report=holdout_report, output_path=report_path,
    )

    elapsed = time.time() - t0
    completed_at = datetime.now(timezone.utc).isoformat()
    logger.info("=== Pipeline complete: %.1fs ===", elapsed)

    return PipelineResult(
        study_name=study_name,
        connector=connector, trading_pair=trading_pair, interval=interval,
        started_at=started_at, completed_at=completed_at, elapsed_seconds=elapsed,
        total_bars=len(candles), dev_bars=len(dev_candles), holdout_bars=len(holdout_candles),
        dataset_hash=dataset_hash,
        n_trials=n_trials, best_trial_number=best_trial.number,
        best_score=best_trial.value, objective_version=objective_version,
        wf_aggregate_score=wf_result.aggregate_score, wf_fold_count=len(wf_result.folds),
        holdout_score=holdout_report.exported_holdout_score, holdout_passed=holdout_report.exported_holdout_passed,
        stress_worst_score=stress_worst, sensitivity_penalty=sensitivity_penalty,
        top_k_clustered=cluster_report.is_clustered,
        stop_ship_checks=stop_ship, stop_ship_passed=all_passed,
        deployable=all_passed,
        package_dir=package_dir, report_path=report_path, yaml_path=yaml_path,
    )
