"""LEGACY — this module emits the OLD result schema
(best_score/trading_pair/binding_frac). It is retained for git history only
and MUST NOT be imported or executed. The canonical generator is
`_build_cell8.py` plus `_build_cell10.py` plus `create_sweep_nb_directional.py`.

Original one-shot builder for the four direction-custom sweep notebooks.
Transforms the authoritative `notebooks/pmm_dynamic/pmm_dynamic_*_sweep*.ipynb`
files by:
  - Keeping the same cell count and markdown/code alternation.
  - Replacing strategy-specific imports and helper calls.
  - Fully rewriting cell 3 with the strategy-specific configuration per
    section 2C of the phase-2 delta prompt.
  - For EMA, extending cells 6 (discovery) and 8 (sweep loop) to load both
    signal-interval and regime-interval candles per pair.
"""

import sys
raise RuntimeError(
    "_build_from_pmm_LEGACY_DO_NOT_USE.py must not be executed. "
    "Use _build_cell8.py / _build_cell10.py / create_sweep_nb_directional.py instead."
)

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Dict, List

PMM_DIR = Path(__file__).resolve().parent.parent / "pmm_dynamic"
OUT_DIR = Path(__file__).resolve().parent


# -------------------- Cell 3 configuration bodies --------------------

MR_MULTI_CELL3 = '''\
# ==============================================================
# MR BB+RSI MULTI-EXCHANGE SWEEP CONFIGURATION
# ==============================================================
# Mirrors the PMM Dynamic multi-exchange sweep. Trial-count guidance:
#   3000–5000: coarse screening / pair triage
#   8000–10000: good default for a serious cross-exchange search
#   12000–15000: only for finalists or very noisy pairs
# For this sweep we default to 500 (per user directive) — raise for
# production runs. All D1–D20 design decisions from phase-1 stand.
# ==============================================================

CONNECTORS = ["mexc", "nonkyc"]
QUOTE_ASSET = "*"
N_TRIALS = 500
PERC_TRIALS_TEST = 0.05
TOP_N = 100
MIN_ROBUST_SCORE = -5.0
N_JOBS = 8

CONNECTOR_INTERVALS = {"nonkyc": "5m", "mexc": "5m"}
DEFAULT_INTERVAL = "5m"

MIN_DATA_DAYS = 56
MAX_STALE_DAYS = 7
MAX_TRAINING_DAYS = 180

SEARCH_CONTROLLER_COMPAT = False
VALIDATION_CONTROLLER_COMPAT = True
PHASE2_CONTROLLER_COMPAT = True

REFRESH_CLOSE_MODE = "market_close"
INITIAL_BASE_BALANCE = 0.0

TAKER_PROBABILITY_BY_CONNECTOR = {"nonkyc": 0.10, "mexc": 0.0}
DEFAULT_TAKER_PROBABILITY = 0.0

MIN_PHASE1_BEST_FOR_STRESS = -0.5
OBJECTIVE_VERSION = 2

RECENT_BLOCKING_WINDOW_DAYS = 28
RECENT_INFORMATIONAL_WINDOW_DAYS = [14, 7]
RECENT_REPORT_WINDOW_DAYS = sorted(
    dict.fromkeys([RECENT_BLOCKING_WINDOW_DAYS] + RECENT_INFORMATIONAL_WINDOW_DAYS),
    reverse=True,
)

CONNECTORS = [c.strip().lower() for c in CONNECTORS]
INTERVALS_BY_CONNECTOR = {c: CONNECTOR_INTERVALS.get(c, DEFAULT_INTERVAL) for c in CONNECTORS}

from pmm_lab.config.defaults import INTERVAL_SECONDS

print(f"Strategy       : mean_reversion_bb_rsi_v1")
print(f"Connectors     : {', '.join(CONNECTORS)}")
print(f"Quote asset    : {QUOTE_ASSET}")
print(f"Intervals      : {', '.join(f'{c}:{INTERVALS_BY_CONNECTOR[c]}' for c in CONNECTORS)}")
print(f"Trials/pair    : {N_TRIALS}")
print(f"Top-N stress   : {TOP_N}")
print(f"Min score      : {MIN_ROBUST_SCORE}")
print(f"Min data days  : {MIN_DATA_DAYS}")
print(f"Search mode    : controller_compat={SEARCH_CONTROLLER_COMPAT}")
print(f"Max stale days : {MAX_STALE_DAYS}")
print(f"Max training   : {MAX_TRAINING_DAYS}d" if MAX_TRAINING_DAYS else "Max training   : unlimited")
print(f"Recent blocker : {RECENT_BLOCKING_WINDOW_DAYS}d")
print(f"Refresh mode   : {REFRESH_CLOSE_MODE}")
print(f"Initial base   : {INITIAL_BASE_BALANCE}")
print(f"Recent info    : {', '.join(f'{d}d' for d in RECENT_INFORMATIONAL_WINDOW_DAYS)}")
'''


MR_RETEST_CELL3 = '''\
# ==============================================================
# MR BB+RSI RETEST SWEEP CONFIGURATION
# ==============================================================
# Retest pattern: optimize a user-provided finalist list rather than
# discovering all pairs. Cross-pair ranking is added in cells 13-14.
# ==============================================================

RETEST_PAIRS = [
    ("XMR-USDT", "nonkyc"),
    ("XMR-USDT", "mexc"),
    # ADD MORE PAIRS AS FINALISTS EMERGE
]
CONNECTORS = sorted(set(connector for _, connector in RETEST_PAIRS))

QUOTE_ASSET = "*"
N_TRIALS = 500
PERC_TRIALS_TEST = 0.05
TOP_N = 75
MIN_ROBUST_SCORE = -5.0
N_JOBS = 8

CONNECTOR_INTERVALS = {"nonkyc": "5m", "mexc": "5m"}
DEFAULT_INTERVAL = "5m"

MIN_DATA_DAYS = 56
MAX_STALE_DAYS = 7
MAX_TRAINING_DAYS = 180

SEARCH_CONTROLLER_COMPAT = False
VALIDATION_CONTROLLER_COMPAT = True
PHASE2_CONTROLLER_COMPAT = True

REFRESH_CLOSE_MODE = "market_close"
INITIAL_BASE_BALANCE = 0.0

TAKER_PROBABILITY_BY_CONNECTOR = {"nonkyc": 0.10, "mexc": 0.0}
DEFAULT_TAKER_PROBABILITY = 0.0

MIN_PHASE1_BEST_FOR_STRESS = -0.5
OBJECTIVE_VERSION = 2

RECENT_BLOCKING_WINDOW_DAYS = 28
RECENT_INFORMATIONAL_WINDOW_DAYS = [14, 7]
RECENT_REPORT_WINDOW_DAYS = sorted(
    dict.fromkeys([RECENT_BLOCKING_WINDOW_DAYS] + RECENT_INFORMATIONAL_WINDOW_DAYS),
    reverse=True,
)

CONNECTORS = [c.strip().lower() for c in CONNECTORS]
INTERVALS_BY_CONNECTOR = {c: CONNECTOR_INTERVALS.get(c, DEFAULT_INTERVAL) for c in CONNECTORS}

from pmm_lab.config.defaults import INTERVAL_SECONDS

print(f"Strategy       : mean_reversion_bb_rsi_v1 (retest)")
print(f"Retest pairs   : {RETEST_PAIRS}")
print(f"Connectors     : {', '.join(CONNECTORS)}")
print(f"Trials/pair    : {N_TRIALS}")
print(f"Top-N stress   : {TOP_N}")
print(f"Max training   : {MAX_TRAINING_DAYS}d" if MAX_TRAINING_DAYS else "Max training   : unlimited")
'''


EMA_MULTI_CELL3 = '''\
# ==============================================================
# EMA REGIME-HOLD MULTI-EXCHANGE SWEEP CONFIGURATION
# ==============================================================
# EMA is multi-timeframe — signal_interval for fast bars + regime_interval
# for slow (trend/regime) detection. Pairs must have BOTH intervals in Mongo.
# Default is None because regime shifts ARE the signal — capping history
# would discard useful information. D4 forces hold_mode='reentry'.
# ==============================================================

CONNECTORS = ["mexc", "nonkyc"]
QUOTE_ASSET = "*"
N_TRIALS = 500
PERC_TRIALS_TEST = 0.05
TOP_N = 100
MIN_ROBUST_SCORE = -5.0
N_JOBS = 8

# EMA is multi-timeframe
SIGNAL_CONNECTOR_INTERVALS = {"nonkyc": "5m", "mexc": "5m"}
REGIME_CONNECTOR_INTERVALS = {"nonkyc": "4h", "mexc": "4h"}
DEFAULT_SIGNAL_INTERVAL = "5m"
DEFAULT_REGIME_INTERVAL = "4h"

MIN_DATA_DAYS = 120                  # EMA needs more history for 4h regime warmup
MAX_STALE_DAYS = 7
MAX_TRAINING_DAYS = None             # None = use all; regime shifts ARE the signal

SEARCH_CONTROLLER_COMPAT = False
VALIDATION_CONTROLLER_COMPAT = True
PHASE2_CONTROLLER_COMPAT = True

REFRESH_CLOSE_MODE = "market_close"
INITIAL_BASE_BALANCE = 0.0

TAKER_PROBABILITY_BY_CONNECTOR = {"nonkyc": 0.10, "mexc": 0.0}
DEFAULT_TAKER_PROBABILITY = 0.0

MIN_PHASE1_BEST_FOR_STRESS = -0.5
OBJECTIVE_VERSION = 2

RECENT_BLOCKING_WINDOW_DAYS = 28
RECENT_INFORMATIONAL_WINDOW_DAYS = [14, 7]
RECENT_REPORT_WINDOW_DAYS = sorted(
    dict.fromkeys([RECENT_BLOCKING_WINDOW_DAYS] + RECENT_INFORMATIONAL_WINDOW_DAYS),
    reverse=True,
)

CONNECTORS = [c.strip().lower() for c in CONNECTORS]

from pmm_lab.config.defaults import INTERVAL_SECONDS

print(f"Strategy       : ema_regime_hold_v1")
print(f"Connectors     : {', '.join(CONNECTORS)}")
print(f"Signal intvls  : {SIGNAL_CONNECTOR_INTERVALS}")
print(f"Regime intvls  : {REGIME_CONNECTOR_INTERVALS}")
print(f"Trials/pair    : {N_TRIALS}")
print(f"Min data days  : {MIN_DATA_DAYS}")
print(f"Max training   : {MAX_TRAINING_DAYS if MAX_TRAINING_DAYS else 'unlimited'}")
print(f"Max stale days : {MAX_STALE_DAYS}")
'''


EMA_RETEST_CELL3 = '''\
# ==============================================================
# EMA REGIME-HOLD RETEST SWEEP CONFIGURATION
# ==============================================================

RETEST_PAIRS = [
    ("XMR-USDT", "nonkyc"),
    ("XMR-USDT", "mexc"),
    # ADD MORE PAIRS AS FINALISTS EMERGE
]
CONNECTORS = sorted(set(connector for _, connector in RETEST_PAIRS))

QUOTE_ASSET = "*"
N_TRIALS = 500
PERC_TRIALS_TEST = 0.05
TOP_N = 75
MIN_ROBUST_SCORE = -5.0
N_JOBS = 8

SIGNAL_CONNECTOR_INTERVALS = {"nonkyc": "5m", "mexc": "5m"}
REGIME_CONNECTOR_INTERVALS = {"nonkyc": "4h", "mexc": "4h"}
DEFAULT_SIGNAL_INTERVAL = "5m"
DEFAULT_REGIME_INTERVAL = "4h"

MIN_DATA_DAYS = 120
MAX_STALE_DAYS = 7
MAX_TRAINING_DAYS = None

SEARCH_CONTROLLER_COMPAT = False
VALIDATION_CONTROLLER_COMPAT = True
PHASE2_CONTROLLER_COMPAT = True

REFRESH_CLOSE_MODE = "market_close"
INITIAL_BASE_BALANCE = 0.0

TAKER_PROBABILITY_BY_CONNECTOR = {"nonkyc": 0.10, "mexc": 0.0}
DEFAULT_TAKER_PROBABILITY = 0.0

MIN_PHASE1_BEST_FOR_STRESS = -0.5
OBJECTIVE_VERSION = 2

RECENT_BLOCKING_WINDOW_DAYS = 28
RECENT_INFORMATIONAL_WINDOW_DAYS = [14, 7]
RECENT_REPORT_WINDOW_DAYS = sorted(
    dict.fromkeys([RECENT_BLOCKING_WINDOW_DAYS] + RECENT_INFORMATIONAL_WINDOW_DAYS),
    reverse=True,
)

CONNECTORS = [c.strip().lower() for c in CONNECTORS]

from pmm_lab.config.defaults import INTERVAL_SECONDS

print(f"Strategy       : ema_regime_hold_v1 (retest)")
print(f"Retest pairs   : {RETEST_PAIRS}")
print(f"Trials/pair    : {N_TRIALS}")
'''


# -------------------- Cell 6 transformations --------------------

EMA_MULTI_CELL6 = '''\
from pmm_lab.data.mongo import MongoCandleLoader
from pmm_lab.config.params import DataQuery
from pmm_lab.data.hashing import hash_candles
from datetime import datetime, timezone

loader = MongoCandleLoader()
all_combos = loader.list_combos(connector=None, quote_asset=QUOTE_ASSET)

now_ts = datetime.now(timezone.utc).timestamp()

# EMA needs BOTH signal_interval AND regime_interval candles per (connector, pair).
pair_groups = {}
for combo in all_combos:
    connector = combo["connector"]
    if connector not in CONNECTORS:
        continue
    signal_i = SIGNAL_CONNECTOR_INTERVALS.get(connector, DEFAULT_SIGNAL_INTERVAL)
    regime_i = REGIME_CONNECTOR_INTERVALS.get(connector, DEFAULT_REGIME_INTERVAL)
    if combo["interval"] not in (signal_i, regime_i):
        continue
    key = (connector, combo["trading_pair"])
    pair_groups.setdefault(key, {})[combo["interval"]] = combo

candidates = []
stale_exclusions = []
insufficient_exclusions = []
missing_interval_exclusions = []

for (connector, pair), ivs in pair_groups.items():
    signal_i = SIGNAL_CONNECTOR_INTERVALS.get(connector, DEFAULT_SIGNAL_INTERVAL)
    regime_i = REGIME_CONNECTOR_INTERVALS.get(connector, DEFAULT_REGIME_INTERVAL)
    if signal_i not in ivs or regime_i not in ivs:
        missing_interval_exclusions.append({
            "connector": connector, "trading_pair": pair,
            "present": sorted(ivs.keys()),
            "reason": f"missing {signal_i}" if signal_i not in ivs else f"missing {regime_i}",
        })
        continue
    s = ivs[signal_i]
    r = ivs[regime_i]

    effective_signal_first = s["first_ts"]
    effective_regime_first = r["first_ts"]
    if MAX_TRAINING_DAYS is not None:
        cutoff = min(s["last_ts"], r["last_ts"]) - (MAX_TRAINING_DAYS * 86400)
        effective_signal_first = max(effective_signal_first, cutoff)
        effective_regime_first = max(effective_regime_first, cutoff)

    effective_first_ts = max(effective_signal_first, effective_regime_first)
    effective_last_ts = min(s["last_ts"], r["last_ts"])
    data_days = (effective_last_ts - effective_first_ts) / 86400

    if data_days < MIN_DATA_DAYS:
        insufficient_exclusions.append({
            "connector": connector, "trading_pair": pair,
            "data_days": data_days,
            "reason": f"< {MIN_DATA_DAYS}d cross-interval data",
        })
        continue

    last_age_days = (now_ts - effective_last_ts) / 86400
    if last_age_days > MAX_STALE_DAYS:
        stale_exclusions.append({
            "connector": connector, "trading_pair": pair,
            "last_age_days": last_age_days,
            "reason": f"stale ({last_age_days:.1f}d old > {MAX_STALE_DAYS}d)",
        })
        continue

    candidates.append({
        "connector": connector, "trading_pair": pair,
        "signal_interval": signal_i, "regime_interval": regime_i,
        "signal_first_ts": effective_signal_first,
        "regime_first_ts": effective_regime_first,
        "effective_first_ts": effective_first_ts,
        "signal_last_ts": s["last_ts"],
        "regime_last_ts": r["last_ts"],
        "signal_count": s["count"],
        "regime_count": r["count"],
        "data_days": data_days,
    })

candidates = sorted(candidates, key=lambda c: (c["connector"], c["trading_pair"]))

print(f"\\n{'='*60}")
print(f"Found {len(candidates)} connector/pair combos with >= {MIN_DATA_DAYS}d of BOTH intervals")
print(f"{'='*60}")

for connector in CONNECTORS:
    s = [c for c in candidates if c["connector"] == connector]
    signal_i = SIGNAL_CONNECTOR_INTERVALS.get(connector, DEFAULT_SIGNAL_INTERVAL)
    regime_i = REGIME_CONNECTOR_INTERVALS.get(connector, DEFAULT_REGIME_INTERVAL)
    print(f"\\n{connector} / {signal_i}+{regime_i}: {len(s)} pair(s)")
    for c in s:
        print(f"  {c['trading_pair']:15s} {c['data_days']:6.1f}d  "
              f"signal={c['signal_count']:>7,} regime={c['regime_count']:>5,}")

if missing_interval_exclusions:
    print(f"\\nExcluded {len(missing_interval_exclusions)} pair(s) missing an interval:")
    for ex in missing_interval_exclusions[:10]:
        print(f"  {ex['connector']:8s} {ex['trading_pair']:15s} {ex['reason']}")

if stale_exclusions:
    print(f"\\nExcluded {len(stale_exclusions)} stale pair(s)")
if insufficient_exclusions:
    print(f"\\nExcluded {len(insufficient_exclusions)} pair(s) with insufficient data")

print(f"\\nTotal to optimize: {len(candidates)}")
'''


EMA_RETEST_CELL6 = '''\
from pmm_lab.data.mongo import MongoCandleLoader
from pmm_lab.config.params import DataQuery
from pmm_lab.data.hashing import hash_candles
from datetime import datetime, timezone

loader = MongoCandleLoader()

candidates = []
for pair, connector in RETEST_PAIRS:
    signal_i = SIGNAL_CONNECTOR_INTERVALS.get(connector, DEFAULT_SIGNAL_INTERVAL)
    regime_i = REGIME_CONNECTOR_INTERVALS.get(connector, DEFAULT_REGIME_INTERVAL)
    candidates.append({
        "connector": connector, "trading_pair": pair,
        "signal_interval": signal_i, "regime_interval": regime_i,
    })

print(f"\\n{'='*60}")
print(f"Retest sweep: {len(candidates)} pair(s)")
print(f"{'='*60}")
for c in candidates:
    print(f"  {c['connector']:8s} {c['trading_pair']:15s} {c['signal_interval']}+{c['regime_interval']}")
'''


MR_RETEST_CELL6 = '''\
from pmm_lab.data.mongo import MongoCandleLoader
from pmm_lab.config.params import DataQuery
from pmm_lab.data.hashing import hash_candles
from datetime import datetime, timezone

loader = MongoCandleLoader()

candidates = []
for pair, connector in RETEST_PAIRS:
    interval = INTERVALS_BY_CONNECTOR.get(connector, DEFAULT_INTERVAL)
    candidates.append({
        "connector": connector, "trading_pair": pair, "interval": interval,
    })

print(f"\\n{'='*60}")
print(f"Retest sweep: {len(candidates)} pair(s)")
print(f"{'='*60}")
for c in candidates:
    print(f"  {c['connector']:8s} {c['trading_pair']:15s} {c['interval']}")
'''


# -------------------- Cell 8 (sweep loop) construction --------------------

def _sweep_loop_mr() -> str:
    return '''\
# ── Config guard: ensure configuration cell was executed ──
_required_config = [
    "VALIDATION_CONTROLLER_COMPAT", "SEARCH_CONTROLLER_COMPAT", "PHASE2_CONTROLLER_COMPAT",
    "OBJECTIVE_VERSION", "N_TRIALS", "TOP_N", "MIN_ROBUST_SCORE", "N_JOBS",
]
_missing = [v for v in _required_config if v not in globals()]
if _missing:
    raise RuntimeError(f"Config cell not executed; missing: {_missing}")

from pmm_lab.data.candles import validate_candles
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import canonicalize_mr_bb_rsi_params
from pmm_lab.optuna.search_space_mean_reversion_bb_rsi import suggest_mr_bb_rsi_params
from pmm_lab.export.hb_yaml_mr_bb_rsi import (
    MRBBRSIExportParams, export_mr_bb_rsi_yaml, validate_export_mr_bb_rsi,
)
from pmm_lab.objective.stress import load_stress_scenarios
from pmm_lab.objective.objective import REJECT_SCORE
from pmm_lab.objective.holdout import split_holdout
import time

stress_scenarios = load_stress_scenarios()
rules_db = load_exchange_rules()
sweep_results = []
sweep_start = time.time()

for pair_idx, pair_info in enumerate(candidates):
    connector = pair_info["connector"]
    pair = pair_info["trading_pair"]
    interval = pair_info["interval"]
    bar_interval_seconds = INTERVAL_SECONDS[interval]

    print(f"\\n{'='*60}")
    print(f"  [{pair_idx+1}/{len(candidates)}] {connector} / {pair} / {interval}")
    print(f"{'='*60}")

    pair_start = time.time()

    # ── Load and audit candles ──
    try:
        _start_ts = int(pair_info.get("first_ts")) if MAX_TRAINING_DAYS is not None else None
        query = DataQuery(connector=connector, trading_pair=pair, interval=interval, start_ts=_start_ts)
        candles = loader.load_range(query)
    except Exception as e:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "load_error", "error": str(e)})
        continue

    audit = validate_candles(candles, interval=interval, strict=True)
    if not audit.passed_strict:
        print(f"  SKIP: audit failed — {audit.failure_reasons}")
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "audit_fail",
                              "reasons": audit.failure_reasons})
        continue

    dataset_hash = hash_candles(candles)
    reference_price = float(candles["close"][-1])
    pair_rules = resolve_pair_rules(rules_db, connector, pair)
    taker_prob = TAKER_PROBABILITY_BY_CONNECTOR.get(connector, DEFAULT_TAKER_PROBABILITY)

    # ── Build and run objective ──
    try:
        objective = create_objective(
            candles=candles, pair_rules=pair_rules,
            bar_interval_seconds=bar_interval_seconds,
            dataset_hash=dataset_hash, reference_price=reference_price,
            strategy_name="mean_reversion_bb_rsi",
            objective_version=OBJECTIVE_VERSION,
            run_stress=False,  # phase-1 search runs without stress
            controller_compat=SEARCH_CONTROLLER_COMPAT,
            refresh_close_mode=REFRESH_CLOSE_MODE,
            initial_base_balance=INITIAL_BASE_BALANCE,
            taker_probability=taker_prob,
        )
    except Exception as e:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "objective_error", "error": str(e)})
        continue

    import optuna
    study_name = f"mr_bb_rsi_{connector}_{pair.replace('-', '_').lower()}"
    study = optuna.create_study(direction="maximize", study_name=study_name, load_if_exists=False)
    study.optimize(objective, n_trials=N_TRIALS, n_jobs=1, catch=(Exception,))

    completed = [t for t in study.trials
                 if t.state == optuna.trial.TrialState.COMPLETE
                 and t.user_attrs.get("reject_reason") is None]
    if not completed:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "no_valid_trials"})
        continue

    completed.sort(key=lambda t: t.user_attrs.get("objective_score", REJECT_SCORE), reverse=True)
    best = completed[0]
    best_score = float(best.user_attrs.get("objective_score", REJECT_SCORE))

    if best_score < MIN_PHASE1_BEST_FOR_STRESS:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "below_phase1_gate",
                              "best_score": best_score})
        continue

    # ── Canonicalize best and export ──
    raw = dict(best.params)
    raw.setdefault("min_trend_slope", 0.0)          # D17
    raw.setdefault("max_spread_pct", 0.006)          # D2
    raw.setdefault("max_trades_per_day", 6)          # D3
    raw.setdefault("max_executors_per_side", 1)
    raw.setdefault("total_amount_quote", 300.0)

    bundle, reason = canonicalize_mr_bb_rsi_params(
        raw, pair_rules, reference_price, bar_interval_seconds=bar_interval_seconds,
    )
    if bundle is None:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "canonicalize_reject",
                              "reason": reason})
        continue

    out_dir = Path("artifacts/direction-custom/mr_bb_rsi") / connector
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{connector}_{pair.replace('-', '_').lower()}_mean_reversion_bb_rsi_v1.yml"
    export_params = MRBBRSIExportParams(
        connector_name=connector, trading_pair=pair, interval=interval,
    )
    export_mr_bb_rsi_yaml(bundle.strategy_config, bundle.engine_config, export_params, out_path)
    validate_export_mr_bb_rsi(out_path)

    sweep_results.append({
        "connector": connector, "trading_pair": pair, "interval": interval,
        "status": "complete",
        "best_score": best_score,
        "yaml_path": str(out_path),
        "n_trials_completed": len(completed),
        "binding_frac": best.user_attrs.get("max_trades_per_day_binding_fraction"),
        "elapsed_s": time.time() - pair_start,
    })

print(f"\\nTotal sweep time: {time.time() - sweep_start:.1f}s")
'''


def _sweep_loop_ema() -> str:
    return '''\
# ── Config guard ──
_required_config = [
    "VALIDATION_CONTROLLER_COMPAT", "SEARCH_CONTROLLER_COMPAT", "PHASE2_CONTROLLER_COMPAT",
    "OBJECTIVE_VERSION", "N_TRIALS", "TOP_N", "MIN_ROBUST_SCORE", "N_JOBS",
]
_missing = [v for v in _required_config if v not in globals()]
if _missing:
    raise RuntimeError(f"Config cell not executed; missing: {_missing}")

from pmm_lab.data.candles import validate_candles
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.canonicalizer_ema_regime_hold import canonicalize_ema_regime_hold_params
from pmm_lab.optuna.search_space_ema_regime_hold import suggest_ema_regime_hold_params
from pmm_lab.export.hb_yaml_ema_regime_hold import (
    EMARegimeHoldExportParams, export_ema_regime_hold_yaml, validate_export_ema_regime_hold,
)
from pmm_lab.objective.stress import load_stress_scenarios
from pmm_lab.objective.objective import REJECT_SCORE
import time

stress_scenarios = load_stress_scenarios()
rules_db = load_exchange_rules()
sweep_results = []
sweep_start = time.time()

for pair_idx, pair_info in enumerate(candidates):
    connector = pair_info["connector"]
    pair = pair_info["trading_pair"]
    signal_interval = pair_info["signal_interval"]
    regime_interval = pair_info["regime_interval"]
    bar_interval_seconds = INTERVAL_SECONDS[signal_interval]

    print(f"\\n{'='*60}")
    print(f"  [{pair_idx+1}/{len(candidates)}] {connector} / {pair} / {signal_interval}+{regime_interval}")
    print(f"{'='*60}")

    pair_start = time.time()

    # ── Load both candle streams ──
    try:
        _signal_start = int(pair_info.get("signal_first_ts")) if MAX_TRAINING_DAYS is not None else None
        _regime_start = int(pair_info.get("regime_first_ts")) if MAX_TRAINING_DAYS is not None else None
        signal_candles = loader.load_range(
            DataQuery(connector=connector, trading_pair=pair, interval=signal_interval, start_ts=_signal_start)
        )
        regime_candles = loader.load_range(
            DataQuery(connector=connector, trading_pair=pair, interval=regime_interval, start_ts=_regime_start)
        )
    except Exception as e:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "load_error", "error": str(e)})
        continue

    # ── Audit both ──
    signal_audit = validate_candles(signal_candles, interval=signal_interval, strict=True)
    if not signal_audit.passed_strict:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "audit_fail_signal",
                              "reasons": signal_audit.failure_reasons})
        continue
    regime_audit = validate_candles(regime_candles, interval=regime_interval, strict=True)
    if not regime_audit.passed_strict:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "audit_fail_regime",
                              "reasons": regime_audit.failure_reasons})
        continue

    dataset_hash = hash_candles(signal_candles)
    reference_price = float(signal_candles["close"][-1])
    pair_rules = resolve_pair_rules(rules_db, connector, pair)
    taker_prob = TAKER_PROBABILITY_BY_CONNECTOR.get(connector, DEFAULT_TAKER_PROBABILITY)

    try:
        objective = create_objective(
            candles=signal_candles, pair_rules=pair_rules,
            bar_interval_seconds=bar_interval_seconds,
            dataset_hash=dataset_hash, reference_price=reference_price,
            strategy_name="ema_regime_hold",
            objective_version=OBJECTIVE_VERSION,
            run_stress=False,
            controller_compat=SEARCH_CONTROLLER_COMPAT,
            refresh_close_mode=REFRESH_CLOSE_MODE,
            initial_base_balance=INITIAL_BASE_BALANCE,
            taker_probability=taker_prob,
            regime_candles=regime_candles,
        )
    except Exception as e:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "objective_error", "error": str(e)})
        continue

    import optuna
    study_name = f"ema_regime_hold_{connector}_{pair.replace('-', '_').lower()}"
    study = optuna.create_study(direction="maximize", study_name=study_name, load_if_exists=False)
    study.optimize(objective, n_trials=N_TRIALS, n_jobs=1, catch=(Exception,))

    completed = [t for t in study.trials
                 if t.state == optuna.trial.TrialState.COMPLETE
                 and t.user_attrs.get("reject_reason") is None]
    if not completed:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "no_valid_trials"})
        continue

    completed.sort(key=lambda t: t.user_attrs.get("objective_score", REJECT_SCORE), reverse=True)
    best = completed[0]
    best_score = float(best.user_attrs.get("objective_score", REJECT_SCORE))

    if best_score < MIN_PHASE1_BEST_FOR_STRESS:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "below_phase1_gate",
                              "best_score": best_score})
        continue

    raw = dict(best.params)
    raw.setdefault("hold_mode", "reentry")          # D4
    raw.setdefault("max_executors_per_side", 1)
    raw.setdefault("total_amount_quote", 300.0)

    bundle, reason = canonicalize_ema_regime_hold_params(
        raw, pair_rules, reference_price,
        signal_interval_seconds=bar_interval_seconds,
        regime_candles=regime_candles,
    )
    if bundle is None:
        sweep_results.append({"connector": connector, "trading_pair": pair, "status": "canonicalize_reject",
                              "reason": reason})
        continue

    out_dir = Path("artifacts/direction-custom/ema_regime_hold") / connector
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{connector}_{pair.replace('-', '_').lower()}_ema_regime_hold_v1.yml"
    export_params = EMARegimeHoldExportParams(
        connector_name=connector, trading_pair=pair,
        signal_interval=signal_interval, regime_interval=regime_interval,
    )
    export_ema_regime_hold_yaml(bundle.strategy_config, bundle.engine_config, export_params, out_path)
    validate_export_ema_regime_hold(out_path)

    sweep_results.append({
        "connector": connector, "trading_pair": pair,
        "signal_interval": signal_interval, "regime_interval": regime_interval,
        "status": "complete",
        "best_score": best_score,
        "yaml_path": str(out_path),
        "n_trials_completed": len(completed),
        "elapsed_s": time.time() - pair_start,
    })

print(f"\\nTotal sweep time: {time.time() - sweep_start:.1f}s")
'''


# -------------------- Common cells (10, 12 — results summaries) --------------------

CELL10 = '''\
# Results summary — exclusion stats and per-pair outcome table.
from pathlib import Path

def _status_counts(rows):
    counts = {}
    for r in rows:
        counts[r.get("status", "?")] = counts.get(r.get("status", "?"), 0) + 1
    return counts

print("=" * 60)
print("SWEEP RESULTS SUMMARY")
print("=" * 60)
print("Status counts:", _status_counts(sweep_results))

print("\\nPer-pair outcomes:")
for r in sweep_results:
    status = r.get("status", "?")
    conn = r.get("connector", "?")
    pair = r.get("trading_pair", "?")
    extras = ""
    if status == "complete":
        extras = f" score={r.get('best_score', 0):.3f}  yaml={r.get('yaml_path')}"
    elif "reason" in r:
        extras = f" reason={r['reason']}"
    elif "error" in r:
        extras = f" error={r['error'][:80]}"
    print(f"  [{status:20s}] {conn:8s} {pair:15s}{extras}")
'''


CELL12_MR = '''\
profitable = [r for r in sweep_results if r["status"] == "complete" and r.get("best_score", 0) > 0]
print(f"\\n{'='*60}")
print(f"Profitable pairs: {len(profitable)}")
print(f"{'='*60}")

# Informational release gates (D-series). None are blocking.
print("\\nRelease Gates (Informational Only):")
for r in profitable:
    print(f"\\n  {r['connector']} / {r['trading_pair']}:")
    gates = [
        ("robust_score > 0", r.get("best_score", 0), 0.0,
         r.get("best_score", 0) > 0),
        ("max_trades_per_day binding_frac < 0.30",
         r.get("binding_frac"), 0.30,
         (r.get("binding_frac") is None) or r["binding_frac"] < 0.30),
    ]
    for name, actual, threshold, passed in gates:
        mark = "PASS" if passed else "FAIL"
        print(f"    [{mark}] {name}: actual={actual}")
'''


CELL12_EMA = '''\
profitable = [r for r in sweep_results if r["status"] == "complete" and r.get("best_score", 0) > 0]
print(f"\\n{'='*60}")
print(f"Profitable pairs: {len(profitable)}")
print(f"{'='*60}")

print("\\nRelease Gates (Informational Only):")
for r in profitable:
    print(f"\\n  {r['connector']} / {r['trading_pair']}:")
    gates = [
        ("robust_score > 0", r.get("best_score", 0), 0.0,
         r.get("best_score", 0) > 0),
    ]
    for name, actual, threshold, passed in gates:
        mark = "PASS" if passed else "FAIL"
        print(f"    [{mark}] {name}: actual={actual}")
'''


# Retest adds cell 14 (code) + cell 15 (markdown)
CELL14_RETEST = '''\
# ── CROSS-PAIR RANKING ──
completed_results = [r for r in sweep_results if r.get("status") == "complete"]
completed_results.sort(key=lambda r: r.get("best_score", float("-inf")), reverse=True)

print(f"\\n{'='*60}")
print(f"Cross-pair ranking by best_score (best first)")
print(f"{'='*60}")
for rank, r in enumerate(completed_results, 1):
    print(f"  #{rank:>2} {r['connector']:8s} {r['trading_pair']:15s} "
          f"score={r.get('best_score', 0):>8.3f}  "
          f"yaml={r.get('yaml_path')}")
'''


# -------------------- Notebook assembly --------------------

def _md(source: str) -> Dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def _code(source: str) -> Dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": source}


def _cell1_imports(strategy_label: str) -> str:
    return f'''\
import sys, os, subprocess, time, logging
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import optuna
import pmm_lab

optuna.logging.set_verbosity(optuna.logging.WARNING)
logging.getLogger("pmm_lab").setLevel(logging.WARNING)

print(f"pmm_lab {{pmm_lab.__version__}} | NumPy {{np.__version__}} | Optuna {{optuna.__version__}}")
print(f"Strategy: {strategy_label}")

MONGO_URI = os.getenv("MONGO_URI", "")
OPTUNA_STORAGE = os.getenv("OPTUNA_STORAGE", "")
print(f"MONGO_URI      : {{'SET' if MONGO_URI else 'NOT SET'}}")
print(f"OPTUNA_STORAGE : {{'SET' if OPTUNA_STORAGE else 'NOT SET (using SQLite)'}}")
'''


def _cell4_preflight() -> str:
    return '''\
# ── Preflight: validate storage + worker configuration ──
from pmm_lab.optuna.storage import get_storage_url

_storage_url = OPTUNA_STORAGE if OPTUNA_STORAGE else get_storage_url()
_is_postgres = "postgresql" in str(_storage_url).lower()

print(f"Requested N_JOBS: {N_JOBS}")
print(f"Storage backend : {'PostgreSQL' if _is_postgres else 'SQLite (fallback)'}")
print(f"Dispatch mode   : {'process-parallel' if N_JOBS > 1 and _is_postgres else 'serial'}")
if N_JOBS > 1 and not _is_postgres:
    print("WARNING: N_JOBS>1 with SQLite — forcing serial. Set OPTUNA_STORAGE for parallelism.")
'''


def _cell_next_steps(strategy_label: str) -> str:
    return f'''\
## 6. Next Steps

- Inspect the per-pair markdown reports under `artifacts/direction-custom/{strategy_label.lower().replace('-', '_').replace(' ', '_')}/<connector>/`.
- Review exported YAMLs against the live Hummingbot controller Pydantic model.
- For finalists, run the retest notebook with a narrowed `RETEST_PAIRS` list.
- All release gates are informational only per the user's directive; only
  the strict data-audit gate hard-stops (per pair — a failed audit `continue`s
  to the next pair, not halting the whole notebook).
'''


def _cell_retest_next_steps(strategy_label: str) -> str:
    return f'''\
## 7. Next Steps

- Open each exported YAML in `artifacts/direction-custom/{strategy_label.lower().replace('-', '_').replace(' ', '_')}/<connector>/`
  and confirm the parameters look reasonable for live deployment.
- Run the multi-exchange sweep first to discover candidate pairs, then
  populate `RETEST_PAIRS` here for a focused run.
- The cross-pair ranking in cell 14 lets you compare the same strategy
  across pairs on the same scale.
'''


def build_mr_multi() -> Dict:
    cells = [
        _md(
            "# Mean-Reversion BB+RSI Multi-Exchange Sweep\n"
            "\n"
            "**Automated optimization across multiple exchanges with exchange-separated results**\n"
            "\n"
            "This notebook:\n"
            "1. Discovers all available pairs for multiple connectors + one quote asset from MongoDB\n"
            "2. For each eligible connector / pair:\n"
            "   - Runs Optuna walk-forward optimization via the MR BB+RSI objective wrapper\n"
            "   - Canonicalizes the best candidate\n"
            "   - Exports a Hummingbot-loadable YAML config\n"
            "3. Exports YAML configs and reports under `artifacts/direction-custom/mr_bb_rsi/<connector>/`\n"
            "4. Displays summary tables separated by exchange\n"
            "\n"
            "**Configuration:** Edit the variables in the first code cell, then Run All.\n"
        ),
        _code(_cell1_imports("mean_reversion_bb_rsi")),
        _md("## 1. Configuration\n\nEdit these variables to control the multi-exchange sweep. Then **Run All** cells below.\n"),
        _code(MR_MULTI_CELL3),
        _code(_cell4_preflight()),
        _md("## 2. Discover Available Pairs Across Exchanges"),
        _code(_discovery_mr()),
        _md(
            "## 3. Sweep: Optimize Each Connector / Pair\n"
            "\n"
            "For each eligible connector / pair, the sweep:\n"
            "1. Loads and validates candles\n"
            "2. Runs Optuna walk-forward trials\n"
            "3. Canonicalizes the best trial\n"
            "4. Exports and validates a Hummingbot YAML\n"
        ),
        _code(_sweep_loop_mr()),
        _md("## 4. Results Summary"),
        _code(CELL10),
        _md("## 5. Profitable Pairs Detail by Exchange"),
        _code(CELL12_MR),
        _md(_cell_next_steps("mr_bb_rsi")),
    ]
    assert len(cells) == 14, f"MR multi has {len(cells)} cells"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _discovery_mr() -> str:
    return '''\
from pmm_lab.data.mongo import MongoCandleLoader
from pmm_lab.config.params import DataQuery
from pmm_lab.data.hashing import hash_candles
from datetime import datetime, timezone

loader = MongoCandleLoader()
all_combos = loader.list_combos(connector=None, quote_asset=QUOTE_ASSET)

now_ts = datetime.now(timezone.utc).timestamp()
candidates = []
stale_exclusions = []
insufficient_exclusions = []

for combo in all_combos:
    connector = combo["connector"]
    if connector not in CONNECTORS:
        continue
    interval = INTERVALS_BY_CONNECTOR.get(connector, DEFAULT_INTERVAL)
    if combo["interval"] != interval:
        continue

    effective_first_ts = combo["first_ts"]
    if MAX_TRAINING_DAYS is not None:
        training_cutoff_ts = combo["last_ts"] - (MAX_TRAINING_DAYS * 86400)
        effective_first_ts = max(effective_first_ts, training_cutoff_ts)
    data_days = (combo["last_ts"] - effective_first_ts) / 86400

    if data_days < MIN_DATA_DAYS:
        insufficient_exclusions.append({
            "connector": connector, "trading_pair": combo["trading_pair"],
            "data_days": data_days, "reason": f"< {MIN_DATA_DAYS}d data",
        })
        continue

    last_age_days = (now_ts - combo["last_ts"]) / 86400
    if last_age_days > MAX_STALE_DAYS:
        stale_exclusions.append({
            "connector": connector, "trading_pair": combo["trading_pair"],
            "last_age_days": last_age_days,
            "reason": f"stale ({last_age_days:.1f}d > {MAX_STALE_DAYS}d)",
        })
        continue

    candidates.append({
        "connector": connector, "trading_pair": combo["trading_pair"],
        "interval": interval, "count": combo["count"],
        "first_ts": effective_first_ts, "full_first_ts": combo["first_ts"],
        "last_ts": combo["last_ts"], "data_days": data_days,
    })

candidates = sorted(candidates, key=lambda c: (c["connector"], c["trading_pair"]))

print(f"\\n{'='*60}")
print(f"Found {len(candidates)} connector/pair combos with >= {MIN_DATA_DAYS}d of data")
print(f"{'='*60}")
for connector in CONNECTORS:
    s = [c for c in candidates if c["connector"] == connector]
    interval = INTERVALS_BY_CONNECTOR.get(connector, DEFAULT_INTERVAL)
    print(f"\\n{connector} / {QUOTE_ASSET} / {interval}: {len(s)} pair(s)")
    for c in s:
        print(f"  {c['trading_pair']:15s}  {c['count']:>8,} candles  {c['data_days']:5.1f} days")

if stale_exclusions:
    print(f"\\nExcluded {len(stale_exclusions)} stale pair(s)")
if insufficient_exclusions:
    print(f"\\nExcluded {len(insufficient_exclusions)} pair(s) with insufficient data")

print(f"\\nTotal to optimize: {len(candidates)}")
'''


def build_mr_retest() -> Dict:
    cells = [
        _md(
            "# Mean-Reversion BB+RSI Retest Sweep\n"
            "\n"
            "Runs the MR BB+RSI pipeline on a user-specified `RETEST_PAIRS` list\n"
            "and ranks results across pairs.\n"
        ),
        _code(_cell1_imports("mean_reversion_bb_rsi (retest)")),
        _md("## 1. Configuration\n"),
        _code(MR_RETEST_CELL3),
        _code(_cell4_preflight()),
        _md("## 2. Load Requested Pairs"),
        _code(MR_RETEST_CELL6),
        _md(
            "## 3. Sweep: Optimize Each Connector / Pair\n"
            "\n"
            "Same pipeline as the multi-exchange sweep, run per-pair from the\n"
            "`RETEST_PAIRS` list.\n"
        ),
        _code(_sweep_loop_mr()),
        _md("## 4. Results Summary"),
        _code(CELL10),
        _md("## 5. Profitable Pairs Detail by Exchange"),
        _code(CELL12_MR),
        _md("## 6. Cross-Pair Ranking"),
        _code(CELL14_RETEST),
        _md(_cell_retest_next_steps("mr_bb_rsi")),
    ]
    assert len(cells) == 16, f"MR retest has {len(cells)} cells"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_ema_multi() -> Dict:
    cells = [
        _md(
            "# EMA Regime-Hold Multi-Exchange Sweep\n"
            "\n"
            "**Multi-timeframe** optimization: requires BOTH signal_interval\n"
            "and regime_interval candles per pair. Pairs missing either are skipped.\n"
            "\n"
            "This notebook:\n"
            "1. Discovers all pairs that have both intervals available\n"
            "2. For each pair, loads both streams, audits both, runs Optuna\n"
            "3. Exports YAML under `artifacts/direction-custom/ema_regime_hold/<connector>/`\n"
            "\n"
            "**Configuration:** Edit the variables in the first code cell, then Run All.\n"
        ),
        _code(_cell1_imports("ema_regime_hold")),
        _md("## 1. Configuration\n"),
        _code(EMA_MULTI_CELL3),
        _code(_cell4_preflight()),
        _md("## 2. Discover Available Pairs Across Exchanges"),
        _code(EMA_MULTI_CELL6),
        _md(
            "## 3. Sweep: Optimize Each Connector / Pair\n"
            "\n"
            "For each pair, loads both signal and regime candles, audits both,\n"
            "and runs the EMA regime-hold objective.\n"
        ),
        _code(_sweep_loop_ema()),
        _md("## 4. Results Summary"),
        _code(CELL10),
        _md("## 5. Profitable Pairs Detail by Exchange"),
        _code(CELL12_EMA),
        _md(_cell_next_steps("ema_regime_hold")),
    ]
    assert len(cells) == 14, f"EMA multi has {len(cells)} cells"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_ema_retest() -> Dict:
    cells = [
        _md(
            "# EMA Regime-Hold Retest Sweep\n"
            "\n"
            "Runs the EMA regime-hold pipeline on a user-specified `RETEST_PAIRS` list.\n"
        ),
        _code(_cell1_imports("ema_regime_hold (retest)")),
        _md("## 1. Configuration\n"),
        _code(EMA_RETEST_CELL3),
        _code(_cell4_preflight()),
        _md("## 2. Load Requested Pairs"),
        _code(EMA_RETEST_CELL6),
        _md(
            "## 3. Sweep: Optimize Each Connector / Pair\n"
            "\n"
            "Loads both signal_interval and regime_interval candles per pair.\n"
        ),
        _code(_sweep_loop_ema()),
        _md("## 4. Results Summary"),
        _code(CELL10),
        _md("## 5. Profitable Pairs Detail by Exchange"),
        _code(CELL12_EMA),
        _md("## 6. Cross-Pair Ranking"),
        _code(CELL14_RETEST),
        _md(_cell_retest_next_steps("ema_regime_hold")),
    ]
    assert len(cells) == 16, f"EMA retest has {len(cells)} cells"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main():
    outputs = {
        "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb": build_mr_multi(),
        "mean_reversion_bb_rsi_retest_sweep.ipynb": build_mr_retest(),
        "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb": build_ema_multi(),
        "ema_regime_hold_retest_sweep.ipynb": build_ema_retest(),
    }
    for fname, nb in outputs.items():
        path = OUT_DIR / fname
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, indent=1)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
