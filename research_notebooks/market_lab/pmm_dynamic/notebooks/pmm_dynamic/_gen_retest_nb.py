"""One-shot generator for pmm_dynamic_retest_sweep.ipynb — run then delete this file."""
import json, hashlib, os

def _id():
    """Generate a unique 8-char hex cell id."""
    _id._counter = getattr(_id, '_counter', 0) + 1
    return hashlib.md5(f"retest-{_id._counter}".encode()).hexdigest()[:8]

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.split("\n"), "id": _id()}

def code(source):
    return {"cell_type": "code", "metadata": {}, "source": source.split("\n"),
            "outputs": [], "execution_count": None, "id": _id()}

# Load original notebook to extract Cell 8 (sweep loop) verbatim, then patch it
with open('pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb', encoding='utf-8') as f:
    orig = json.load(f)

# Get Cell 8 source as a single string
cell8_src = ''.join(orig['cells'][8]['source'])

# Patch: artifacts/sweep -> retest/sweep
cell8_src = cell8_src.replace('artifacts/sweep/', 'retest/sweep/')

# Patch: study_name = f"..." line
cell8_src = cell8_src.replace(
    'study_name = f"{connector}_{pair}_{interval}_sweep_v1"',
    'study_name = f"{connector}_{pair}_{interval}_retest_{_retest_date}"'
)

# Get Cell 10 (summary) source
cell10_src = ''.join(orig['cells'][10]['source'])

# Get Cell 12 (profitable detail) source
cell12_src = ''.join(orig['cells'][12]['source'])
cell12_src = cell12_src.replace('artifacts/sweep/', 'retest/sweep/')

# ── Build cells ──
cells = []

# Cell 0: Title markdown
cells.append(md(
"# PMM Dynamic Retest Sweep\n"
"\n"
"**Retest specific (pair, exchange) tuples with full optimization pipeline**\n"
"\n"
"Unlike the auto-discovery sweep, this notebook lets you specify exactly which\n"
"pairs to retest. All output goes to `retest/sweep/<connector>/` instead of\n"
"`artifacts/sweep/<connector>/`.\n"
"\n"
"1. Define your `RETEST_PAIRS` list below\n"
"2. The notebook loads metadata from MongoDB for only those pairs\n"
"3. Same full pipeline: walk-forward optimization, stress testing, finalist validation\n"
"4. Date-stamped Optuna study names prevent collisions with prior runs\n"
"\n"
"**Configuration:** Edit `RETEST_PAIRS` and sweep variables, then Run All."
))

# Cell 1: Imports (identical to original)
cells.append(code(''.join(orig['cells'][1]['source']).rstrip('\n')))

# Cell 2: Configuration markdown
cells.append(md(
"## 1. Configuration\n"
"\n"
"Edit `RETEST_PAIRS` and sweep variables below, then **Run All** cells."
))

# Cell 3: Configuration — replace CONNECTORS with RETEST_PAIRS
cells.append(code(
'# ==============================================================\n'
'# RETEST CONFIGURATION — edit these, then Run All\n'
'# ==============================================================\n'
'\n'
'# ── RETEST PAIR LIST ──\n'
'# Each tuple is (trading_pair, connector).\n'
'# Trading pairs use the format already in MongoDB (e.g. "XMR-USDT", "ARRR-USDT").\n'
'# Connectors are lowercase exchange names (e.g. "mexc", "nonkyc").\n'
'RETEST_PAIRS = [\n'
'    ("XMR-USDT",  "mexc"),\n'
'    ("HYPE-USDT", "mexc"),\n'
'    ("ARRR-USDT", "nonkyc"),\n'
']\n'
'\n'
'# Derive CONNECTORS automatically from RETEST_PAIRS\n'
'CONNECTORS = sorted(set(connector for _, connector in RETEST_PAIRS))\n'
'\n'
'QUOTE_ASSET = "*"             # Quote asset filter\n'
'N_TRIALS = 12000                 # Optuna trials per connector / pair\n'
'PERC_TRIALS_TEST = .05           # what percentage of the N_TRIALS should be completely random\n'
'TOP_N = 75                       # Top candidates to stress test\n'
'MIN_ROBUST_SCORE = -5.0           # Minimum robust score to export (0 = breakeven)\n'
'N_JOBS = 8                       # Parallel Optuna workers\n'
'\n'
'# Preferred interval per connector (add your own)\n'
'CONNECTOR_INTERVALS = {\n'
'    "nonkyc": "5m",\n'
'    "mexc": "5m",\n'
'}\n'
'DEFAULT_INTERVAL = "5m"\n'
'\n'
'# Minimum data requirement (days)\n'
'MIN_DATA_DAYS = 56\n'
'\n'
'# Maximum training window (days). Only the most recent N days of candle\n'
'# data will be used for walk-forward optimization. Set to None to use all\n'
'# available data (original behaviour).\n'
'MAX_TRAINING_DAYS = 180\n'
'\n'
'# Feature computation mode for search AND stress/validation.\n'
'SEARCH_CONTROLLER_COMPAT = False\n'
'\n'
'# Validation controller mode — True = controller-equivalent sliding window for finalist\n'
'# evaluation (holdout, recent-window, sensitivity).\n'
'VALIDATION_CONTROLLER_COMPAT = True\n'
'\n'
'# Stale data gate — skip pairs whose most recent candle is older than this\n'
'MAX_STALE_DAYS = 7\n'
'\n'
'# Phase-1 minimum score to proceed to stress testing\n'
'MIN_PHASE1_BEST_FOR_STRESS = -0.5\n'
'\n'
'OBJECTIVE_VERSION = 2\n'
'\n'
'# ==============================================================\n'
'\n'
'CONNECTORS = [c.strip().lower() for c in CONNECTORS]\n'
'INTERVALS_BY_CONNECTOR = {\n'
'    connector: CONNECTOR_INTERVALS.get(connector, DEFAULT_INTERVAL)\n'
'    for connector in CONNECTORS\n'
'}\n'
'\n'
'from pmm_lab.config.defaults import INTERVAL_SECONDS\n'
'\n'
'print(f"Retest pairs   : {len(RETEST_PAIRS)}")\n'
'print(f"Connectors     : {\', \'.join(CONNECTORS)}")\n'
'print(f"Intervals      : {\', \'.join(f\'{c}:{INTERVALS_BY_CONNECTOR[c]}\' for c in CONNECTORS)}")\n'
'print(f"Trials/pair    : {N_TRIALS}")\n'
'print(f"Top-N stress   : {TOP_N}")\n'
'print(f"Min score      : {MIN_ROBUST_SCORE}")\n'
'print(f"Min data days  : {MIN_DATA_DAYS}")\n'
'print(f"Search mode    : controller_compat={SEARCH_CONTROLLER_COMPAT}")\n'
'print(f"Max stale days : {MAX_STALE_DAYS}")\n'
'print(f"Max training   : {MAX_TRAINING_DAYS}d" if MAX_TRAINING_DAYS else "Max training   : unlimited")'
))

# Cell 4: Preflight (identical to original cell 4)
cells.append(code(''.join(orig['cells'][4]['source']).rstrip('\n')))

# Cell 5: Markdown — Load Requested Pairs
cells.append(md(
"## 2. Load Requested Pairs\n"
"\n"
"Query MongoDB for only the pairs specified in `RETEST_PAIRS`. Data-quality gates still apply."
))

# Cell 6: Load requested pairs (replaces auto-discovery)
cells.append(code(
'from pmm_lab.data.mongo import MongoCandleLoader\n'
'from pmm_lab.config.params import DataQuery\n'
'from pmm_lab.data.hashing import hash_candles\n'
'from datetime import datetime, timezone\n'
'\n'
'loader = MongoCandleLoader()\n'
'all_combos = loader.list_combos(connector=None, quote_asset=QUOTE_ASSET)\n'
'\n'
'now_ts = datetime.now(timezone.utc).timestamp()\n'
'\n'
'# Build lookup from all_combos for the requested pairs\n'
'combo_lookup = {}\n'
'for combo in all_combos:\n'
'    key = (combo["trading_pair"], combo["connector"], combo["interval"])\n'
'    combo_lookup[key] = combo\n'
'\n'
'# Deduplicate RETEST_PAIRS\n'
'seen_pairs = set()\n'
'deduped_retest = []\n'
'for pair_tuple in RETEST_PAIRS:\n'
'    if pair_tuple not in seen_pairs:\n'
'        seen_pairs.add(pair_tuple)\n'
'        deduped_retest.append(pair_tuple)\n'
'if len(deduped_retest) < len(RETEST_PAIRS):\n'
'    print(f"Deduplicated: {len(RETEST_PAIRS)} -> {len(deduped_retest)} unique pairs")\n'
'RETEST_PAIRS = deduped_retest\n'
'\n'
'# Filter requested pairs through data-quality gates\n'
'candidates = []\n'
'stale_exclusions = []\n'
'insufficient_exclusions = []\n'
'missing_pairs = []\n'
'\n'
'for trading_pair, connector in RETEST_PAIRS:\n'
'    interval = INTERVALS_BY_CONNECTOR.get(connector, DEFAULT_INTERVAL)\n'
'    key = (trading_pair, connector, interval)\n'
'    combo = combo_lookup.get(key)\n'
'\n'
'    if combo is None:\n'
'        missing_pairs.append({"connector": connector, "trading_pair": trading_pair,\n'
'                              "interval": interval, "reason": "not found in MongoDB"})\n'
'        print(f"  WARNING: {trading_pair} on {connector} ({interval}) not found in MongoDB — skipping")\n'
'        continue\n'
'\n'
'    # Cap effective start to training window\n'
'    effective_first_ts = combo["first_ts"]\n'
'    if MAX_TRAINING_DAYS is not None:\n'
'        training_cutoff_ts = combo["last_ts"] - (MAX_TRAINING_DAYS * 86400)\n'
'        effective_first_ts = max(effective_first_ts, training_cutoff_ts)\n'
'    data_days = (combo["last_ts"] - effective_first_ts) / 86400\n'
'\n'
'    if data_days < MIN_DATA_DAYS:\n'
'        insufficient_exclusions.append({\n'
'            "connector": connector,\n'
'            "trading_pair": trading_pair,\n'
'            "count": combo["count"],\n'
'            "interval": interval,\n'
'            "data_days": data_days,\n'
'            "reason": f"only {data_days:.0f} days of data, need {MIN_DATA_DAYS}",\n'
'        })\n'
'        print(f"  WARNING: {trading_pair} on {connector}: only {data_days:.0f} days of data, need {MIN_DATA_DAYS} — skipping")\n'
'        continue\n'
'\n'
'    # Stale-pair gate\n'
'    last_age_days = (now_ts - combo["last_ts"]) / 86400\n'
'    if last_age_days > MAX_STALE_DAYS:\n'
'        last_utc = datetime.fromtimestamp(combo["last_ts"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")\n'
'        stale_exclusions.append({\n'
'            "connector": connector,\n'
'            "trading_pair": trading_pair,\n'
'            "count": combo["count"],\n'
'            "interval": interval,\n'
'            "data_days": data_days,\n'
'            "last_age_days": last_age_days,\n'
'            "last_utc": last_utc,\n'
'            "reason": f"stale ({last_age_days:.1f}d old > {MAX_STALE_DAYS}d)",\n'
'        })\n'
'        print(f"  WARNING: {trading_pair} on {connector}: stale ({last_age_days:.1f}d old > {MAX_STALE_DAYS}d) — skipping")\n'
'        continue\n'
'\n'
'    candidates.append({\n'
'        "connector": connector,\n'
'        "trading_pair": trading_pair,\n'
'        "interval": interval,\n'
'        "count": combo["count"],\n'
'        "first_ts": effective_first_ts,\n'
'        "full_first_ts": combo["first_ts"],\n'
'        "last_ts": combo["last_ts"],\n'
'        "data_days": data_days,\n'
'    })\n'
'\n'
'candidates = sorted(candidates, key=lambda c: (c["connector"], c["trading_pair"]))\n'
'\n'
'print(f"\\n{\'=\'*60}")\n'
'print(f"Retest: {len(candidates)} of {len(RETEST_PAIRS)} requested pairs passed data-quality gates")\n'
'print(f"{\'=\'*60}")\n'
'\n'
'for connector in CONNECTORS:\n'
'    connector_candidates = [c for c in candidates if c["connector"] == connector]\n'
'    interval = INTERVALS_BY_CONNECTOR.get(connector, DEFAULT_INTERVAL)\n'
'    print(f"\\n{connector} / {interval}: {len(connector_candidates)} pair(s)")\n'
'    if connector_candidates:\n'
'        for c in connector_candidates:\n'
'            print(f"  {c[\'trading_pair\']:15s}  {c[\'count\']:>8,} candles  {c[\'data_days\']:5.1f} days")\n'
'    else:\n'
'        print("  (no eligible pairs)")\n'
'\n'
'if missing_pairs:\n'
'    print(f"\\nNot found in MongoDB: {len(missing_pairs)} pair(s):")\n'
'    for ex in missing_pairs:\n'
'        print(f"  {ex[\'connector\']:8s}  {ex[\'trading_pair\']:15s}  ({ex[\'interval\']})")\n'
'\n'
'if stale_exclusions:\n'
'    print(f"\\nExcluded {len(stale_exclusions)} stale pair(s) (last candle > {MAX_STALE_DAYS}d old):")\n'
'    for ex in stale_exclusions:\n'
'        print(f"  {ex[\'connector\']:8s}  {ex[\'trading_pair\']:15s}  last={ex[\'last_utc\']}  age={ex[\'last_age_days\']:.1f}d")\n'
'\n'
'if insufficient_exclusions:\n'
'    print(f"\\nExcluded {len(insufficient_exclusions)} pair(s) with insufficient data:")\n'
'    for ex in insufficient_exclusions:\n'
'        print(f"  {ex[\'connector\']:8s}  {ex[\'trading_pair\']:15s}  {ex[\'data_days\']:.1f} days")\n'
'\n'
'print(f"\\nTotal pairs to optimize: {len(candidates)}")'
))

# Cell 7: Sweep markdown (identical)
cells.append(md(''.join(orig['cells'][7]['source']).rstrip('\n')))

# Cell 8: Main sweep loop — patched version
# We need to add _retest_date computation before the loop and makedirs for retest/
# Insert _retest_date computation and makedirs right before the loop
retest_preamble = (
'# Compute retest date once for consistent study naming\n'
'_retest_date = datetime.now(timezone.utc).strftime("%Y%m%d")\n'
'\n'
'# Ensure retest output directories exist\n'
'for _c in CONNECTORS:\n'
'    os.makedirs(f"retest/sweep/{_c}", exist_ok=True)\n'
'\n'
)

# Find the position to insert: right before "rules_db = load_exchange_rules()"
insert_marker = "rules_db = load_exchange_rules()"
cell8_patched = cell8_src.replace(insert_marker, retest_preamble + insert_marker)

cells.append(code(cell8_patched.rstrip('\n')))

# Cell 9: Results Summary markdown (identical)
cells.append(md(''.join(orig['cells'][9]['source']).rstrip('\n')))

# Cell 10: Summary table (identical to original)
cells.append(code(cell10_src.rstrip('\n')))

# Cell 11: Profitable Pairs Detail markdown (identical)
cells.append(md(''.join(orig['cells'][11]['source']).rstrip('\n')))

# Cell 12: Profitable pairs detail (patched paths)
cells.append(code(cell12_src.rstrip('\n')))

# Cell 13: Cross-Pair Ranking markdown (NEW)
cells.append(md(
"## 6. Cross-Pair Ranking\n"
"\n"
"All completed pairs ranked by robust score, regardless of exchange."
))

# Cell 14: Cross-Pair Ranking code (NEW)
cells.append(code(
'# ── CROSS-PAIR RANKING ──\n'
'completed = [r for r in sweep_results if r["status"] == "complete"]\n'
'completed.sort(key=lambda r: r["robust_score"], reverse=True)\n'
'\n'
'if not completed:\n'
'    print("No completed pairs to rank.")\n'
'else:\n'
'    ranking_rows = []\n'
'    for rank, r in enumerate(completed, 1):\n'
'        ranking_rows.append({\n'
'            "Rank": rank,\n'
'            "Exchange": r["connector"],\n'
'            "Pair": r["pair"],\n'
'            "Robust Score": r["robust_score"],\n'
'            "PnL %": r["pnl_pct"],\n'
'            "Sharpe": r["sharpe"],\n'
'            "Max DD %": r["max_dd_pct"],\n'
'            "Trades": r["trade_count"],\n'
'            "Profit Factor": r["profit_factor"] if r["profit_factor"] != float(\'inf\') else float(\'nan\'),\n'
'            "Worst Stress": r.get("worst_scenario", ""),\n'
'            "All Checks Pass": "\\u2713" if r.get("all_checks_pass") else "\\u2717",\n'
'        })\n'
'\n'
'    ranking_df = pd.DataFrame(ranking_rows)\n'
'\n'
'    # Print text table\n'
'    print(f"{\'=\'*80}")\n'
'    print(f"  CROSS-PAIR RANKING (all exchanges, sorted by robust score)")\n'
'    print(f"{\'=\'*80}\\n")\n'
'\n'
'    profitable_ranked = [r for r in completed if r["robust_score"] >= MIN_ROBUST_SCORE]\n'
'    unprofitable_ranked = [r for r in completed if r["robust_score"] < MIN_ROBUST_SCORE]\n'
'\n'
'    if profitable_ranked:\n'
'        print(f"  --- PROFITABLE (robust >= {MIN_ROBUST_SCORE}) ---")\n'
'        for rank, r in enumerate(profitable_ranked, 1):\n'
'            pf = f"{r[\'profit_factor\']:.2f}" if r["profit_factor"] != float(\'inf\') else "inf"\n'
'            checks = "\\u2713" if r.get("all_checks_pass") else "\\u2717"\n'
'            print(f"  {rank:3d}. {r[\'connector\']:8s} {r[\'pair\']:15s}  "\n'
'                  f"robust={r[\'robust_score\']:+8.4f}  PnL={r[\'pnl_pct\']:+7.2f}%  "\n'
'                  f"sharpe={r[\'sharpe\']:+6.2f}  DD={r[\'max_dd_pct\']:6.2f}%  "\n'
'                  f"trades={r[\'trade_count\']:4d}  PF={pf:>6s}  "\n'
'                  f"worst={r.get(\'worst_scenario\', \'\'):20s}  checks={checks}")\n'
'\n'
'    if unprofitable_ranked:\n'
'        print(f"\\n  --- BELOW THRESHOLD (robust < {MIN_ROBUST_SCORE}) ---")\n'
'        offset = len(profitable_ranked)\n'
'        for rank, r in enumerate(unprofitable_ranked, offset + 1):\n'
'            pf = f"{r[\'profit_factor\']:.2f}" if r["profit_factor"] != float(\'inf\') else "inf"\n'
'            checks = "\\u2713" if r.get("all_checks_pass") else "\\u2717"\n'
'            print(f"  {rank:3d}. {r[\'connector\']:8s} {r[\'pair\']:15s}  "\n'
'                  f"robust={r[\'robust_score\']:+8.4f}  PnL={r[\'pnl_pct\']:+7.2f}%  "\n'
'                  f"sharpe={r[\'sharpe\']:+6.2f}  DD={r[\'max_dd_pct\']:6.2f}%  "\n'
'                  f"trades={r[\'trade_count\']:4d}  PF={pf:>6s}  "\n'
'                  f"worst={r.get(\'worst_scenario\', \'\'):20s}  checks={checks}")\n'
'\n'
'    print()\n'
'    display(ranking_df)'
))

# Cell 15: Next Steps markdown (updated paths)
cells.append(md(
"## 7. Next Steps\n"
"\n"
"For each exported pair:\n"
"1. **Review the report** in `retest/sweep/<connector>/`\n"
"2. **Verify stop-ship checks** and YAML validation results\n"
"3. **Paper trade** using Hummingbot's paper trading mode\n"
"4. **Monitor** for at least 1 week before live trading\n"
"5. **Compare** live performance to backtest expectations\n"
"\n"
"To retest a different set of pairs, edit `RETEST_PAIRS` in the configuration cell and Run All."
))

# ── Assemble notebook ──
nb = {
    "metadata": orig["metadata"],
    "nbformat": 4,
    "nbformat_minor": 5,
    "cells": [],
}

# Convert all cells: ensure source is list-of-lines format
for cell in cells:
    src = cell["source"]
    if isinstance(src, list):
        # Already a list — but we built them from split("\n") which doesn't add \n
        # Need to ensure each line except possibly the last ends with \n
        lines = []
        for i, line in enumerate(src):
            if i < len(src) - 1 and not line.endswith("\n"):
                lines.append(line + "\n")
            else:
                lines.append(line)
        cell["source"] = lines
    nb["cells"].append(cell)

out_path = "pmm_dynamic_retest_sweep.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Created {out_path} with {len(nb['cells'])} cells")
