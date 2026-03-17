"""Script to create the multi-pair sweep notebook."""
import nbformat

nb = nbformat.v4.new_notebook()

# Cell 0 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell(
    '# PMM Dynamic Multi-Pair Sweep\n'
    '\n'
    '**Automated optimization across all available trading pairs**\n'
    '\n'
    'This notebook:\n'
    '1. Discovers all available pairs for a connector + quote asset from MongoDB\n'
    '2. For each pair with sufficient data:\n'
    '   - Runs 3000 Optuna trials (walk-forward, stress OFF)\n'
    '   - Stress-tests the top 50 candidates\n'
    '   - Evaluates the best stress-validated candidate\n'
    '3. Exports YAML configs and reports for profitable pairs\n'
    '4. Displays a summary comparison across all pairs\n'
    '\n'
    '**Configuration:** Edit the variables in the first code cell, then Run All.'
))

# Cell 1 - Code (Setup)
nb.cells.append(nbformat.v4.new_code_cell(
    'import sys, os, subprocess, time, logging\n'
    'from datetime import datetime, timezone\n'
    '\n'
    'PMM_DIR = "/quants-lab/research_notebooks/market_lab/pmm_dynamic"\n'
    'if PMM_DIR not in sys.path:\n'
    '    sys.path.insert(0, PMM_DIR)\n'
    'subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", PMM_DIR, "--quiet"],\n'
    '                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n'
    '\n'
    'import numpy as np\n'
    'import pandas as pd\n'
    'import optuna\n'
    'import pmm_lab\n'
    '\n'
    'optuna.logging.set_verbosity(optuna.logging.WARNING)\n'
    'logging.getLogger("pmm_lab").setLevel(logging.WARNING)\n'
    '\n'
    'print(f"pmm_lab {pmm_lab.__version__} | NumPy {np.__version__} | Optuna {optuna.__version__}")\n'
    '\n'
    'MONGO_URI = os.getenv("MONGO_URI", "")\n'
    'OPTUNA_STORAGE = os.getenv("OPTUNA_STORAGE", "")\n'
    'print(f"MONGO_URI      : {\'SET\' if MONGO_URI else \'NOT SET\'}")\n'
    'print(f"OPTUNA_STORAGE : {\'SET\' if OPTUNA_STORAGE else \'NOT SET (using SQLite)\'}")'
))

# Cell 2 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell(
    '## 1. Configuration\n'
    '\n'
    'Edit these variables to control the sweep. Then **Run All** cells below.'
))

# Cell 3 - Code (Configuration)
cell3_src = '''\
# ==============================================================
# SWEEP CONFIGURATION — edit these, then Run All
# ==============================================================

CONNECTOR = "nonkyc"           # Exchange connector to sweep
QUOTE_ASSET = "USDT"           # Quote asset filter (pairs ending in -USDT)
N_TRIALS = 3000                # Optuna trials per pair
TOP_N = 50                     # Top candidates to stress test
MIN_ROBUST_SCORE = 0.0         # Minimum robust score to export (0 = breakeven)
N_JOBS = 8                     # Parallel Optuna workers

# Preferred interval per connector (add your own)
CONNECTOR_INTERVALS = {
    "nonkyc": "5m",
    "mexc": "5m",
}

# Minimum data requirement (days)
MIN_DATA_DAYS = 28

# ==============================================================

INTERVAL = CONNECTOR_INTERVALS.get(CONNECTOR, "5m")

from pmm_lab.config.defaults import INTERVAL_SECONDS
BAR_INTERVAL_SECONDS = INTERVAL_SECONDS[INTERVAL]

print(f"Connector      : {CONNECTOR}")
print(f"Quote asset    : {QUOTE_ASSET}")
print(f"Interval       : {INTERVAL} ({BAR_INTERVAL_SECONDS}s/bar)")
print(f"Trials/pair    : {N_TRIALS}")
print(f"Top-N stress   : {TOP_N}")
print(f"Min score      : {MIN_ROBUST_SCORE}")
print(f"Min data days  : {MIN_DATA_DAYS}")'''
nb.cells.append(nbformat.v4.new_code_cell(cell3_src))

# Cell 4 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell(
    '## 2. Discover Available Pairs'
))

# Cell 5 - Code (Discover Pairs)
cell5_src = '''\
from pmm_lab.data.mongo import MongoCandleLoader
from pmm_lab.config.params import DataQuery
from pmm_lab.data.hashing import hash_candles

loader = MongoCandleLoader()
all_combos = loader.list_combos(connector=CONNECTOR, quote_asset=QUOTE_ASSET)

# Filter to our selected interval and minimum data
candidates = []
for combo in all_combos:
    if combo["interval"] != INTERVAL:
        continue
    data_days = (combo["last_ts"] - combo["first_ts"]) / 86400
    if data_days < MIN_DATA_DAYS:
        print(f"  SKIP {combo['trading_pair']:15s}  {combo['count']:>8,} candles  {data_days:5.1f} days (< {MIN_DATA_DAYS}d)")
        continue
    candidates.append({
        "trading_pair": combo["trading_pair"],
        "count": combo["count"],
        "first_ts": combo["first_ts"],
        "last_ts": combo["last_ts"],
        "data_days": data_days,
    })

print(f"\\n{'='*60}")
print(f"Found {len(candidates)} pairs with >= {MIN_DATA_DAYS} days of {INTERVAL} data on {CONNECTOR}:")
print(f"{'='*60}")
for c in candidates:
    print(f"  {c['trading_pair']:15s}  {c['count']:>8,} candles  {c['data_days']:5.1f} days")
print(f"\\nTotal pairs to optimize: {len(candidates)}")'''
nb.cells.append(nbformat.v4.new_code_cell(cell5_src))

# Cell 6 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell(
    '## 3. Sweep: Optimize Each Pair\n'
    '\n'
    'For each pair, the sweep:\n'
    '1. Loads and validates candles\n'
    '2. Auto-scales walk-forward windows to fit available data\n'
    '3. Runs 3000 Optuna trials (walk-forward, stress OFF)\n'
    '4. Stress-tests top 50 candidates\n'
    '5. Records the best stress-validated result'
))

# Cell 7 - Code (Main Sweep Loop)
cell7_src = '''\
from pmm_lab.data.candles import validate_candles
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.study import create_study
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

# Preload stress scenarios once (Task 4.1)
stress_scenarios = load_stress_scenarios()

rules_db = load_exchange_rules()
sweep_results = []
sweep_start = time.time()

for pair_idx, pair_info in enumerate(candidates):
    pair = pair_info["trading_pair"]
    print(f"\\n{'\\u2550'*60}")
    print(f"  [{pair_idx+1}/{len(candidates)}] {CONNECTOR} / {pair} / {INTERVAL}")
    print(f"{'\\u2550'*60}")

    pair_start = time.time()

    # ── Load candles ──
    try:
        query = DataQuery(connector=CONNECTOR, trading_pair=pair, interval=INTERVAL)
        candles = loader.load_range(query)
        audit = validate_candles(candles, interval=INTERVAL, strict=True)
        if not audit.passed_strict:
            print(f"  SKIP: audit failed — {audit.failure_reasons}")
            sweep_results.append({"pair": pair, "status": "audit_fail", "robust_score": None})
            continue
        dataset_hash = hash_candles(candles)
    except Exception as e:
        print(f"  SKIP: load failed — {e}")
        sweep_results.append({"pair": pair, "status": "load_fail", "robust_score": None})
        continue

    # ── Exchange rules ──
    try:
        pair_rules = resolve_pair_rules(rules_db, CONNECTOR, pair)
    except KeyError:
        # Fall back to connector defaults if pair-specific rules not found
        try:
            pair_rules = resolve_pair_rules(rules_db, CONNECTOR, "DEFAULT")
        except KeyError:
            print(f"  SKIP: no exchange rules for {CONNECTOR}/{pair}")
            sweep_results.append({"pair": pair, "status": "no_rules", "robust_score": None})
            continue

    ref_price = float(np.median(candles["close"]))

    # ── Auto-scale walk-forward windows ──
    dataset_days = len(candles) * BAR_INTERVAL_SECONDS / 86400
    if dataset_days >= 120:
        train_days, test_days, step_days = 42.0, 14.0, 14.0
    elif dataset_days >= 60:
        train_days, test_days, step_days = 21.0, 7.0, 7.0
    elif dataset_days >= 28:
        train_days, test_days, step_days = 10.0, 4.0, 4.0
    else:
        print(f"  SKIP: only {dataset_days:.1f} days of data")
        sweep_results.append({"pair": pair, "status": "insufficient_data", "robust_score": None})
        continue

    print(f"  Candles: {len(candles):,}  Days: {dataset_days:.1f}  "
          f"WF: {train_days}/{test_days}/{step_days}d  Ref: {ref_price:,.4f}")

    # ── Phase 1: Optimization ──
    study_name = f"{CONNECTOR}_{pair}_{INTERVAL}_sweep_v1"

    try:
        study = create_study(
            study_name=study_name,
            storage_url=OPTUNA_STORAGE if OPTUNA_STORAGE else None,
            n_startup_trials=int(N_TRIALS * 0.10),
        )

        objective_fn = create_objective(
            candles=candles,
            pair_rules=pair_rules,
            bar_interval_seconds=BAR_INTERVAL_SECONDS,
            dataset_hash=dataset_hash,
            reference_price=ref_price,
            train_days=train_days,
            test_days=test_days,
            step_days=step_days,
            run_stress=False,
        )

        study.optimize(
            objective_fn,
            n_trials=N_TRIALS,
            callbacks=[DegeneracyCheckCallback()],
            catch=(Exception,),
            n_jobs=N_JOBS,
        )

        n_complete = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        n_pruned = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])
        best_val = study.best_value if study.best_trial else REJECT_SCORE
        print(f"  Phase 1: {n_complete} complete, {n_pruned} pruned, best={best_val:.4f}")
    except Exception as e:
        print(f"  SKIP: optimization failed — {e}")
        sweep_results.append({"pair": pair, "status": "optim_fail", "robust_score": None})
        continue

    # ── Phase 2: Stress top N (with signal cache, dedup, early pruning) ──
    try:
        completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        ranked = sorted(completed, key=lambda t: t.value, reverse=True)
        top_trials = ranked[:min(TOP_N, len(ranked))]

        top_candidates = []
        for trial in top_trials:
            config, reject = canonicalize_params(trial.params, pair_rules, ref_price)
            if config is not None:
                top_candidates.append({
                    "trial_number": trial.number,
                    "phase1_score": trial.value,
                    "params": trial.params,
                    "config": config,
                })

        if not top_candidates:
            print(f"  SKIP: no valid configs to stress test")
            sweep_results.append({"pair": pair, "status": "no_valid_configs", "robust_score": None})
            continue

        # Deduplicate by full config fingerprint (Task 4.4)
        seen_configs = {}
        deduped_candidates = []
        for candidate in top_candidates:
            fingerprint = candidate["config"].to_fingerprint()
            if fingerprint not in seen_configs:
                seen_configs[fingerprint] = True
                deduped_candidates.append(candidate)
        print(f"  Deduped: {len(top_candidates)} -> {len(deduped_candidates)} unique configs")
        top_candidates = deduped_candidates

        # Signal cache + early pruning (Tasks 4.3, 4.5)
        signal_cache = {}
        best, diag = select_best_stressed_candidate(
            top_candidates, candles, pair_rules, BAR_INTERVAL_SECONDS,
            scenarios=stress_scenarios,
            signal_cache=signal_cache,
        )

        if best is None:
            print(f"  SKIP: no candidates survived stress testing")
            sweep_results.append({"pair": pair, "status": "stress_fail", "robust_score": None})
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
        sweep_results.append({"pair": pair, "status": "stress_fail", "robust_score": None})
        continue

    # ── Record result ──
    best_metrics = bm
    best_obj = best_stress.baseline_objective
    result_entry = {
        "pair": pair,
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
    }
    sweep_results.append(result_entry)

    # ── Export if profitable ──
    if best["robust_score"] >= MIN_ROBUST_SCORE:
        try:
            export_params = ExportParams(
                connector_name=CONNECTOR,
                trading_pair=pair,
                candles_connector=CONNECTOR,
                candles_trading_pair=pair,
                interval=INTERVAL,
            )

            yaml_path = export_yaml(
                config=best_config,
                output_path=f"artifacts/sweep/{CONNECTOR}/{pair}_{INTERVAL}_best.yaml",
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

            # Walk-forward for report
            wf_result = run_walk_forward(
                candles=candles, config=best_config, pair_rules=pair_rules,
                bar_interval_seconds=BAR_INTERVAL_SECONDS, dataset_hash=dataset_hash,
                train_days=train_days, test_days=test_days, step_days=step_days,
            )

            checks = run_stop_ship_checks(
                best_metrics=best_metrics, best_objective=best_obj,
                walkforward_result=wf_result, stress_report=best_stress,
                dataset_hash=dataset_hash,
            )

            generate_report(
                study_name=study_name,
                dataset_summary={
                    "connector": CONNECTOR, "trading_pair": pair, "interval": INTERVAL,
                    "n_candles": len(candles), "dataset_hash": dataset_hash,
                    "n_trials_phase1": N_TRIALS, "n_candidates_stressed": len(top_candidates),
                },
                best_params=best["params"], best_metrics=best_metrics, best_objective=best_obj,
                walkforward_result=wf_result, stress_report=best_stress,
                stop_ship_checks=checks,
                output_path=f"artifacts/sweep/{CONNECTOR}/{pair}_{INTERVAL}_report.md",
            )

            result_entry["exported"] = True
            result_entry["yaml_path"] = yaml_path
            all_pass = all(checks.values())
            result_entry["all_checks_pass"] = all_pass
            print(f"  EXPORTED  yaml={yaml_path}  checks={'ALL PASS' if all_pass else 'SOME FAIL'}")
        except Exception as e:
            print(f"  Export failed: {e}")
            result_entry["exported"] = False
    else:
        result_entry["exported"] = False
        print(f"  NOT PROFITABLE (robust={best['robust_score']:.4f} < {MIN_ROBUST_SCORE})")

total_elapsed = time.time() - sweep_start
print(f"\\n{'\\u2550'*60}")
print(f"SWEEP COMPLETE: {len(candidates)} pairs in {total_elapsed/60:.1f} minutes")
print(f"{'\\u2550'*60}")'''
nb.cells.append(nbformat.v4.new_code_cell(cell7_src))

# Cell 8 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell('## 4. Results Summary'))

# Cell 9 - Code (Summary Table)
cell9_src = '''\
# Build summary table
summary_rows = []
for r in sweep_results:
    row = {
        "Pair": r["pair"],
        "Status": r["status"],
    }
    if r["status"] == "complete":
        row.update({
            "Robust": f"{r['robust_score']:.2f}",
            "PnL%": f"{r['pnl_pct']:.2f}",
            "Sharpe": f"{r['sharpe']:.2f}",
            "MaxDD%": f"{r['max_dd_pct']:.2f}",
            "Trades": r["trade_count"],
            "PF": f"{r['profit_factor']:.2f}" if r["profit_factor"] != float('inf') else "\\u221e",
            "Fees": f"{r['total_fees']:.2f}",
            "WorstStress": r.get("worst_scenario", ""),
            "Exported": "\\u2713" if r.get("exported") else "\\u2717",
            "Checks": "PASS" if r.get("all_checks_pass") else "\\u2014",
        })
    else:
        row.update({k: "\\u2014" for k in ["Robust", "PnL%", "Sharpe", "MaxDD%", "Trades",
                                       "PF", "Fees", "WorstStress", "Exported", "Checks"]})
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)

# Sort: completed + exported first, then by robust score
def sort_key(row):
    if row["Status"] != "complete":
        return (2, 0)
    if row["Exported"] == "\\u2713":
        return (0, -float(row["Robust"]))
    return (1, -float(row["Robust"]))

summary_df["_sort"] = summary_df.apply(sort_key, axis=1)
summary_df = summary_df.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

print(f"{'='*60}")
print(f"  SWEEP RESULTS: {CONNECTOR} / {QUOTE_ASSET} / {INTERVAL}")
print(f"{'='*60}\\n")

n_complete = len([r for r in sweep_results if r["status"] == "complete"])
n_exported = len([r for r in sweep_results if r.get("exported")])
n_profitable = len([r for r in sweep_results if r["status"] == "complete" and r["robust_score"] >= MIN_ROBUST_SCORE])

print(f"  Total pairs scanned : {len(candidates)}")
print(f"  Completed           : {n_complete}")
print(f"  Profitable          : {n_profitable} (robust score >= {MIN_ROBUST_SCORE})")
print(f"  Exported            : {n_exported}")
print()

display(summary_df)'''
nb.cells.append(nbformat.v4.new_code_cell(cell9_src))

# Cell 10 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell('## 5. Profitable Pairs Detail'))

# Cell 11 - Code (Profitable Pairs Detail)
cell11_src = '''\
profitable = [r for r in sweep_results if r["status"] == "complete"
              and r["robust_score"] is not None and r["robust_score"] >= MIN_ROBUST_SCORE]
profitable.sort(key=lambda r: r["robust_score"], reverse=True)

if not profitable:
    print("No profitable pairs found in this sweep.")
    print(f"Try adjusting MIN_ROBUST_SCORE (currently {MIN_ROBUST_SCORE}) or running on a different connector/interval.")
else:
    for i, r in enumerate(profitable):
        print(f"\\n{'\\u2500'*60}")
        print(f"  #{i+1}  {r['pair']}  (robust={r['robust_score']:.4f})")
        print(f"{'\\u2500'*60}")
        print(f"  PnL %       : {r['pnl_pct']:.4f}")
        print(f"  Sharpe      : {r['sharpe']:.4f}")
        print(f"  Max DD %    : {r['max_dd_pct']:.4f}")
        print(f"  Trades      : {r['trade_count']}")
        print(f"  Profit Fac. : {r['profit_factor']:.4f}")
        print(f"  Fees        : {r['total_fees']:.4f}")
        print(f"  Worst stress: {r['worst_scenario']} ({r['worst_score']:.4f})")
        print(f"  Data        : {r['n_candles']:,} candles, {r['dataset_days']:.1f} days")
        if r.get("yaml_path"):
            print(f"  YAML        : {r['yaml_path']}")
        print(f"  Checks      : {'ALL PASS' if r.get('all_checks_pass') else 'SOME FAILED'}")

    print(f"\\n{'='*60}")
    print(f"  {len(profitable)} profitable pair(s) found!")
    print(f"  Check artifacts/sweep/{CONNECTOR}/ for configs and reports.")
    print(f"{'='*60}")'''
nb.cells.append(nbformat.v4.new_code_cell(cell11_src))

# Cell 12 - Markdown
nb.cells.append(nbformat.v4.new_markdown_cell(
    '## 6. Next Steps\n'
    '\n'
    'For each exported pair:\n'
    '1. **Review the report** in `artifacts/sweep/<connector>/`\n'
    '2. **Verify stop-ship checks** all pass\n'
    '3. **Paper trade** using Hummingbot\'s paper trading mode\n'
    '4. **Monitor** for at least 1 week before live trading\n'
    '5. **Compare** live performance to backtest expectations\n'
    '\n'
    'To re-run for a different connector, change `CONNECTOR` in the configuration cell and Run All.'
))

nbformat.write(nb, 'notebooks/pmm_dynamic_multi_pair_sweep.ipynb')
print(f"Created notebook with {len(nb.cells)} cells")
print(f"  Code cells: {len([c for c in nb.cells if c.cell_type == 'code'])}")
print(f"  Markdown cells: {len([c for c in nb.cells if c.cell_type == 'markdown'])}")
