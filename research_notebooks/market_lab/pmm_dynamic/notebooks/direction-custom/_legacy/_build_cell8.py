"""Generate cell 8 source for direction-custom sweep notebooks.

Produces MR and EMA variants, each with a multi-exchange and a retest flavor.
The notebook is the source of truth; this generator is run once then can be
deleted. It mirrors PMM's cell 8 (573 lines) with MR/EMA substitutions and
adds tqdm progress bars (outer + inner with TqdmProgressCallback).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent


def _common_header():
    return r'''# ── Config guard: ensure configuration cell was executed ──
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
    if "VALIDATION_CONTROLLER_COMPAT" not in globals():
        VALIDATION_CONTROLLER_COMPAT = True
    if "SEARCH_CONTROLLER_COMPAT" not in globals():
        SEARCH_CONTROLLER_COMPAT = False
    if "PHASE2_CONTROLLER_COMPAT" not in globals():
        PHASE2_CONTROLLER_COMPAT = True
    if "OBJECTIVE_VERSION" not in globals():
        OBJECTIVE_VERSION = 2
    if "N_TRIALS" not in globals():
        N_TRIALS = 200
    if "TOP_N" not in globals():
        TOP_N = 25
    if "MIN_ROBUST_SCORE" not in globals():
        MIN_ROBUST_SCORE = 0.0
    if "N_JOBS" not in globals():
        N_JOBS = 1
    if "MIN_PHASE1_BEST_FOR_STRESS" not in globals():
        MIN_PHASE1_BEST_FOR_STRESS = 0.0

# Enable the Numba-compiled controller-compat feature kernels.
# Stage 1 benchmarks: ~247x MR, ~3549x EMA warm-call speedup.
# Set to False to use the pandas replay path (no numerical change).
USE_NUMBA_KERNEL = True

# Pair-level parallelism: run multiple pairs concurrently via ThreadPoolExecutor.
# 1 = serial (original behavior). On a 32-CPU host with N_JOBS=8, PAIR_JOBS=4
# saturates CPUs (4 pairs × 8 Optuna workers). Going higher than PAIR_JOBS=4
# without halving N_JOBS oversubscribes subprocesses on most hardware.
# The outer layer MUST be threads, not processes — nested ProcessPoolExecutor
# raises "daemonic processes are not allowed to have children".
if "PAIR_JOBS" not in globals():
    PAIR_JOBS = 1

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

'''


def _mr_imports():
    return r'''import os, time
from dataclasses import replace as _replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import optuna
from tqdm.auto import tqdm

from pmm_lab.data.candles import validate_candles
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.callbacks import (
    DegeneracyCheckCallback, TrialLoggingCallback, TqdmProgressCallback,
)
# MR-specific imports (aliased to match PMM naming) — substitution per prompt 5A
from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import (
    canonicalize_mr_bb_rsi_params as canonicalize_params,
)
from pmm_lab.export.hb_yaml_mr_bb_rsi import (
    export_mr_bb_rsi_yaml as export_yaml,
    MRBBRSIExportParams as ExportParams,
    validate_export_mr_bb_rsi as validate_yaml_file,
)
from pmm_lab.objective.stress import load_stress_scenarios
from pmm_lab.objective.stress_selection import select_best_stressed_candidate
from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch
from pmm_lab.objective.objective import REJECT_SCORE, objective_v1
from pmm_lab.report.report_md import generate_report, run_stop_ship_checks
from pmm_lab.objective.recent_window import evaluate_recent_window
from pmm_lab.objective.holdout import evaluate_holdout, split_holdout, HoldoutCandidateSpec
from pmm_lab.objective.dataset_split import split_for_release_gate
from pmm_lab.objective.signal_cache import SharedSignalCache
from pmm_lab.optuna.sensitivity import compute_sensitivity, MR_PERTURBABLE_PARAMS
from pmm_lab.optuna.clustering import analyze_top_k
from pmm_lab.parity.feature_parity import check_feature_parity_frozen_mr
from pmm_lab.parity.fixtures import load_frozen_fixture
from pmm_lab.data.candles import hash_candles

'''


def _ema_imports():
    return r'''import os, time
from dataclasses import replace as _replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import optuna
from tqdm.auto import tqdm

from pmm_lab.data.candles import validate_candles
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.callbacks import (
    DegeneracyCheckCallback, TrialLoggingCallback, TqdmProgressCallback,
)
# EMA-specific imports (aliased) — substitution per prompt 5A
from pmm_lab.optuna.canonicalizer_ema_regime_hold import (
    canonicalize_ema_regime_hold_params as canonicalize_params,
)
from pmm_lab.export.hb_yaml_ema_regime_hold import (
    export_ema_regime_hold_yaml as export_yaml,
    EMARegimeHoldExportParams as ExportParams,
    validate_export_ema_regime_hold as validate_yaml_file,
)
from pmm_lab.objective.stress import load_stress_scenarios
from pmm_lab.objective.stress_selection import select_best_stressed_candidate
from pmm_lab.objective.walkforward_dispatch import run_walk_forward_dispatch
from pmm_lab.objective.objective import REJECT_SCORE, objective_v1
from pmm_lab.report.report_md import generate_report, run_stop_ship_checks
from pmm_lab.objective.recent_window import evaluate_recent_window
from pmm_lab.objective.holdout import evaluate_holdout, split_holdout, HoldoutCandidateSpec
from pmm_lab.objective.dataset_split import split_for_release_gate
from pmm_lab.objective.signal_cache import SharedSignalCache
from pmm_lab.optuna.sensitivity import compute_sensitivity, EMA_PERTURBABLE_PARAMS
from pmm_lab.optuna.clustering import analyze_top_k
from pmm_lab.parity.feature_parity import check_feature_parity_frozen_ema
from pmm_lab.parity.fixtures import load_frozen_fixture
from pmm_lab.data.candles import hash_candles
from pmm_lab.data.ema_identity import compute_ema_dataset_identity

'''


def _common_preloop():
    return r'''# Preload stress scenarios once
stress_scenarios = load_stress_scenarios()

rules_db = load_exchange_rules()
sweep_results = []
sweep_start = time.time()

_pair_bar = tqdm(
    total=len(candidates), position=0, leave=True, desc="Pairs",
)

'''


def _mr_body():
    return r'''def _run_one_pair(pair_idx, pair_info):
    connector = pair_info["connector"]
    pair = pair_info["trading_pair"]
    interval = pair_info["interval"]
    bar_interval_seconds = INTERVAL_SECONDS[interval]
    _pair_bar.set_postfix_str(f"{connector}/{pair}")

    print(f"\n{'='*60}")
    print(f"  [{pair_idx+1}/{len(candidates)}] {connector} / {pair} / {interval}")
    print(f"{'='*60}")

    pair_start = time.time()

    # ── Load candles ──
    try:
        _start_ts = int(pair_info["first_ts"]) if (MAX_TRAINING_DAYS is not None and "first_ts" in pair_info) else None
        query = DataQuery(connector=connector, trading_pair=pair, interval=interval, start_ts=_start_ts)
        candles = loader.load_range(query)
        audit = validate_candles(candles, interval=interval, strict=True)
        if not audit.passed_strict:
            print(f"  SKIP: audit failed — {audit.failure_reasons}")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "audit_fail", "robust_score": None})
            return
        dataset_hash = hash_candles(candles)
    except Exception as e:
        print(f"  SKIP: load failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                              "status": "load_fail", "robust_score": None})
        return

    # ── Dataset split for release gate (informational) ──
    try:
        dataset_slices = split_for_release_gate(
            candles, recent_days=RECENT_BLOCKING_WINDOW_DAYS, holdout_fraction=0.20,
            min_pre_release_bars=200, min_holdout_bars=50,
        )
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
        try:
            pair_rules = resolve_pair_rules(rules_db, connector, "DEFAULT")
        except KeyError:
            print(f"  SKIP: no exchange rules for {connector}/{pair}")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "no_rules", "robust_score": None})
            return

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
        return

    print(f"  Candles: {len(candles):,}  Days: {dataset_days:.1f}  "
          f"WF: {train_days}/{test_days}/{step_days}d  Ref: {ref_price:,.4f}")

    # ── Phase 1: Optimization with inner tqdm bar + DegeneracyCheck ──
    study_name = f"{connector}_{pair}_{interval}_mr_bb_rsi_v1"

    if PAIR_JOBS > 1:
        _trial_bar = None
        _trial_cb = None
    else:
        _trial_bar = tqdm(total=N_TRIALS, position=1, leave=False, desc="trials")
        _trial_cb = TqdmProgressCallback(_trial_bar, show_best=True)

    try:
        study = optimize_study_for_notebook(
            study_name=study_name,
            storage_url=OPTUNA_STORAGE if "OPTUNA_STORAGE" in globals() and OPTUNA_STORAGE else None,
            n_trials=N_TRIALS,
            n_jobs=N_JOBS,
            objective_factory=create_objective,
            factory_kwargs=dict(
                candles=dev_candles,
                pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds,
                dataset_hash=dev_dataset_hash,
                reference_price=ref_price,
                strategy_name="mean_reversion_bb_rsi",
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
            callbacks=([DegeneracyCheckCallback(), _trial_cb] if _trial_cb is not None else [DegeneracyCheckCallback()]),
            n_startup_trials=int(N_TRIALS * PERC_TRIALS_TEST) if "PERC_TRIALS_TEST" in globals() else 15,
        )

        completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        pruned = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
        ranked = sorted(
            [t for t in completed if t.value is not None],
            key=lambda t: t.value, reverse=True,
        )

        if not ranked:
            print(f"  Phase 1: {len(completed)} complete, {len(pruned)} pruned — NO COMPLETED TRIALS")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "no_completed_trials", "robust_score": None})
            _trial_bar.close()
            return

        best_val = ranked[0].value
        print(f"  Phase 1: {len(completed)} complete, {len(pruned)} pruned, best={best_val:.4f}")
    except Exception as e:
        print(f"  SKIP: optimization failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                              "status": "optim_fail", "robust_score": None})
        _trial_bar.close()
        return
    finally:
        try:
            if _trial_bar is not None:
                _trial_bar.close()
        except Exception:
            pass

    # ── Phase 1 score gate (informational — log and continue to Phase 2) ──
    phase1_below_threshold = best_val <= MIN_PHASE1_BEST_FOR_STRESS
    if phase1_below_threshold:
        print(f"  INFO: phase-1 best ({best_val:.4f}) <= {MIN_PHASE1_BEST_FOR_STRESS}; continuing anyway")

    phase1_pair_elapsed = time.time() - pair_start
    print(f"  Phase 1 time: ({phase1_pair_elapsed/60:.1f}min)")

    # ── Phase 2: Stress top N (dedup via to_fingerprint, MR-local stress) ──
    try:
        top_trials = ranked[:min(TOP_N, len(ranked))]
        top_candidates = []
        for trial in top_trials:
            raw = dict(trial.params)
            raw.setdefault("min_trend_slope", 0.0)
            raw.setdefault("max_spread_pct", 0.006)
            raw.setdefault("max_trades_per_day", 6)
            raw.setdefault("max_executors_per_side", 1)
            raw.setdefault("total_amount_quote", 300.0)
            bundle, reject = canonicalize_params(
                raw, pair_rules, ref_price, bar_interval_seconds=bar_interval_seconds,
            )
            if bundle is not None:
                sc = _replace(bundle.strategy_config, controller_compat=PHASE2_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)
                ec = _replace(bundle.engine_config, taker_probability=taker_prob)
                top_candidates.append({
                    "trial_number": trial.number,
                    "phase1_score": trial.value,
                    "params": trial.params,
                    "config": sc,
                    "engine_config": ec,
                })

        if not top_candidates:
            print(f"  SKIP: no valid configs to stress test")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "no_valid_configs", "robust_score": None})
            return

        # Dedup by full config fingerprint
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

        # Signal cache for MR: process-parallel precompute for Phase 2 (Stage 3).
        # Returns a SharedSignalCache containing one entry per unique signal_cache_key.
        from pmm_lab.objective.phase2_parallel_directional import (
            precompute_unique_directional_signals,
        )
        _shared_cache = precompute_unique_directional_signals(
            top_candidates=top_candidates,
            candles=dev_candles,
            pair_rules=pair_rules,
            regime_candles=None,
            dataset_key="dev",
            max_workers=N_JOBS,
        )

        # MR apply_scenario: modify engine_config (not strategy_config)
        from pmm_lab.objective.stress_mean_reversion_bb_rsi import _apply_scenario as _mr_apply_scenario
        def _apply_scenario_fn(strategy_cfg, engine_cfg, pair_rules, scenario):
            new_engine, new_rules = _mr_apply_scenario(engine_cfg, pair_rules, scenario)
            return strategy_cfg, new_engine, new_rules

        best, diag = select_best_stressed_candidate(
            top_candidates, dev_candles, pair_rules, bar_interval_seconds,
            scenarios=stress_scenarios,
            objective_version=OBJECTIVE_VERSION,
            shared_signal_cache=_shared_cache,
            dataset_key="dev",
            apply_scenario_fn=_apply_scenario_fn,
        )

        if best is None:
            print(f"  SKIP: no candidates survived stress testing")
            sweep_results.append({"connector": connector, "pair": pair, "interval": interval,
                                  "status": "stress_fail", "robust_score": None})
            return

        best_config = best["config"]
        best_engine_config = best["engine_config"]
        best_stress = best["stress_report"]
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
                              "status": "stress_fail", "robust_score": None, "error": str(e)})
        return

    # ── Finalist validation ──
    val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)
    val_engine = _replace(
        best_engine_config,
        refresh_close_mode=REFRESH_CLOSE_MODE,
        initial_base_balance=INITIAL_BASE_BALANCE,
        taker_probability=taker_prob,
    )

    recent_window_results = {}
    _shared_cache_full = SharedSignalCache()
    _recent_signals = _shared_cache_full.get_or_compute(
        val_config, "full", candles, pair_rules,
    )

    for _rw_days in RECENT_REPORT_WINDOW_DAYS:
        try:
            _rw = evaluate_recent_window(
                full_candles=candles, config=val_config, pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds,
                recent_days=_rw_days, run_stress=False,
                objective_version=OBJECTIVE_VERSION,
                precomputed_signals=_recent_signals,
                shared_signal_cache=_shared_cache_full,
                engine_config=val_engine,
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
            dev_candles_h, holdout_candles_h = split_holdout(candles, 0.20, min_holdout_bars=50)
            holdout_start_idx = len(dev_candles_h)
        # Per-candidate engine_config (Stage 1 fix): MR execution fields live on
        # engine_config, not strategy_config. Each candidate gets its own engine
        # config so holdout scoring uses the candidate's real execution params.
        holdout_candidates = [
            HoldoutCandidateSpec(
                strategy_config=val_config,
                engine_config=val_engine,
                development_score=best.get("robust_score", 0.0),
            )
        ]
        for t_idx in range(1, min(5, len(top_candidates))):
            tc = top_candidates[t_idx]
            tc_bundle, _ = canonicalize_params(
                dict(tc["params"], min_trend_slope=0.0, max_spread_pct=0.006,
                     max_trades_per_day=6, max_executors_per_side=1, total_amount_quote=300.0),
                pair_rules, ref_price, bar_interval_seconds=bar_interval_seconds,
            )
            if tc_bundle is not None:
                tc_cfg = _replace(tc_bundle.strategy_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)
                tc_engine = _replace(
                    tc_bundle.engine_config,
                    refresh_close_mode=REFRESH_CLOSE_MODE,
                    initial_base_balance=INITIAL_BASE_BALANCE,
                    taker_probability=taker_prob,
                )
                holdout_candidates.append(
                    HoldoutCandidateSpec(
                        strategy_config=tc_cfg,
                        engine_config=tc_engine,
                        development_score=tc.get("phase1_score", 0.0),
                    )
                )
        holdout_report = evaluate_holdout(
            holdout_candles_h, holdout_candidates, pair_rules, bar_interval_seconds,
            run_stress=False, objective_version=OBJECTIVE_VERSION,
            full_candles=candles, holdout_start_idx=holdout_start_idx,
            shared_signal_cache=_shared_cache_full,
            engine_config=val_engine,  # defensive fallback for specs with engine_config=None
        )
        print(f"  Holdout: {'PASS' if holdout_report.exported_holdout_passed else 'FAIL'}")
    except Exception as e:
        print(f"  Holdout: ERROR — {e}")

    sensitivity_report = None
    sensitivity_penalty = None
    try:
        def _mr_canon_adapter(params, pair_rules_arg, ref_price_arg, **kwargs):
            raw = dict(params)
            raw.setdefault("min_trend_slope", 0.0)
            raw.setdefault("max_spread_pct", 0.006)
            raw.setdefault("max_trades_per_day", 6)
            raw.setdefault("max_executors_per_side", 1)
            raw.setdefault("total_amount_quote", 300.0)
            return canonicalize_params(
                raw, pair_rules_arg, ref_price_arg, bar_interval_seconds=bar_interval_seconds,
            )
        sensitivity_report = compute_sensitivity(
            best["params"], candles, pair_rules, bar_interval_seconds, ref_price,
            objective_version=OBJECTIVE_VERSION,
            controller_compat=VALIDATION_CONTROLLER_COMPAT,
            shared_signal_cache=_shared_cache_full,
            canonicalize_fn=_mr_canon_adapter,
            perturb_params=MR_PERTURBABLE_PARAMS,
            use_numba_kernel=USE_NUMBA_KERNEL,
        )
        sensitivity_penalty = sensitivity_report.sensitivity_penalty
        print(f"  Sensitivity: penalty={sensitivity_penalty:.4f}")
    except Exception as e:
        print(f"  Sensitivity: ERROR — {e}")

    cluster_report = None
    try:
        cluster_report = analyze_top_k(study, k=min(10, len(ranked)))
        print(f"  Clustering: {'CLUSTERED' if cluster_report.is_clustered else 'SCATTERED'}")
    except Exception as e:
        print(f"  Clustering: ERROR — {e}")

    parity_result = None
    long_parity_result = None
    try:
        # Directional MR parity — uses MR-specific fixture and check (P2.3)
        _fix_base = Path("fixtures")
        if _fix_base.is_dir():
            _short = _fix_base / "mr_short_100bar"
            if _short.is_dir():
                _f = load_frozen_fixture(str(_short))
                parity_result = check_feature_parity_frozen_mr(
                    _f.candles, _f.expected_features, _f.config_params,
                )
        print(f"  Parity: short={'PASS' if parity_result and parity_result.passed else 'N/A'}")
    except Exception as e:
        print(f"  Parity: ERROR — {e}")

    full_validation_executed = all([recent_window_result is not None, holdout_report is not None])

    # ── Record result ──
    best_metrics = bm
    best_obj = best_stress.baseline_objective
    # Pull rejection fraction from best trial's user attrs (ML-DIR-007)
    _best_trial_obj = next(
        (t for t in study.trials if t.number == best["trial_number"]), None,
    )
    _reject_frac = None
    if _best_trial_obj is not None:
        _reject_frac = _best_trial_obj.user_attrs.get("total_reject_fraction")
        if _reject_frac is None:
            _reject_frac = _best_trial_obj.user_attrs.get("max_trades_per_day_binding_fraction")
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
        "total_reject_fraction": _reject_frac,
        "trial_number": best["trial_number"],
        "best_config": best_config,
        "best_engine_config": best_engine_config,
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
        "phase1_below_threshold": phase1_below_threshold,
    }
    sweep_results.append(result_entry)

    # ── Validation state machine: fail-closed YAML placement (ML-DIR-001) ──
    # Status values: optimized_only, validation_error, validated_fail, validated_pass
    MANDATORY_GATES = {
        "dataset_audit", "runtime_sanity", "objective_not_degenerate",
        "stress_not_collapsed", "yaml_validates",
        "walkforward_robust", "walkforward_positive_majority",
        "holdout_passed", "holdout_no_collapse",
        "sensitivity_stable", "recent_28d_passed", "top_k_clustered",
    }
    # Once MR + EMA frozen fixtures exist and check_feature_parity_frozen_mr/_ema are green,
    # promote "frozen_parity" into MANDATORY_GATES. Flip this to "mandatory" after P2.3
    # fixtures are committed AND verified to pass on the current feature impls.
    FROZEN_PARITY_POLICY = "advisory"
    if FROZEN_PARITY_POLICY == "mandatory":
        MANDATORY_GATES = MANDATORY_GATES | {"frozen_parity"}

    validation_status = "optimized_only"
    validation_errors = []
    mandatory_gates_failed = []
    yaml_path = None
    checks = {}
    validation_result = None
    wf_result = None

    # Export YAML to .pending/ first; final placement depends on outcome
    try:
        export_params = ExportParams(
            connector_name=connector, trading_pair=pair, interval=interval,
        )
        _out_dir = Path(f"artifacts/direction-custom/mr_bb_rsi/{connector}")
        _out_dir.mkdir(parents=True, exist_ok=True)
        _yaml_filename = f"{connector}_{pair.replace('-', '_').lower()}_{interval}_screening_best.yml"
        _pending_dir = _out_dir / ".pending"
        _pending_dir.mkdir(parents=True, exist_ok=True)
        pending_yaml_path = str(_pending_dir / _yaml_filename)
        export_yaml(best_config, best_engine_config, export_params, Path(pending_yaml_path))
        validation_result = validate_yaml_file(Path(pending_yaml_path))
    except Exception as e:
        validation_errors.append(("export", type(e).__name__, str(e)))
        print(f"  Export/validate error: {e}")

    try:
        wf_result = run_walk_forward_dispatch(
            candles=candles, config=val_config, pair_rules=pair_rules,
            bar_interval_seconds=bar_interval_seconds, dataset_hash=dataset_hash,
            train_days=train_days, test_days=test_days, step_days=step_days,
            objective_version=OBJECTIVE_VERSION,
            engine_config=val_engine,
            shared_signal_cache=_shared_cache_full,
            dataset_key="dev",
        )
        print(f"  Walk-forward: {len(wf_result.folds)} folds, aggregate={wf_result.aggregate_score:.4f}")
    except Exception as e:
        validation_errors.append(("walkforward", type(e).__name__, str(e)))
        print(f"  Walk-forward ERROR: {type(e).__name__}: {e}")
        wf_result = None

    try:
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
        mandatory_gates_failed = [
            name for name in MANDATORY_GATES if checks.get(name) is False
        ]
        if validation_errors:
            validation_status = "validation_error"
        elif mandatory_gates_failed:
            validation_status = "validated_fail"
        else:
            validation_status = "validated_pass"
    except Exception as e:
        validation_errors.append(("stop_ship_checks", type(e).__name__, str(e)))
        validation_status = "validation_error"
        print(f"  Stop-ship checks error: {e}")

    # Move YAML based on outcome
    import shutil as _shutil
    if pending_yaml_path and Path(pending_yaml_path).exists():
        if validation_status == "validated_pass":
            yaml_path = str(_out_dir / _yaml_filename)
            _shutil.move(pending_yaml_path, yaml_path)
        else:
            _rejected_dir = _out_dir / "rejected"
            _rejected_dir.mkdir(parents=True, exist_ok=True)
            yaml_path = str(_rejected_dir / _yaml_filename)
            _shutil.move(pending_yaml_path, yaml_path)
            # Drop a REJECTED.json sibling marker
            import json as _json
            _marker = Path(yaml_path).with_suffix("").as_posix() + "_REJECTED.json"
            Path(_marker).write_text(_json.dumps({
                "validation_status": validation_status,
                "mandatory_gates_failed": mandatory_gates_failed,
                "validation_errors": [
                    {"step": step, "type": t, "message": m}
                    for step, t, m in validation_errors
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dataset_hash": dataset_hash,
                "mandatory_gates_policy": {
                    "frozen_parity_policy": FROZEN_PARITY_POLICY,
                    "mandatory_gates": sorted(list(MANDATORY_GATES)),
                },
            }, indent=2))

    result_entry["status"] = validation_status
    result_entry["validation_status"] = validation_status
    result_entry["validation_errors"] = validation_errors
    result_entry["mandatory_gates_failed"] = mandatory_gates_failed
    result_entry["yaml_path"] = yaml_path
    result_entry["checks"] = checks

    try:
        _run_provenance = {
            "notebook": "direction-custom/mr_bb_rsi",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "n_jobs": N_JOBS,
            "objective_version": OBJECTIVE_VERSION,
            "search_controller_compat": SEARCH_CONTROLLER_COMPAT,
            "validation_controller_compat": VALIDATION_CONTROLLER_COMPAT,
            "refresh_close_mode": REFRESH_CLOSE_MODE,
            "initial_base_balance": INITIAL_BASE_BALANCE,
            "taker_probability": taker_prob,
            "trial_number": best["trial_number"],
            "validation_status": validation_status,
        }
        generate_report(
            study_name=study_name,
            dataset_summary={
                "connector": connector, "trading_pair": pair, "interval": interval,
                "n_candles": len(candles), "dataset_hash": dataset_hash,
                "n_trials_phase1": N_TRIALS, "n_candidates_stressed": len(top_candidates),
                "total_amount_quote_search_min": 50.0,
                "total_amount_quote_search_max": 500.0,
                "total_amount_quote_ideal": best_engine_config.total_amount_quote,
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
                "refresh_close_mode": REFRESH_CLOSE_MODE,
            },
            tp_min_notional_failures=getattr(best_metrics, "tp_min_notional_failures", 0),
            output_path=f"artifacts/direction-custom/mr_bb_rsi/{connector}/{pair.replace('-', '_').lower()}_{interval}_report.md",
        )
        _gates_pass = sum(1 for v in checks.values() if v)
        _gates_total = len(checks)
        result_entry["gates_pass"] = _gates_pass
        result_entry["gates_total"] = _gates_total
        _total_time = time.time() - pair_start
        print(f"  Total time: ({_total_time/60:.1f}min)  Gates: {_gates_pass}/{_gates_total}  Status: {validation_status}")
        if yaml_path:
            print(f"  YAML: {yaml_path}")
        if mandatory_gates_failed:
            print(f"  Failed mandatory gates: {mandatory_gates_failed}")
    except Exception as e:
        print(f"  Report error: {e}")

    return
if PAIR_JOBS <= 1:
    for pair_idx, pair_info in enumerate(candidates):
        try:
            _run_one_pair(pair_idx, pair_info)
        except Exception as _e:
            import traceback as _tb
            print(f"  [pair {pair_idx+1}] raised: {_e}")
            _tb.print_exc()
        _pair_bar.update(1)
else:
    from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _as_completed
    print(f"[pair-level] Running with PAIR_JOBS={PAIR_JOBS} threads x N_JOBS={N_JOBS} Optuna subprocesses per pair.")
    with _TPE(max_workers=PAIR_JOBS) as _pool:
        _futs = {
            _pool.submit(_run_one_pair, _pidx, _pinfo): (_pidx, _pinfo)
            for _pidx, _pinfo in enumerate(candidates)
        }
        for _fut in _as_completed(_futs):
            _pidx, _pinfo = _futs[_fut]
            try:
                _fut.result()
            except Exception as _e:
                import traceback as _tb
                print(f"  [parallel] pair {_pidx+1} raised: {_e}")
                _tb.print_exc()
            _pair_bar.update(1)

_pair_bar.close()

total_elapsed = time.time() - sweep_start
print(f"\n{'='*60}")
print(f"SWEEP COMPLETE: {len(candidates)} connector/pair combinations in {total_elapsed/60:.1f} minutes")
print(f"{'='*60}")
'''


def _ema_body():
    return r'''def _run_one_pair(pair_idx, pair_info):
    connector = pair_info["connector"]
    pair = pair_info["trading_pair"]
    signal_interval = pair_info["signal_interval"]
    regime_interval = pair_info["regime_interval"]
    bar_interval_seconds = INTERVAL_SECONDS[signal_interval]
    regime_interval_seconds = INTERVAL_SECONDS[regime_interval]
    _pair_bar.set_postfix_str(f"{connector}/{pair} {signal_interval}+{regime_interval}")

    print(f"\n{'='*60}")
    print(f"  [{pair_idx+1}/{len(candidates)}] {connector} / {pair} / {signal_interval}+{regime_interval}")
    print(f"{'='*60}")

    pair_start = time.time()

    # ── Load BOTH candle streams (hard stop on either) ──
    try:
        _signal_start = int(pair_info.get("signal_first_ts")) if (MAX_TRAINING_DAYS is not None and pair_info.get("signal_first_ts") is not None) else None
        _regime_start = int(pair_info.get("regime_first_ts")) if (MAX_TRAINING_DAYS is not None and pair_info.get("regime_first_ts") is not None) else None
        signal_candles = loader.load_range(
            DataQuery(connector=connector, trading_pair=pair, interval=signal_interval, start_ts=_signal_start),
        )
        regime_candles = loader.load_range(
            DataQuery(connector=connector, trading_pair=pair, interval=regime_interval, start_ts=_regime_start),
        )
    except Exception as e:
        print(f"  SKIP: load failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair,
                              "signal_interval": signal_interval, "regime_interval": regime_interval,
                              "status": "load_error", "error": str(e), "robust_score": None})
        return

    # ── Audit both streams (hard stop on either) ──
    audit = validate_candles(signal_candles, interval=signal_interval, strict=True)
    if not audit.passed_strict:
        print(f"  SKIP: signal audit failed — {audit.failure_reasons}")
        sweep_results.append({"connector": connector, "pair": pair,
                              "signal_interval": signal_interval, "regime_interval": regime_interval,
                              "status": "audit_fail_signal", "robust_score": None})
        return
    regime_audit = validate_candles(regime_candles, interval=regime_interval, strict=True)
    if not regime_audit.passed_strict:
        print(f"  SKIP: regime audit failed — {regime_audit.failure_reasons}")
        sweep_results.append({"connector": connector, "pair": pair,
                              "signal_interval": signal_interval, "regime_interval": regime_interval,
                              "status": "audit_fail_regime", "robust_score": None})
        return
    # Composite EMA dataset identity (ML-DIR-002) — covers BOTH streams
    _identity = compute_ema_dataset_identity(
        signal_candles=signal_candles, regime_candles=regime_candles,
        signal_interval=signal_interval, regime_interval=regime_interval,
    )
    dataset_hash = _identity["composite_hash"]
    signal_hash = _identity["signal_hash"]
    regime_hash = _identity["regime_hash"]

    # ── Dataset split (on signal candles) ──
    try:
        dataset_slices = split_for_release_gate(
            signal_candles, recent_days=RECENT_BLOCKING_WINDOW_DAYS, holdout_fraction=0.20,
            min_pre_release_bars=200, min_holdout_bars=50,
        )
        dev_candles = dataset_slices.dev_candles
        dev_dataset_hash = hash_candles(dev_candles)
        print(f"  Split: dev={len(dev_candles)} holdout={len(dataset_slices.holdout_candles)} recent={len(dataset_slices.recent_release_candles)}")
    except ValueError as e:
        print(f"  Split failed ({e}), using full candles")
        dataset_slices = None
        dev_candles = signal_candles
        dev_dataset_hash = dataset_hash

    # ── Exchange rules ──
    try:
        pair_rules = resolve_pair_rules(rules_db, connector, pair)
    except KeyError:
        try:
            pair_rules = resolve_pair_rules(rules_db, connector, "DEFAULT")
        except KeyError:
            print(f"  SKIP: no exchange rules for {connector}/{pair}")
            sweep_results.append({"connector": connector, "pair": pair,
                                  "signal_interval": signal_interval, "regime_interval": regime_interval,
                                  "status": "no_rules", "robust_score": None})
            return

    taker_prob = TAKER_PROBABILITY_BY_CONNECTOR.get(connector, DEFAULT_TAKER_PROBABILITY)
    ref_price = float(np.median(signal_candles["close"]))

    dataset_days = len(signal_candles) * bar_interval_seconds / 86400
    if dataset_days >= 120:
        train_days, test_days, step_days = 42.0, 14.0, 14.0
    elif dataset_days >= 60:
        train_days, test_days, step_days = 21.0, 7.0, 7.0
    elif dataset_days >= 28:
        train_days, test_days, step_days = 10.0, 4.0, 4.0
    else:
        print(f"  SKIP: only {dataset_days:.1f} days of data")
        sweep_results.append({"connector": connector, "pair": pair,
                              "signal_interval": signal_interval, "regime_interval": regime_interval,
                              "status": "insufficient_data", "robust_score": None})
        return

    print(f"  Candles: {len(signal_candles):,} signal / {len(regime_candles):,} regime  "
          f"Days: {dataset_days:.1f}  WF: {train_days}/{test_days}/{step_days}d  Ref: {ref_price:,.4f}")

    # ── Phase 1: Optimization with inner tqdm bar + regime_candles in factory_kwargs ──
    study_name = f"{connector}_{pair}_{signal_interval}_{regime_interval}_ema_regime_hold_v1"
    if PAIR_JOBS > 1:
        _trial_bar = None
        _trial_cb = None
    else:
        _trial_bar = tqdm(total=N_TRIALS, position=1, leave=False, desc="trials")
        _trial_cb = TqdmProgressCallback(_trial_bar, show_best=True)

    try:
        study = optimize_study_for_notebook(
            study_name=study_name,
            storage_url=OPTUNA_STORAGE if "OPTUNA_STORAGE" in globals() and OPTUNA_STORAGE else None,
            n_trials=N_TRIALS,
            n_jobs=N_JOBS,
            objective_factory=create_objective,
            factory_kwargs=dict(
                candles=dev_candles,
                pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds,
                dataset_hash=dev_dataset_hash,
                reference_price=ref_price,
                strategy_name="ema_regime_hold",
                train_days=train_days,
                test_days=test_days,
                step_days=step_days,
                run_stress=False,
                controller_compat=SEARCH_CONTROLLER_COMPAT,
                objective_version=OBJECTIVE_VERSION,
                refresh_close_mode=REFRESH_CLOSE_MODE,
                initial_base_balance=INITIAL_BASE_BALANCE,
                taker_probability=taker_prob,
                regime_candles=regime_candles,
            ),
            callbacks=([DegeneracyCheckCallback(), _trial_cb] if _trial_cb is not None else [DegeneracyCheckCallback()]),
            n_startup_trials=int(N_TRIALS * PERC_TRIALS_TEST) if "PERC_TRIALS_TEST" in globals() else 15,
        )

        completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        pruned = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
        ranked = sorted(
            [t for t in completed if t.value is not None],
            key=lambda t: t.value, reverse=True,
        )

        if not ranked:
            print(f"  Phase 1: {len(completed)} complete, {len(pruned)} pruned — NO COMPLETED TRIALS")
            sweep_results.append({"connector": connector, "pair": pair,
                                  "signal_interval": signal_interval, "regime_interval": regime_interval,
                                  "status": "no_completed_trials", "robust_score": None})
            _trial_bar.close()
            return

        best_val = ranked[0].value
        print(f"  Phase 1: {len(completed)} complete, {len(pruned)} pruned, best={best_val:.4f}")
    except Exception as e:
        print(f"  SKIP: optimization failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair,
                              "signal_interval": signal_interval, "regime_interval": regime_interval,
                              "status": "optim_fail", "robust_score": None, "error": str(e)})
        _trial_bar.close()
        return
    finally:
        try:
            if _trial_bar is not None:
                _trial_bar.close()
        except Exception:
            pass

    phase1_below_threshold = best_val <= MIN_PHASE1_BEST_FOR_STRESS
    if phase1_below_threshold:
        print(f"  INFO: phase-1 best ({best_val:.4f}) <= {MIN_PHASE1_BEST_FOR_STRESS}; continuing anyway")

    phase1_pair_elapsed = time.time() - pair_start
    print(f"  Phase 1 time: ({phase1_pair_elapsed/60:.1f}min)")

    # ── Phase 2: Stress top N ──
    try:
        top_trials = ranked[:min(TOP_N, len(ranked))]
        top_candidates = []
        for trial in top_trials:
            raw = dict(trial.params)
            raw.setdefault("hold_mode", "reentry")
            raw.setdefault("max_executors_per_side", 1)
            raw.setdefault("total_amount_quote", 300.0)
            bundle, reject = canonicalize_params(
                raw, pair_rules, ref_price,
                signal_interval_seconds=bar_interval_seconds,
                regime_candles=regime_candles,
            )
            if bundle is not None:
                sc = _replace(bundle.strategy_config, controller_compat=PHASE2_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)
                ec = _replace(bundle.engine_config, taker_probability=taker_prob)
                top_candidates.append({
                    "trial_number": trial.number,
                    "phase1_score": trial.value,
                    "params": trial.params,
                    "config": sc,
                    "engine_config": ec,
                })

        if not top_candidates:
            print(f"  SKIP: no valid configs to stress test")
            sweep_results.append({"connector": connector, "pair": pair,
                                  "signal_interval": signal_interval, "regime_interval": regime_interval,
                                  "status": "no_valid_configs", "robust_score": None})
            return

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

        # Signal cache for EMA: process-parallel precompute for Phase 2 (Stage 3).
        # Returns a SharedSignalCache containing one entry per unique signal_cache_key,
        # keyed on the regime-hashed effective dataset key.
        from pmm_lab.objective.phase2_parallel_directional import (
            precompute_unique_directional_signals,
        )
        _shared_cache = precompute_unique_directional_signals(
            top_candidates=top_candidates,
            candles=dev_candles,
            pair_rules=pair_rules,
            regime_candles=regime_candles,
            dataset_key="dev",
            max_workers=N_JOBS,
        )

        from pmm_lab.objective.stress_ema_regime_hold import _apply_scenario as _ema_apply_scenario
        def _apply_scenario_fn(strategy_cfg, engine_cfg, pair_rules, scenario):
            new_engine, new_rules = _ema_apply_scenario(engine_cfg, pair_rules, scenario)
            return strategy_cfg, new_engine, new_rules

        best, diag = select_best_stressed_candidate(
            top_candidates, dev_candles, pair_rules, bar_interval_seconds,
            scenarios=stress_scenarios,
            objective_version=OBJECTIVE_VERSION,
            shared_signal_cache=_shared_cache,
            dataset_key="dev",
            regime_candles=regime_candles,
            apply_scenario_fn=_apply_scenario_fn,
        )

        if best is None:
            print(f"  SKIP: no candidates survived stress testing")
            sweep_results.append({"connector": connector, "pair": pair,
                                  "signal_interval": signal_interval, "regime_interval": regime_interval,
                                  "status": "stress_fail", "robust_score": None})
            return

        best_config = best["config"]
        best_engine_config = best["engine_config"]
        best_stress = best["stress_report"]
        bm = best_stress.baseline_metrics

        pair_elapsed = time.time() - pair_start
        print(f"  Best: trial {best['trial_number']}  robust={best['robust_score']:.4f}  "
              f"PnL={bm.pnl_pct:.2f}%  trades={bm.trade_count}  ({pair_elapsed/60:.1f}min)")
        print(f"  Stress diag: evaluated={diag['candidates_evaluated']} "
              f"pruned={diag['candidates_pruned']} "
              f"cache_hits={diag['signal_cache_hits']} misses={diag['signal_cache_misses']}")

    except Exception as e:
        print(f"  SKIP: stress testing failed — {e}")
        sweep_results.append({"connector": connector, "pair": pair,
                              "signal_interval": signal_interval, "regime_interval": regime_interval,
                              "status": "stress_fail", "robust_score": None, "error": str(e)})
        return

    # ── Finalist validation ──
    val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT,
                          _regime_candles=regime_candles, use_numba_kernel=USE_NUMBA_KERNEL)
    val_engine = _replace(
        best_engine_config,
        refresh_close_mode=REFRESH_CLOSE_MODE,
        initial_base_balance=INITIAL_BASE_BALANCE,
        taker_probability=taker_prob,
    )

    recent_window_results = {}
    _shared_cache_full = SharedSignalCache()
    _recent_signals = _shared_cache_full.get_or_compute(
        val_config, "full", signal_candles, pair_rules,
        regime_candles=regime_candles,
    )

    for _rw_days in RECENT_REPORT_WINDOW_DAYS:
        try:
            _rw = evaluate_recent_window(
                full_candles=signal_candles, config=val_config, pair_rules=pair_rules,
                bar_interval_seconds=bar_interval_seconds,
                recent_days=_rw_days, run_stress=False,
                objective_version=OBJECTIVE_VERSION,
                precomputed_signals=_recent_signals,
                shared_signal_cache=_shared_cache_full,
                engine_config=val_engine,
                regime_candles=regime_candles,
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
            dev_candles_h, holdout_candles_h = split_holdout(signal_candles, 0.20, min_holdout_bars=50)
            holdout_start_idx = len(dev_candles_h)
        # Per-candidate engine_config (Stage 1 fix): EMA execution fields live on
        # engine_config, not strategy_config. Each candidate gets its own engine
        # config so holdout scoring uses the candidate's real execution params.
        holdout_candidates = [
            HoldoutCandidateSpec(
                strategy_config=val_config,
                engine_config=val_engine,
                development_score=best.get("robust_score", 0.0),
            )
        ]
        for t_idx in range(1, min(5, len(top_candidates))):
            tc = top_candidates[t_idx]
            tc_raw = dict(tc["params"], hold_mode="reentry", max_executors_per_side=1, total_amount_quote=300.0)
            tc_bundle, _ = canonicalize_params(
                tc_raw, pair_rules, ref_price,
                signal_interval_seconds=bar_interval_seconds,
                regime_candles=regime_candles,
            )
            if tc_bundle is not None:
                tc_cfg = _replace(
                    tc_bundle.strategy_config,
                    controller_compat=VALIDATION_CONTROLLER_COMPAT,
                    _regime_candles=regime_candles,
                    use_numba_kernel=USE_NUMBA_KERNEL,
                )
                tc_engine = _replace(
                    tc_bundle.engine_config,
                    refresh_close_mode=REFRESH_CLOSE_MODE,
                    initial_base_balance=INITIAL_BASE_BALANCE,
                    taker_probability=taker_prob,
                )
                holdout_candidates.append(
                    HoldoutCandidateSpec(
                        strategy_config=tc_cfg,
                        engine_config=tc_engine,
                        development_score=tc.get("phase1_score", 0.0),
                    )
                )
        holdout_report = evaluate_holdout(
            holdout_candles_h, holdout_candidates, pair_rules, bar_interval_seconds,
            run_stress=False, objective_version=OBJECTIVE_VERSION,
            full_candles=signal_candles, holdout_start_idx=holdout_start_idx,
            shared_signal_cache=_shared_cache_full,
            engine_config=val_engine,  # defensive fallback for specs with engine_config=None
            regime_candles=regime_candles,
        )
        print(f"  Holdout: {'PASS' if holdout_report.exported_holdout_passed else 'FAIL'}")
    except Exception as e:
        print(f"  Holdout: ERROR — {e}")

    sensitivity_report = None
    sensitivity_penalty = None
    try:
        def _ema_canon_adapter(params, pair_rules_arg, ref_price_arg, **kwargs):
            raw = dict(params)
            raw.setdefault("hold_mode", "reentry")
            raw.setdefault("max_executors_per_side", 1)
            raw.setdefault("total_amount_quote", 300.0)
            return canonicalize_params(
                raw, pair_rules_arg, ref_price_arg,
                signal_interval_seconds=bar_interval_seconds,
                regime_candles=regime_candles,
            )
        sensitivity_report = compute_sensitivity(
            best["params"], signal_candles, pair_rules, bar_interval_seconds, ref_price,
            objective_version=OBJECTIVE_VERSION,
            controller_compat=VALIDATION_CONTROLLER_COMPAT,
            shared_signal_cache=_shared_cache_full,
            canonicalize_fn=_ema_canon_adapter,
            regime_candles=regime_candles,
            perturb_params=EMA_PERTURBABLE_PARAMS,
            use_numba_kernel=USE_NUMBA_KERNEL,
        )
        sensitivity_penalty = sensitivity_report.sensitivity_penalty
        print(f"  Sensitivity: penalty={sensitivity_penalty:.4f}")
    except Exception as e:
        print(f"  Sensitivity: ERROR — {e}")

    cluster_report = None
    try:
        cluster_report = analyze_top_k(study, k=min(10, len(ranked)))
        print(f"  Clustering: {'CLUSTERED' if cluster_report.is_clustered else 'SCATTERED'}")
    except Exception as e:
        print(f"  Clustering: ERROR — {e}")

    parity_result = None
    long_parity_result = None
    try:
        _fix_base = Path("fixtures")
        if _fix_base.is_dir():
            _short = _fix_base / "ema_short_100bar"
            if _short.is_dir():
                _f = load_frozen_fixture(str(_short))
                parity_result = check_feature_parity_frozen_ema(
                    _f.candles, _f.regime_candles, _f.expected_features, _f.config_params,
                )
        print(f"  Parity: short={'PASS' if parity_result and parity_result.passed else 'N/A'}")
    except Exception as e:
        print(f"  Parity: ERROR — {e}")

    full_validation_executed = all([recent_window_result is not None, holdout_report is not None])

    best_metrics = bm
    best_obj = best_stress.baseline_objective
    result_entry = {
        "connector": connector,
        "pair": pair,
        "signal_interval": signal_interval,
        "regime_interval": regime_interval,
        "interval": signal_interval,  # alias for compatibility
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
        "best_engine_config": best_engine_config,
        "best_params": best["params"],
        "best_stress": best_stress,
        "dataset_hash": dataset_hash,
        "signal_hash": signal_hash,
        "regime_hash": regime_hash,
        "ema_dataset_identity": _identity,
        "n_candles": len(signal_candles),
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
        "phase1_below_threshold": phase1_below_threshold,
    }
    sweep_results.append(result_entry)

    # ── Validation state machine: fail-closed YAML placement (ML-DIR-001) ──
    MANDATORY_GATES = {
        "dataset_audit", "runtime_sanity", "objective_not_degenerate",
        "stress_not_collapsed", "yaml_validates",
        "walkforward_robust", "walkforward_positive_majority",
        "holdout_passed", "holdout_no_collapse",
        "sensitivity_stable", "recent_28d_passed", "top_k_clustered",
    }
    FROZEN_PARITY_POLICY = "advisory"
    if FROZEN_PARITY_POLICY == "mandatory":
        MANDATORY_GATES = MANDATORY_GATES | {"frozen_parity"}

    validation_status = "optimized_only"
    validation_errors = []
    mandatory_gates_failed = []
    yaml_path = None
    checks = {}
    validation_result = None
    wf_result = None

    try:
        export_params = ExportParams(
            connector_name=connector, trading_pair=pair,
            signal_interval=signal_interval, regime_interval=regime_interval,
        )
        _out_dir = Path(f"artifacts/direction-custom/ema_regime_hold/{connector}")
        _out_dir.mkdir(parents=True, exist_ok=True)
        _yaml_filename = f"{connector}_{pair.replace('-', '_').lower()}_{signal_interval}_{regime_interval}_screening_best.yml"
        _pending_dir = _out_dir / ".pending"
        _pending_dir.mkdir(parents=True, exist_ok=True)
        pending_yaml_path = str(_pending_dir / _yaml_filename)
        export_yaml(best_config, best_engine_config, export_params, Path(pending_yaml_path))
        validation_result = validate_yaml_file(Path(pending_yaml_path))
    except Exception as e:
        validation_errors.append(("export", type(e).__name__, str(e)))
        print(f"  Export/validate error: {e}")
        pending_yaml_path = None

    try:
        wf_result = run_walk_forward_dispatch(
            candles=signal_candles, config=val_config, pair_rules=pair_rules,
            bar_interval_seconds=bar_interval_seconds, dataset_hash=dataset_hash,
            train_days=train_days, test_days=test_days, step_days=step_days,
            objective_version=OBJECTIVE_VERSION,
            engine_config=val_engine,
            regime_candles=regime_candles,
            shared_signal_cache=_shared_cache_full,
            dataset_key="dev",
        )
        print(f"  Walk-forward: {len(wf_result.folds)} folds, aggregate={wf_result.aggregate_score:.4f}")
    except Exception as e:
        validation_errors.append(("walkforward", type(e).__name__, str(e)))
        print(f"  Walk-forward ERROR: {type(e).__name__}: {e}")
        wf_result = None

    try:
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
        mandatory_gates_failed = [
            name for name in MANDATORY_GATES if checks.get(name) is False
        ]
        if validation_errors:
            validation_status = "validation_error"
        elif mandatory_gates_failed:
            validation_status = "validated_fail"
        else:
            validation_status = "validated_pass"
    except Exception as e:
        validation_errors.append(("stop_ship_checks", type(e).__name__, str(e)))
        validation_status = "validation_error"
        print(f"  Stop-ship checks error: {e}")

    import shutil as _shutil
    if pending_yaml_path and Path(pending_yaml_path).exists():
        if validation_status == "validated_pass":
            yaml_path = str(_out_dir / _yaml_filename)
            _shutil.move(pending_yaml_path, yaml_path)
        else:
            _rejected_dir = _out_dir / "rejected"
            _rejected_dir.mkdir(parents=True, exist_ok=True)
            yaml_path = str(_rejected_dir / _yaml_filename)
            _shutil.move(pending_yaml_path, yaml_path)
            import json as _json
            _marker = Path(yaml_path).with_suffix("").as_posix() + "_REJECTED.json"
            Path(_marker).write_text(_json.dumps({
                "validation_status": validation_status,
                "mandatory_gates_failed": mandatory_gates_failed,
                "validation_errors": [
                    {"step": step, "type": t, "message": m}
                    for step, t, m in validation_errors
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dataset_hash": dataset_hash,
                "mandatory_gates_policy": {
                    "frozen_parity_policy": FROZEN_PARITY_POLICY,
                    "mandatory_gates": sorted(list(MANDATORY_GATES)),
                },
            }, indent=2))

    result_entry["status"] = validation_status
    result_entry["validation_status"] = validation_status
    result_entry["validation_errors"] = validation_errors
    result_entry["mandatory_gates_failed"] = mandatory_gates_failed
    result_entry["yaml_path"] = yaml_path
    result_entry["checks"] = checks

    try:
        _run_provenance = {
            "notebook": "direction-custom/ema_regime_hold",
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "n_jobs": N_JOBS,
            "objective_version": OBJECTIVE_VERSION,
            "search_controller_compat": SEARCH_CONTROLLER_COMPAT,
            "validation_controller_compat": VALIDATION_CONTROLLER_COMPAT,
            "refresh_close_mode": REFRESH_CLOSE_MODE,
            "initial_base_balance": INITIAL_BASE_BALANCE,
            "taker_probability": taker_prob,
            "trial_number": best["trial_number"],
            "signal_interval": signal_interval,
            "regime_interval": regime_interval,
            "validation_status": validation_status,
        }
        generate_report(
            study_name=study_name,
            dataset_summary={
                "connector": connector, "trading_pair": pair,
                "interval": f"{signal_interval}+{regime_interval}",
                "n_candles": len(signal_candles), "dataset_hash": dataset_hash,
                "n_trials_phase1": N_TRIALS, "n_candidates_stressed": len(top_candidates),
                "total_amount_quote_search_min": 50.0,
                "total_amount_quote_search_max": 500.0,
                "total_amount_quote_ideal": best_engine_config.total_amount_quote,
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
                "refresh_close_mode": REFRESH_CLOSE_MODE,
            },
            tp_min_notional_failures=getattr(best_metrics, "tp_min_notional_failures", 0),
            output_path=f"artifacts/direction-custom/ema_regime_hold/{connector}/{pair.replace('-', '_').lower()}_{signal_interval}_{regime_interval}_report.md",
        )
        _gates_pass = sum(1 for v in checks.values() if v)
        _gates_total = len(checks)
        result_entry["gates_pass"] = _gates_pass
        result_entry["gates_total"] = _gates_total
        _total_time = time.time() - pair_start
        print(f"  Total time: ({_total_time/60:.1f}min)  Gates: {_gates_pass}/{_gates_total}  Status: {validation_status}")
        if yaml_path:
            print(f"  YAML: {yaml_path}")
        if mandatory_gates_failed:
            print(f"  Failed mandatory gates: {mandatory_gates_failed}")
    except Exception as e:
        print(f"  Report error: {e}")

    return
if PAIR_JOBS <= 1:
    for pair_idx, pair_info in enumerate(candidates):
        try:
            _run_one_pair(pair_idx, pair_info)
        except Exception as _e:
            import traceback as _tb
            print(f"  [pair {pair_idx+1}] raised: {_e}")
            _tb.print_exc()
        _pair_bar.update(1)
else:
    from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _as_completed
    print(f"[pair-level] Running with PAIR_JOBS={PAIR_JOBS} threads x N_JOBS={N_JOBS} Optuna subprocesses per pair.")
    with _TPE(max_workers=PAIR_JOBS) as _pool:
        _futs = {
            _pool.submit(_run_one_pair, _pidx, _pinfo): (_pidx, _pinfo)
            for _pidx, _pinfo in enumerate(candidates)
        }
        for _fut in _as_completed(_futs):
            _pidx, _pinfo = _futs[_fut]
            try:
                _fut.result()
            except Exception as _e:
                import traceback as _tb
                print(f"  [parallel] pair {_pidx+1} raised: {_e}")
                _tb.print_exc()
            _pair_bar.update(1)

_pair_bar.close()

total_elapsed = time.time() - sweep_start
print(f"\n{'='*60}")
print(f"SWEEP COMPLETE: {len(candidates)} connector/pair combinations in {total_elapsed/60:.1f} minutes")
print(f"{'='*60}")
'''


def build_mr_cell8():
    return _common_header() + _mr_imports() + _common_preloop() + _mr_body()


def build_ema_cell8():
    return _common_header() + _ema_imports() + _common_preloop() + _ema_body()


def write_cell8(nb_path: Path, new_source: str) -> int:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    # Replace cell 8 source (store as single string so JSON is stable)
    nb["cells"][8]["source"] = new_source
    # Also clear outputs/execution_count for the replaced cell
    nb["cells"][8]["outputs"] = []
    nb["cells"][8]["execution_count"] = None
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    return len(new_source.splitlines())


def main():
    mr_src = build_mr_cell8()
    ema_src = build_ema_cell8()

    results = []
    for name, src in [
        ("mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb", mr_src),
        ("mean_reversion_bb_rsi_retest_sweep.ipynb", mr_src),
        ("ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb", ema_src),
        ("ema_regime_hold_retest_sweep.ipynb", ema_src),
    ]:
        path = NB_DIR / name
        lines = write_cell8(path, src)
        results.append((name, lines))

    for name, lines in results:
        print(f"{name}: {lines} lines")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
