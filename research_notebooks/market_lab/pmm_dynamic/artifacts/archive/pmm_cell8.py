# ── Config guard: ensure configuration cell was executed ──
_required_config = [
    "VALIDATION_CONTROLLER_COMPAT", "SEARCH_CONTROLLER_COMPAT", "PHASE2_CONTROLLER_COMPAT",
    "OBJECTIVE_VERSION", "N_TRIALS", "TOP_N", "MIN_ROBUST_SCORE",
    "N_JOBS", "MIN_PHASE1_BEST_FOR_STRESS",
]
_missing = [v for v in _required_config if v not in globals()]
if _missing:
    import warnings as _w
    _w.warn(
        f"Configuration cell may not have been executed. "
        f"Missing: {', '.join(_missing)}. "
        f"Applying safe defaults — re-run all cells from the top for your custom settings.",
        stacklevel=1,
    )
    # Safe defaults so the sweep can still proceed
    if "VALIDATION_CONTROLLER_COMPAT" not in globals():
        VALIDATION_CONTROLLER_COMPAT = True
    if "SEARCH_CONTROLLER_COMPAT" not in globals():
        SEARCH_CONTROLLER_COMPAT = False
    if "PHASE2_CONTROLLER_COMPAT" not in globals():
        PHASE2_CONTROLLER_COMPAT = True
    if "OBJECTIVE_VERSION" not in globals():
        OBJECTIVE_VERSION = 2

if "REFRESH_CLOSE_MODE" not in globals():
    REFRESH_CLOSE_MODE = "keep"
if "INITIAL_BASE_BALANCE" not in globals():
    INITIAL_BASE_BALANCE = 0.0

if "RECENT_BLOCKING_WINDOW_DAYS" not in globals():
    RECENT_BLOCKING_WINDOW_DAYS = 28
if "RECENT_INFORMATIONAL_WINDOW_DAYS" not in globals():
    RECENT_INFORMATIONAL_WINDOW_DAYS = [14, 7]
if "RECENT_REPORT_WINDOW_DAYS" not in globals():
    RECENT_REPORT_WINDOW_DAYS = sorted(
        dict.fromkeys([RECENT_BLOCKING_WINDOW_DAYS] + RECENT_INFORMATIONAL_WINDOW_DAYS),
        reverse=True,
    )


from pmm_lab.data.candles import validate_candles
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.callbacks import DegeneracyCheckCallback, TrialLoggingCallback
from pmm_lab.optuna.canonicalizer import canonicalize_params
from pmm_lab.objective.stress import load_stress_scenarios
from pmm_lab.objective.stress_selection import select_best_stressed_candidate
from pmm_lab.objective.walkforward import run_walk_forward
from pmm_lab.objective.objective import REJECT_SCORE, objective_v1
from pmm_lab.export.hb_yaml import export_yaml, ExportParams
from pmm_lab.export.validate_export import validate_yaml_file
from pmm_lab.report.report_md import generate_report, run_stop_ship_checks
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.objective.recent_window import evaluate_recent_window
from pmm_lab.objective.holdout import evaluate_holdout
from pmm_lab.objective.dataset_split import split_for_release_gate
from pmm_lab.optuna.sensitivity import compute_sensitivity
from pmm_lab.optuna.clustering import analyze_top_k
from pmm_lab.parity.feature_parity import check_feature_parity_frozen
from pmm_lab.parity.fixtures import load_frozen_fixture
from dataclasses import replace as _replace

# Preload stress scenarios once (Task 4.1)
stress_scenarios = load_stress_scenarios()

rules_db = load_exchange_rules()
sweep_results = []
sweep_start = time.time()

for pair_idx, pair_info in enumerate(candidates):
    connector = pair_info["connector"]
    pair = pair_info["trading_pair"]
    interval = pair_info["interval"]
    bar_interval_seconds = INTERVAL_SECONDS[interval]

    print(f"\n{'═'*60}")
    print(f"  [{pair_idx+1}/{len(candidates)}] {connector} / {pair} / {interval}")
    print(f"{'═'*60}")

    pair_start = time.time()

    # ── Load candles ──
    try:
        _start_ts = int(pair_info["first_ts"]) if MAX_TRAINING_DAYS is not None else None
        query = DataQuery(connector=connector, trading_pair=pair, interval=interval, start_ts=_start_ts)
        candles = loader.load_range(query)
        audit = validate_candles(candles, interval=interval, strict=True)
        if not audit.passed_strict:
            print(f"  SKIP: audit failed — {audit.failure_reasons}")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "audit_fail", "robust_score": None})
            continue
        dataset_hash = hash_candles(candles)
    except Exception as e:
        print(f"  SKIP: load failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                              "status": "load_fail", "robust_score": None})
        continue


    # ── Dataset split for release gate ──
    try:
        dataset_slices = split_for_release_gate(candles, recent_days=RECENT_BLOCKING_WINDOW_DAYS, holdout_fraction=0.20, min_pre_release_bars=200, min_holdout_bars=50)
        dev_candles = dataset_slices.dev_candles
        dev_dataset_hash = hash_candles(dev_candles)
        print(f"  Split: dev={len(dev_candles)} holdout={len(dataset_slices.holdout_candles)} recent={len(dataset_slices.recent_release_candles)}")
    except ValueError as e:
        print(f"  Split failed ({e}), using full candles")
        dataset_slices = None
        dev_candles = candles
        dev_dataset_hash = dataset_hash

    # ── Exchange rules ──
    try:
        pair_rules = resolve_pair_rules(rules_db, connector, pair)
    except KeyError:
        # Fall back to connector defaults if pair-specific rules not found
        try:
            pair_rules = resolve_pair_rules(rules_db, connector, "DEFAULT")
        except KeyError:
            print(f"  SKIP: no exchange rules for {connector}/{pair}")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "no_rules", "robust_score": None})
            continue

    taker_prob = TAKER_PROBABILITY_BY_CONNECTOR.get(connector, DEFAULT_TAKER_PROBABILITY)
    ref_price = float(np.median(candles["close"]))

    # ── Auto-scale walk-forward windows ──
    dataset_days = len(candles) * bar_interval_seconds / 86400
    if dataset_days >= 120:
        train_days, test_days, step_days = 42.0, 14.0, 14.0
    elif dataset_days >= 60:
        train_days, test_days, step_days = 21.0, 7.0, 7.0
    elif dataset_days >= 28:
        train_days, test_days, step_days = 10.0, 4.0, 4.0
    else:
        print(f"  SKIP: only {dataset_days:.1f} days of data")
        sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                              "status": "insufficient_data", "robust_score": None})
        continue

    print(f"  Candles: {len(candles):,}  Days: {dataset_days:.1f}  "
          f"WF: {train_days}/{test_days}/{step_days}d  Ref: {ref_price:,.4f}")

    if MAX_TRAINING_DAYS is not None and pair_info.get("full_first_ts"):
        full_days = (pair_info["last_ts"] - pair_info["full_first_ts"]) / 86400
        used_days = (pair_info["last_ts"] - pair_info["first_ts"]) / 86400
        if full_days > used_days + 1:
            print(f"  Training window: {used_days:.0f}d of {full_days:.0f}d available (capped to {MAX_TRAINING_DAYS}d)")
    
    # ── Phase 1: Optimization ──
    study_name = f"{connector}_{pair}_{interval}_sweep_v1"

    try:
        study = optimize_study_for_notebook(
            study_name=study_name,
            storage_url=OPTUNA_STORAGE if OPTUNA_STORAGE else None,
            n_trials=N_TRIALS,
            n_jobs=N_JOBS,
            objective_factory=create_objective,
            factory_kwargs=dict(
                candles=dev_candles,
                pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds,
                dataset_hash=dev_dataset_hash,
                reference_price=ref_price,
                train_days=train_days,
                test_days=test_days,
                step_days=step_days,
                run_stress=False,
                controller_compat=SEARCH_CONTROLLER_COMPAT,
                objective_version=OBJECTIVE_VERSION,
                refresh_close_mode=REFRESH_CLOSE_MODE,
                initial_base_balance=INITIAL_BASE_BALANCE,
                taker_probability=taker_prob,
            ),
            callbacks=[DegeneracyCheckCallback()],
            n_startup_trials=int(N_TRIALS * PERC_TRIALS_TEST),
        )

        completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        pruned = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
        ranked = sorted(completed, key=lambda t: t.value, reverse=True)

        if not ranked:
            print(f"  Phase 1: {len(completed)} complete, {len(pruned)} pruned — NO COMPLETED TRIALS")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "no_completed_trials", "robust_score": None})
            continue

        best_val = ranked[0].value
        print(f"  Phase 1: {len(completed)} complete, {len(pruned)} pruned, best={best_val:.4f}")
    except Exception as e:
        print(f"  SKIP: optimization failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                              "status": "optim_fail", "robust_score": None})
        continue

    # ── Phase 1 score gate ──
    if best_val <= MIN_PHASE1_BEST_FOR_STRESS:
        print(f"  SKIP STRESS: phase-1 best ({best_val:.4f}) <= {MIN_PHASE1_BEST_FOR_STRESS}")
        sweep_results.append({
            "connector": connector,
            "pair": pair,
            "interval": interval,
            "status": "phase1_below_threshold",
            "robust_score": best_val,
            "phase1_best": best_val,
        })
        continue

    phase1_pair_elapsed = time.time() - pair_start
    print(f"  Phase 1 time:  ({phase1_pair_elapsed/60:.1f}min)")
    
    # ── Phase 2: Stress top N (with signal cache, dedup, early pruning) ──
    try:
        top_trials = ranked[:min(TOP_N, len(ranked))]

        top_candidates = []
        for trial in top_trials:
            config, reject = canonicalize_params(trial.params, pair_rules, ref_price)
            if config is not None:
                config = _replace(config, controller_compat=PHASE2_CONTROLLER_COMPAT, taker_probability=taker_prob)
                top_candidates.append({
                    "trial_number": trial.number,
                    "phase1_score": trial.value,
                    "params": trial.params,
                    "config": config,
                })

        if not top_candidates:
            print(f"  SKIP: no valid configs to stress test")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "no_valid_configs", "robust_score": None})
            continue

        # Deduplicate by full config fingerprint (Task 4.4)
        seen_configs = {}
        deduped_candidates = []
        for candidate in top_candidates:
            fingerprint = candidate["config"].to_fingerprint()
            if fingerprint not in seen_configs:
                seen_configs[fingerprint] = True
                deduped_candidates.append(candidate)
        print(f"  Phase 2: controller_compat={PHASE2_CONTROLLER_COMPAT} (search={SEARCH_CONTROLLER_COMPAT})")
        print(f"  Deduped: {len(top_candidates)} -> {len(deduped_candidates)} unique configs")
        top_candidates = deduped_candidates

        # Signal cache + early pruning (Tasks 4.3, 4.5)
        from pmm_lab.objective.phase2_parallel import precompute_unique_signals
        signal_cache = precompute_unique_signals(
            top_candidates=top_candidates,
            candles=dev_candles,
            pair_rules=pair_rules,
            max_workers=N_JOBS,
        )
        best, diag = select_best_stressed_candidate(
            top_candidates, dev_candles, pair_rules, bar_interval_seconds,
            scenarios=stress_scenarios,
            signal_cache=signal_cache,
            objective_version=OBJECTIVE_VERSION,
        )

        if best is None:
            print(f"  SKIP: no candidates survived stress testing")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "stress_fail", "robust_score": None})
            continue

        best_config = best["config"]
        best_stress = best["stress_report"]
        # Reuse winner baseline metrics (Task 4.2) — no extra sim needed
        bm = best_stress.baseline_metrics

        pair_elapsed = time.time() - pair_start
        print(f"  Best: trial {best['trial_number']}  robust={best['robust_score']:.4f}  "
              f"PnL={bm.pnl_pct:.2f}%  trades={bm.trade_count}  ({pair_elapsed/60:.1f}min)")
        print(f"  Stress diag: evaluated={diag['candidates_evaluated']} "
              f"pruned={diag['candidates_pruned']} "
              f"cache_hits={diag['signal_cache_hits']} misses={diag['signal_cache_misses']}")

    except Exception as e:
        print(f"  SKIP: stress testing failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                              "status": "stress_fail", "robust_score": None})
        continue


    # ── Finalist validation ──
    val_config = _replace(
        best_config,
        controller_compat=VALIDATION_CONTROLLER_COMPAT,
        refresh_close_mode=REFRESH_CLOSE_MODE,
        initial_base_balance=INITIAL_BASE_BALANCE,
        taker_probability=taker_prob,
    )

    # Multi-window recent evaluation (28d blocking + 14d/7d informational)
    recent_window_results = {}
    from pmm_lab.objective.signal_cache import SharedSignalCache
    _shared_cache = SharedSignalCache()
    _recent_signals = _shared_cache.get_or_compute(val_config, "full", candles, pair_rules)

    for _rw_days in RECENT_REPORT_WINDOW_DAYS:
        try:
            _rw = evaluate_recent_window(
                full_candles=candles, config=val_config, pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds,
                recent_days=_rw_days, run_stress=True, objective_version=OBJECTIVE_VERSION,
                precomputed_signals=_recent_signals,
                shared_signal_cache=_shared_cache,
            )
            recent_window_results[_rw_days] = _rw
            _role = "BLOCKER" if _rw_days == RECENT_BLOCKING_WINDOW_DAYS else "INFO"
            print(f"  Recent {_rw_days}d [{_role}]: {'PASS' if _rw.passed else 'FAIL'} — {_rw.reason}")
        except Exception as e:
            _role = "BLOCKER" if _rw_days == RECENT_BLOCKING_WINDOW_DAYS else "INFO"
            print(f"  Recent {_rw_days}d [{_role}]: ERROR — {e}")

    recent_window_result = recent_window_results.get(RECENT_BLOCKING_WINDOW_DAYS)

    holdout_report = None
    try:
        if dataset_slices is not None:
            holdout_candles_h = dataset_slices.holdout_candles
            holdout_start_idx = dataset_slices.holdout_start_idx_in_pre_release
        else:
            from pmm_lab.objective.holdout import split_holdout
            dev_candles_h, holdout_candles_h = split_holdout(candles, 0.20, min_holdout_bars=50)
            holdout_start_idx = len(dev_candles_h)
        holdout_candidates = [(val_config, best.get("robust_score", 0.0))]
        for t_idx in range(1, min(5, len(top_candidates))):
            tc = top_candidates[t_idx]
            tc_config = canonicalize_params(tc["params"], pair_rules, ref_price)[0]
            if tc_config is not None:
                tc_config = _replace(tc_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, taker_probability=taker_prob)
                holdout_candidates.append((tc_config, tc.get("phase1_score", 0.0)))
        holdout_report = evaluate_holdout(
            holdout_candles_h, holdout_candidates, pair_rules, bar_interval_seconds,
            run_stress=True, objective_version=OBJECTIVE_VERSION,
            full_candles=candles, holdout_start_idx=holdout_start_idx,
            shared_signal_cache=_shared_cache,
        )
        print(f"  Holdout: {'PASS' if holdout_report.exported_holdout_passed else 'FAIL'}")
    except Exception as e:
        print(f"  Holdout: ERROR \u2014 {e}")

    sensitivity_report = None
    sensitivity_penalty = None
    try:
        sensitivity_report = compute_sensitivity(
            best["params"], candles, pair_rules, bar_interval_seconds, ref_price,
            objective_version=OBJECTIVE_VERSION, controller_compat=VALIDATION_CONTROLLER_COMPAT,
            shared_signal_cache=_shared_cache,
        )
        sensitivity_penalty = sensitivity_report.sensitivity_penalty
        print(f"  Sensitivity: penalty={sensitivity_penalty:.4f}")
    except Exception as e:
        print(f"  Sensitivity: ERROR \u2014 {e}")

    cluster_report = None
    try:
        cluster_report = analyze_top_k(study, k=min(10, len(ranked)))
        print(f"  Clustering: {'CLUSTERED' if cluster_report.is_clustered else 'SCATTERED'}")
    except Exception as e:
        print(f"  Clustering: ERROR \u2014 {e}")

    parity_result = None
    long_parity_result = None
    try:
        from pathlib import Path as _Path
        _fix_base = _Path(__file__).resolve().parent.parent if '__file__' in dir() else _Path("fixtures")
        if not _fix_base.is_dir():
            _fix_base = _Path("research_notebooks/market_lab/pmm_dynamic/fixtures")
        if not _fix_base.is_dir():
            _fix_base = _Path("fixtures")
        _short = _fix_base / "short_100bar_compat"
        if _short.is_dir():
            _f = load_frozen_fixture(str(_short))
            parity_result = check_feature_parity_frozen(_f.candles, _f.expected_features, _f.config_params)
        _long = _fix_base / "long_500bar_compat"
        if _long.is_dir():
            _lf = load_frozen_fixture(str(_long))
            long_parity_result = check_feature_parity_frozen(_lf.candles, _lf.expected_features, _lf.config_params)
        print(f"  Parity: short={'PASS' if parity_result and parity_result.passed else 'N/A'}, long={'PASS' if long_parity_result and long_parity_result.passed else 'N/A'}")
    except Exception as e:
        print(f"  Parity: ERROR \u2014 {e}")

    full_validation_executed = all([recent_window_result is not None, holdout_report is not None])

    # ── Record result ──
    best_metrics = bm
    best_obj = best_stress.baseline_objective
    result_entry = {
        "connector": connector,
        "pair": pair,
        "interval": interval,
        "status": "complete",
        "robust_score": best["robust_score"],
        "baseline_score": best["baseline_score"],
        "worst_score": best["worst_score"],
        "worst_scenario": best["worst_scenario"],
        "pnl_pct": bm.pnl_pct,
        "sharpe": bm.sharpe,
        "max_dd_pct": bm.max_drawdown_pct,
        "trade_count": bm.trade_count,
        "total_fees": bm.total_fees_quote,
        "profit_factor": bm.profit_factor,
        "trial_number": best["trial_number"],
        "best_config": best_config,
        "best_params": best["params"],
        "best_stress": best_stress,
        "dataset_hash": dataset_hash,
        "n_candles": len(candles),
        "dataset_days": dataset_days,
        "train_days": train_days,
        "test_days": test_days,
        "step_days": step_days,
        "study_name": study_name,
        "recent_window_result": recent_window_result,
        "recent_window_results": recent_window_results,
        "holdout_report": holdout_report,
        "sensitivity_report": sensitivity_report,
        "sensitivity_penalty": sensitivity_penalty,
        "cluster_report": cluster_report,
        "parity_result": parity_result,
        "long_parity_result": long_parity_result,
        "full_validation_executed": full_validation_executed,
        "dataset_slices": dataset_slices if 'dataset_slices' in dir() else None,
    }
    sweep_results.append(result_entry)

    # ── Export if profitable ──
    if best["robust_score"] >= MIN_ROBUST_SCORE:
        validation_result = None
        try:
            export_params = ExportParams(
                connector_name=connector,
                trading_pair=pair,
                candles_connector=connector,
                candles_trading_pair=pair,
                interval=interval,
            )

            yaml_path = export_yaml(
                config=best_config,
                output_path=f"artifacts/sweep/{connector}/{pair}_{interval}_screening_best.yaml",
                export_params=export_params,
                metadata={
                    "dataset_hash": dataset_hash,
                    "trial": best["trial_number"],
                    "phase1_score": best["phase1_score"],
                    "robust_score": best["robust_score"],
                    "worst_scenario": best["worst_scenario"],
                    "worst_score": best["worst_score"],
                    "sweep_date": datetime.now(timezone.utc).isoformat(),
                },
            )
            validation_result = validate_yaml_file(
                yaml_path,
                supports_post_only=pair_rules.supports_post_only,
                taker_probability=taker_prob,
            )

            # Walk-forward for report
            wf_result = run_walk_forward(
                candles=candles, config=val_config, pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds, dataset_hash=dataset_hash,
                train_days=train_days, test_days=test_days, step_days=step_days,
                objective_version=OBJECTIVE_VERSION,
            )

            checks = run_stop_ship_checks(
                best_metrics=best_metrics, best_objective=best_obj,
                walkforward_result=wf_result, stress_report=best_stress,
                dataset_audit=audit,
                validation_result=validation_result,
                holdout_report=holdout_report,
                sensitivity_penalty=sensitivity_penalty,
                recent_window_result=recent_window_result,
                parity_result=parity_result,
                cluster_report=cluster_report,
                long_parity_result=long_parity_result,
                execution_realism={
                    "connector": connector,
                    "taker_probability": taker_prob,
                    "supports_post_only": pair_rules.supports_post_only,
                },
            )

            _run_provenance = {
                "notebook": os.path.basename(__file__) if '__file__' in dir() else "jupyter",
                "run_timestamp": datetime.now(timezone.utc).isoformat(),
                "n_jobs": N_JOBS,
                "objective_version": OBJECTIVE_VERSION,
                "search_controller_compat": SEARCH_CONTROLLER_COMPAT,
                "validation_controller_compat": VALIDATION_CONTROLLER_COMPAT,
                "refresh_close_mode": REFRESH_CLOSE_MODE,
                "initial_base_balance": INITIAL_BASE_BALANCE,
                "taker_probability": taker_prob,
                "trial_number": best["trial_number"],
            }

            generate_report(
                study_name=study_name,
                dataset_summary={
                    "connector": connector, "trading_pair": pair, "interval": interval,
                    "n_candles": len(candles), "dataset_hash": dataset_hash,
                    "n_trials_phase1": N_TRIALS, "n_candidates_stressed": len(top_candidates),
                    "total_amount_quote_search_min": 25.0,
                    "total_amount_quote_search_max": 1000.0,
                    "total_amount_quote_ideal": best_config.total_amount_quote,
                    "search_controller_compat": SEARCH_CONTROLLER_COMPAT,
                },
                best_params=best["params"], best_metrics=best_metrics, best_objective=best_obj,
                walkforward_result=wf_result, stress_report=best_stress,
                stop_ship_checks=checks,
                holdout_report=holdout_report,
                dataset_audit=audit,
                sensitivity_report=sensitivity_report,
                recent_window_result=recent_window_result,
                recent_window_results=recent_window_results,
                recent_blocking_window_days=RECENT_BLOCKING_WINDOW_DAYS,
                cluster_report=cluster_report,
                yaml_validation_result=validation_result,
                dataset_slices=dataset_slices,
                parity_result=parity_result,
                long_parity_result=long_parity_result,
                run_provenance=_run_provenance,
                execution_realism={
                    "taker_probability": taker_prob,
                    "supports_post_only": pair_rules.supports_post_only,
                    "connector": connector,
                    "fill_participation_rate": 0.1,
                    "latency_bars": 1,
                    "slippage_bps": 5.0,
                    "touch_through": best_config.touch_through,
                    "maker_fill_probability": best_config.maker_fill_probability,
                    "refresh_close_mode": REFRESH_CLOSE_MODE,
                },
                tp_min_notional_failures=best_metrics.tp_min_notional_failures,
                output_path=f"artifacts/sweep/{connector}/{pair}_{interval}_report.md",
            )

            total_time_per_pair = time.time() - pair_start
            print(f"  Total time: ({total_time_per_pair/60:.1f}min)")
            
            result_entry["exported"] = True
            result_entry["yaml_path"] = yaml_path
            all_pass = all(v for k, v in checks.items() if k != "taker_realism")
            if all_pass:
                import shutil
                _validated_path = yaml_path.replace("_screening_best.yaml", "_validated_best.yaml")
                shutil.copy2(yaml_path, _validated_path)
                print(f"  VALIDATED  yaml={_validated_path}")
            result_entry["all_checks_pass"] = all_pass
            print(f"  EXPORTED  yaml={yaml_path}  checks={'ALL PASS' if all_pass else 'SOME FAIL'}")
        except Exception as e:
            print(f"  Export failed: {e}")
            result_entry["exported"] = False
    else:
        result_entry["exported"] = False
        print(f"  NOT PROFITABLE (robust={best['robust_score']:.4f} < {MIN_ROBUST_SCORE})")

total_elapsed = time.time() - sweep_start
print(f"\n{'═'*60}")
print(f"SWEEP COMPLETE: {len(candidates)} connector/pair combinations in {total_elapsed/60:.1f} minutes")
print(f"{'═'*60}")


