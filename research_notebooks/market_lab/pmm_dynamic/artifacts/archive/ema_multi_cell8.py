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

    print(f"\n{'='*60}")
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

print(f"\nTotal sweep time: {time.time() - sweep_start:.1f}s")
