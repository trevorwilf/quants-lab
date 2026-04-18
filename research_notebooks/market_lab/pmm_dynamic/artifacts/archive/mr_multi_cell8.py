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

    print(f"\n{'='*60}")
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

print(f"\nTotal sweep time: {time.time() - sweep_start:.1f}s")
