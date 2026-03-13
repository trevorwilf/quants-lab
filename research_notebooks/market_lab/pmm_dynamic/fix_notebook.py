"""Rewrite notebook code cells to match actual pmm_lab API."""
import json

REPLACEMENTS = {}

REPLACEMENTS[1] = '''import sys, os, subprocess

# Ensure pmm_lab is importable
PMM_DIR = "/quants-lab/research_notebooks/market_lab/pmm_dynamic"
if PMM_DIR not in sys.path:
    sys.path.insert(0, PMM_DIR)
subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", PMM_DIR, "--quiet"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

import numpy as np
import pandas as pd
import optuna
import pmm_lab

print(f"Python version  : {sys.version.split()[0]}")
print(f"NumPy version   : {np.__version__}")
print(f"Pandas version  : {pd.__version__}")
print(f"Optuna version  : {optuna.__version__}")
print(f"pmm_lab version : {pmm_lab.__version__}")
print()
MONGO_URI = os.getenv("MONGO_URI", "")
OPTUNA_STORAGE = os.getenv("OPTUNA_STORAGE", "")
print(f"MONGO_URI       : {'SET' if MONGO_URI else 'NOT SET (will skip MongoDB cells)'}")
print(f"OPTUNA_STORAGE  : {'SET' if OPTUNA_STORAGE else 'NOT SET (will use SQLite)'}")'''

# Cell 3: MongoDB Connect — keep as-is per spec

REPLACEMENTS[5] = '''try:
    from pmm_lab.data.mongo import MongoCandleLoader

    if not MONGO_URI:
        raise EnvironmentError("MONGO_URI not set")

    loader = MongoCandleLoader()
    combos = loader.list_combos(quote_asset="USDT")
    print(f"Available USDT-quote combos: {len(combos)}")
    combos_df = pd.DataFrame(combos)
    display(combos_df)
except Exception as exc:
    print(f"[SKIP] Dataset discovery failed: {exc}")
    combos_df = pd.DataFrame()'''

REPLACEMENTS[7] = '''# --- Configuration: change these to match your dataset ---
CONNECTOR = "nonkyc"
TRADING_PAIR = "BTC-USDT"
INTERVAL = "5m"
BAR_INTERVAL_SECONDS = 300  # must match INTERVAL
# ----------------------------------------------------------'''

REPLACEMENTS[8] = '''try:
    from pmm_lab.data.mongo import MongoCandleLoader
    from pmm_lab.data.candles import validate_candles
    from pmm_lab.config.params import DataQuery
    from pmm_lab.data.hashing import hash_candles

    if not MONGO_URI:
        raise EnvironmentError("MONGO_URI not set")

    loader = MongoCandleLoader()
    query = DataQuery(connector=CONNECTOR, trading_pair=TRADING_PAIR, interval=INTERVAL)
    candles = loader.load_range(query)
    print(f"Loaded {len(candles):,} candles  [{candles['timestamp'][0]} .. {candles['timestamp'][-1]}]")

    audit = validate_candles(candles, interval=INTERVAL, strict=True)
    print(f"\\n--- Candle Audit Summary ---")
    print(f"  Total rows       : {audit.total_rows:,}")
    print(f"  Expected rows    : {audit.expected_rows:,}")
    print(f"  Missing rows     : {audit.missing_rows:,}")
    print(f"  Duplicates       : {audit.duplicate_count}")
    print(f"  OHLC violations  : {audit.ohlc_violations}")
    print(f"  Volume=0 bars    : {audit.volume_zero_count} ({audit.volume_zero_fraction:.2%})")
    print(f"  Strict pass      : {audit.passed_strict}")
    if audit.failure_reasons:
        for r in audit.failure_reasons:
            print(f"    FAIL: {r}")

    DATASET_HASH = hash_candles(candles)
    print(f"\\n  Dataset hash     : {DATASET_HASH[:16]}...")
except Exception as exc:
    print(f"[SKIP] Candle extraction/validation failed: {exc}")
    candles = None
    DATASET_HASH = None'''

REPLACEMENTS[10] = '''if candles is not None:
    zero_vol = np.sum(candles["volume"] == 0)
    total = len(candles)
    print(f"Volume=0 candles: {zero_vol} / {total} ({zero_vol/total:.2%})")
    print()
    print("Note: Forward-fill detection is deferred to v2.")
    print("Volume=0 bars are not filled by the simulator (volume > 0 required for fills).")
else:
    print("[SKIP] No candle data loaded.")'''

# Cell 12: Timestamp Semantics — keep as-is per spec

REPLACEMENTS[14] = '''try:
    from pmm_lab.features.pmm_dynamic_features import compute_pmm_dynamic_features, PMMDynamicConfig
    from pmm_lab.features.alignment import align_features

    if candles is None:
        raise ValueError("No candle data loaded.")

    feat_config = PMMDynamicConfig()
    features = compute_pmm_dynamic_features(candles, feat_config)
    aligned = align_features(features, timestamp_mode=timestamp_mode)

    print(f"Warmup ends at bar {aligned.warmup_end} (features valid from here)")
    print(f"\\nLast 5 bars:")
    for i in range(-5, 0):
        idx = len(candles) + i
        print(f"  Bar {idx}: ref_price={aligned.reference_price[idx]:.2f}, "
              f"spread_mult={aligned.spread_multiplier[idx]:.6f}, "
              f"natr={aligned.natr[idx]:.6f}")
except Exception as exc:
    print(f"[SKIP] Feature computation failed: {exc}")
    aligned = None'''

REPLACEMENTS[16] = '''try:
    from pmm_lab.sim.executor_model import SimConfig
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.config.params import PairRules, FeeConfig
    from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules

    if candles is None:
        raise ValueError("No candle data loaded.")

    # Load exchange rules for the target pair
    rules_db = load_exchange_rules()
    pair_rules = resolve_pair_rules(rules_db, CONNECTOR, TRADING_PAIR)

    # Default baseline config
    baseline_config = SimConfig(
        buy_spreads=[1.0, 2.0, 4.0],
        sell_spreads=[1.0, 2.0, 4.0],
        buy_amounts_pct=[0.33, 0.34, 0.33],
        sell_amounts_pct=[0.33, 0.34, 0.33],
        total_amount_quote=100.0,
    )

    runner = CandleSimRunner(baseline_config, pair_rules)
    baseline_result = runner.run(candles)

    print("=== Baseline Backtest Summary ===")
    print(f"  Trades completed : {len(baseline_result.trades)}")
    print(f"  Orders placed    : {baseline_result.n_orders_placed}")
    print(f"  Orders filled    : {baseline_result.n_orders_filled}")
    print(f"  Orders rejected  : {baseline_result.n_orders_rejected}")
    print(f"  Market exits     : {baseline_result.n_market_exits}")
    print(f"  Final equity     : {baseline_result.equity_curve[-1]:.2f}")
    print(f"  PnL (quote)      : {baseline_result.equity_curve[-1] - baseline_config.total_amount_quote:.2f}")
except Exception as exc:
    print(f"[SKIP] Baseline backtest failed: {exc}")
    baseline_result = None
    baseline_config = None'''

REPLACEMENTS[18] = '''try:
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.objective.objective import objective_v1

    if baseline_result is None:
        raise ValueError("No baseline result available.")

    metrics = compute_metrics(
        baseline_result,
        initial_equity=baseline_config.total_amount_quote,
        candles=candles,
        bar_interval_seconds=BAR_INTERVAL_SECONDS,
    )

    obj = objective_v1(metrics)

    print(f"=== Metrics ===")
    print(f"  PnL %          : {metrics.pnl_pct:.4f}")
    print(f"  Sharpe         : {metrics.sharpe:.4f}")
    print(f"  Max Drawdown % : {metrics.max_drawdown_pct:.4f}")
    print(f"  Trade count    : {metrics.trade_count}")
    print(f"  Profit factor  : {metrics.profit_factor:.4f}")
    print(f"  Total fees     : {metrics.total_fees_quote:.4f}")
    print(f"  Fee drag %     : {metrics.fee_drag_pct:.4f}")
    print()
    print(f"=== Objective Decomposition ===")
    print(f"  Raw score      : {obj.raw_score:.6f}")
    print(f"  PnL component  : {obj.pnl_component:.6f}")
    print(f"  Sharpe comp.   : {obj.sharpe_component:.6f}")
    print(f"  Drawdown comp. : {obj.drawdown_component:.6f}")
    print(f"  Fee drag comp. : {obj.fee_drag_component:.6f}")
    print(f"  Inventory comp.: {obj.inventory_component:.6f}")
    print(f"  Trade penalty  : {obj.trade_count_penalty:.6f}")
    print(f"  Rejected?      : {obj.is_rejected}")
except Exception as exc:
    print(f"[SKIP] Metrics/objective failed: {exc}")
    metrics = None
    obj = None'''

REPLACEMENTS[20] = '''try:
    from pmm_lab.objective.walkforward import run_walk_forward

    if candles is None or baseline_config is None:
        raise ValueError("No candle data or config available.")

    wf_result = run_walk_forward(
        candles=candles,
        config=baseline_config,
        pair_rules=pair_rules,
        bar_interval_seconds=BAR_INTERVAL_SECONDS,
        dataset_hash=DATASET_HASH,
        train_days=42.0,
        test_days=14.0,
        step_days=14.0,
    )

    print(f"Walk-forward: {len(wf_result.folds)} folds, aggregate score: {wf_result.aggregate_score:.4f}")
    print()
    rows = []
    for fr in wf_result.folds:
        rows.append({
            "Fold": fr.fold_index,
            "PnL %": f"{fr.test_metrics.pnl_pct:.2f}",
            "Sharpe": f"{fr.test_metrics.sharpe:.2f}",
            "MaxDD %": f"{fr.test_metrics.max_drawdown_pct:.2f}",
            "Trades": fr.test_metrics.trade_count,
            "Objective": f"{fr.test_objective.raw_score:.4f}",
        })
    display(pd.DataFrame(rows))
except Exception as exc:
    print(f"[SKIP] Walk-forward failed: {exc}")
    wf_result = None'''

REPLACEMENTS[22] = '''try:
    from pmm_lab.objective.stress import run_stress_tests

    if candles is None or baseline_config is None:
        raise ValueError("No candle data or config available.")

    stress_report = run_stress_tests(
        candles=candles,
        config=baseline_config,
        pair_rules=pair_rules,
        bar_interval_seconds=BAR_INTERVAL_SECONDS,
    )

    print(f"Stress tests: {len(stress_report.scenario_results)} scenarios")
    print(f"Worst scenario: {stress_report.worst_scenario} (score: {stress_report.worst_score:.4f})")
    print()
    rows = []
    for sr in stress_report.scenario_results:
        rows.append({
            "Scenario": sr.scenario.name,
            "PnL %": f"{sr.metrics.pnl_pct:.2f}",
            "Sharpe": f"{sr.metrics.sharpe:.2f}",
            "MaxDD %": f"{sr.metrics.max_drawdown_pct:.2f}",
            "Trades": sr.metrics.trade_count,
            "Objective": f"{sr.objective.raw_score:.4f}",
        })
    display(pd.DataFrame(rows))
except Exception as exc:
    print(f"[SKIP] Stress testing failed: {exc}")
    stress_report = None'''

REPLACEMENTS[24] = '''# --- Optimization configuration ---
N_TRIALS = 50
STUDY_NAME = f"{CONNECTOR}_{TRADING_PAIR}_{INTERVAL}_pmm_dynamic_v1"
# -----------------------------------
print(f"Study name: {STUDY_NAME}")
print(f"Trials: {N_TRIALS}")'''

REPLACEMENTS[25] = '''try:
    from pmm_lab.optuna.study import create_study, run_optimization
    from pmm_lab.optuna.objective_wrapper import create_objective
    from pmm_lab.optuna.callbacks import DegeneracyCheckCallback, TrialLoggingCallback

    if candles is None:
        raise ValueError("No candle data available.")

    ref_price = float(np.median(candles["close"]))

    study = create_study(
        study_name=STUDY_NAME,
        storage_url=OPTUNA_STORAGE if OPTUNA_STORAGE else None,
    )

    objective_fn = create_objective(
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=BAR_INTERVAL_SECONDS,
        dataset_hash=DATASET_HASH,
        reference_price=ref_price,
        train_days=42.0,
        test_days=14.0,
        step_days=14.0,
        run_stress=False,  # set True for full robustness (slower)
    )

    run_optimization(
        study, objective_fn, n_trials=N_TRIALS,
        callbacks=[TrialLoggingCallback(log_every=5), DegeneracyCheckCallback()],
    )

    n_complete = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    n_pruned = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])
    print(f"\\nOptimization complete. Completed: {n_complete}, Pruned: {n_pruned}")
    print(f"Best value: {study.best_value:.6f}")
except Exception as exc:
    print(f"[SKIP] Optuna optimization failed: {exc}")
    study = None'''

REPLACEMENTS[27] = '''try:
    if study is None:
        raise ValueError("No Optuna study available.")

    best = study.best_trial
    print("=== Best Trial ===")
    print(f"  Trial #   : {best.number}")
    print(f"  Objective : {best.value:.6f}")
    print(f"  Params    :")
    for k, v in sorted(best.params.items()):
        print(f"    {k:30s} = {v}")

    # Top-N comparison
    TOP_N = 10
    complete_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    sorted_trials = sorted(complete_trials, key=lambda t: t.value, reverse=True)[:TOP_N]
    rows = []
    for t in sorted_trials:
        rows.append({
            "Trial": t.number,
            "Objective": f"{t.value:.4f}",
            **{k: t.params.get(k, "") for k in ["buy_n_levels", "sell_n_levels", "stop_loss", "take_profit"]},
        })
    print(f"\\n=== Top {TOP_N} Trials ===")
    display(pd.DataFrame(rows))
except Exception as exc:
    print(f"[SKIP] Best-trial review failed: {exc}")'''

REPLACEMENTS[29] = '''try:
    from pmm_lab.export.hb_yaml import export_yaml, ExportParams
    from pmm_lab.export.validate_export import validate_yaml_file
    from pmm_lab.optuna.canonicalizer import canonicalize_params

    if study is None:
        raise ValueError("No Optuna study available.")

    # Reconstruct SimConfig from best trial params
    ref_price = float(np.median(candles["close"]))
    best_config, reject = canonicalize_params(study.best_trial.params, pair_rules, ref_price)
    if best_config is None:
        raise ValueError(f"Best trial params rejected: {reject}")

    export_params = ExportParams(
        connector_name=CONNECTOR,
        trading_pair=TRADING_PAIR,
        candles_connector=CONNECTOR,
        candles_trading_pair=TRADING_PAIR,
        interval=INTERVAL,
    )

    yaml_path = export_yaml(
        config=best_config,
        output_path=f"artifacts/{STUDY_NAME}_best.yaml",
        export_params=export_params,
        metadata={"dataset_hash": DATASET_HASH, "trial": study.best_trial.number,
                  "objective": study.best_value},
    )
    print(f"YAML exported to: {yaml_path}")

    validation = validate_yaml_file(yaml_path)
    print(f"Validation: {'PASS' if validation.valid else 'FAIL'} (mode: {validation.mode})")
    if not validation.valid:
        for err in validation.errors:
            print(f"  ERROR: {err}")
except Exception as exc:
    print(f"[SKIP] YAML export/validation failed: {exc}")'''

REPLACEMENTS[31] = '''try:
    from pmm_lab.report.report_md import generate_report, run_stop_ship_checks

    if study is None:
        raise ValueError("No study available.")

    # Build dataset summary
    dataset_summary = {
        "connector": CONNECTOR,
        "trading_pair": TRADING_PAIR,
        "interval": INTERVAL,
        "n_candles": len(candles) if candles is not None else 0,
        "dataset_hash": DATASET_HASH,
    }

    # Get best trial metrics from user attrs (if available) or recompute
    best_params_dict = study.best_trial.params

    # Run stop-ship checks
    checks = run_stop_ship_checks(
        best_metrics=metrics,
        best_objective=obj,
        walkforward_result=wf_result if 'wf_result' in dir() and wf_result else None,
        stress_report=stress_report if 'stress_report' in dir() and stress_report else None,
        dataset_hash=DATASET_HASH,
    )

    report_path = generate_report(
        study_name=STUDY_NAME,
        dataset_summary=dataset_summary,
        best_params=best_params_dict,
        best_metrics=metrics,
        best_objective=obj,
        walkforward_result=wf_result if 'wf_result' in dir() and wf_result else None,
        stress_report=stress_report if 'stress_report' in dir() and stress_report else None,
        stop_ship_checks=checks,
        output_path=f"artifacts/{STUDY_NAME}_report.md",
    )
    print(f"Report saved to: {report_path}")
except Exception as exc:
    print(f"[SKIP] Report generation failed: {exc}")'''


def main():
    with open('notebooks/pmm_dynamic_hyperbo.ipynb') as f:
        nb = json.load(f)

    for cell_idx, new_source in REPLACEMENTS.items():
        cell = nb['cells'][cell_idx]
        assert cell['cell_type'] == 'code', f"Cell {cell_idx} is {cell['cell_type']}, expected code"
        cell['source'] = new_source

    with open('notebooks/pmm_dynamic_hyperbo.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)

    print(f"Replaced {len(REPLACEMENTS)} code cells: {sorted(REPLACEMENTS.keys())}")

    # Verify
    with open('notebooks/pmm_dynamic_hyperbo.ipynb') as f:
        nb2 = json.load(f)
    sections = [c for c in nb2['cells'] if c['cell_type'] == 'markdown'
                and (c['source'] if isinstance(c['source'], str) else ''.join(c['source'])).startswith('#')]
    print(f"Notebook valid: {len(nb2['cells'])} cells, {len(sections)} sections")
    assert len(sections) >= 15, f"Expected >= 15 sections, got {len(sections)}"


if __name__ == '__main__':
    main()
