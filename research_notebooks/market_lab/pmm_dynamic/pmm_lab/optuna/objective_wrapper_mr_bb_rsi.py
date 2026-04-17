"""Objective wrapper for MR BB+RSI.

Isolates new code so regressions don't touch MACD-BB (which is alpha).
Mirrors the MACD-BB wrapper's structure:
  suggest -> canonicalize -> walk-forward -> stress -> aggregate -> log.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

import numpy as np
import optuna

from pmm_lab.config.params import PairRules
from pmm_lab.objective.objective import REJECT_SCORE
from pmm_lab.objective.robustness import robust_aggregate


def _create_mr_bb_rsi_objective(
    candles,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    dataset_hash: str,
    reference_price: float,
    train_days: float,
    test_days: float,
    step_days: float,
    embargo_bars,
    obj_fn,
    _obj_weights,
    objective_version: int,
    run_stress: bool,
    lambda_mad: float,
    fixed_quote: Optional[float],
    controller_compat: bool,
    strategy_search_space,
    strategy_canonicalizer,
    refresh_close_mode: str = "keep",
    initial_base_balance: float = 0.0,
    taker_probability: float = 0.0,
):
    """Create an Optuna objective for the MR BB+RSI strategy."""
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.objective.walkforward import TimeSeriesCV
    from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import canonicalize_mr_bb_rsi_params
    from pmm_lab.optuna.search_space_mean_reversion_bb_rsi import suggest_mr_bb_rsi_params
    from pmm_lab.sim.engine import SimEngine
    from pmm_lab.sim.executor_model import SimResult
    from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategy

    _suggest = strategy_search_space or suggest_mr_bb_rsi_params
    _canonicalize = strategy_canonicalizer or canonicalize_mr_bb_rsi_params

    def objective(trial: optuna.Trial) -> float:
        # 1. Suggest
        try:
            raw_params = _suggest(trial, fixed_quote=fixed_quote, bar_interval_seconds=bar_interval_seconds)
        except TypeError:
            raw_params = _suggest(trial, fixed_quote=fixed_quote)

        # 2. Canonicalize
        bundle, reject_reason = _canonicalize(
            raw_params, pair_rules, reference_price,
            bar_interval_seconds=bar_interval_seconds,
        )
        if bundle is None:
            trial.set_user_attr("reject_reason", reject_reason)
            trial.set_user_attr("objective_score", REJECT_SCORE)
            trial.set_user_attr("dataset_hash", dataset_hash)
            return REJECT_SCORE

        strategy_config = replace(bundle.strategy_config, controller_compat=controller_compat)
        engine_config = replace(
            bundle.engine_config,
            refresh_close_mode=refresh_close_mode,
            initial_base_balance=initial_base_balance,
            taker_probability=taker_probability,
        )

        trial.set_user_attr("reject_reason", None)
        trial.set_user_attr("strategy_name", "mean_reversion_bb_rsi")
        trial.set_user_attr("dataset_hash", dataset_hash)

        # 3. Walk-forward
        n_bars = len(candles)
        warmup_bars = max(
            strategy_config.bb_length, strategy_config.trend_ema_length,
            strategy_config.rsi_length, strategy_config.atr_length,
        )
        cv = TimeSeriesCV(
            n_bars=n_bars, bar_interval_seconds=bar_interval_seconds,
            train_days=train_days, test_days=test_days, step_days=step_days,
            embargo_bars=embargo_bars if embargo_bars is not None else warmup_bars + 10,
            macd_slow=strategy_config.trend_ema_length,  # warmup hint slot
            natr_length=strategy_config.bb_length,
        )
        try:
            fold_defs = cv.get_folds()
        except ValueError:
            trial.set_user_attr("reject_reason", "insufficient data for walk-forward folds")
            trial.set_user_attr("objective_score", REJECT_SCORE)
            return REJECT_SCORE

        # Compute signals once
        signal_strategy = MeanReversionBBRSIStrategy(strategy_config)
        full_signals = signal_strategy.compute_signals(candles)

        initial_equity = engine_config.total_amount_quote
        fold_scores = []
        fold_pnls = []
        fold_sharpes = []
        fold_dds = []
        fold_trades = []
        fold_fees = []
        total_place_attempts = 0
        total_cap_rejects = 0

        for fold_def in fold_defs:
            test_start = fold_def.test_start_idx
            test_end = fold_def.test_end_idx
            test_candles = candles[test_start:test_end]
            test_signals = full_signals.slice(test_start, test_end)

            # Fresh strategy per fold — rolling cap state must not leak
            fold_strategy = MeanReversionBBRSIStrategy(strategy_config)

            engine = SimEngine(engine_config, pair_rules)
            sim_result = engine.run_with_signals(
                test_candles, fold_strategy, test_signals,
                sim_start_idx=0, bar_index_offset=test_start,
            )
            # Track fold-level cap rejection fraction. The strategy's
            # _entry_timestamps contains accepted entries; rejections are
            # reflected in SimResult.n_orders_rejected at the engine level.
            total_place_attempts += sim_result.n_orders_placed + sim_result.n_orders_rejected
            # We don't have a per-fold breakdown of cap vs other rejects without
            # instrumenting the strategy; approximate cap_rejects as total rejects.
            total_cap_rejects += sim_result.n_orders_rejected

            test_sim_result = SimResult(
                trades=sim_result.trades,
                equity_curve=sim_result.equity_curve,
                position_history=sim_result.position_history,
                n_orders_placed=sim_result.n_orders_placed,
                n_orders_filled=sim_result.n_orders_filled,
                n_orders_rejected=sim_result.n_orders_rejected,
                n_market_exits=sim_result.n_market_exits,
                final_base_balance=sim_result.final_base_balance,
                final_quote_balance=sim_result.final_quote_balance,
            )
            test_metrics = compute_metrics(
                test_sim_result, initial_equity, test_candles, bar_interval_seconds
            )
            test_obj = obj_fn(test_metrics)

            fold_scores.append(test_obj.raw_score)
            fold_pnls.append(test_metrics.pnl_pct)
            fold_sharpes.append(test_metrics.sharpe)
            fold_dds.append(test_metrics.max_drawdown_pct)
            fold_trades.append(test_metrics.trade_count)
            fold_fees.append(test_metrics.total_fees_quote)

            running_median = float(np.median(fold_scores))
            trial.report(running_median, step=fold_def.fold_index)
            if trial.should_prune():
                raise optuna.TrialPruned()

        # 4. Stress
        stress_worst_score = None
        stress_worst_scenario = None
        fold_stress_scores_list = None
        if run_stress:
            from pmm_lab.objective.stress import load_stress_scenarios
            from pmm_lab.objective.stress_mean_reversion_bb_rsi import run_mr_bb_rsi_fold_local_stress

            scenarios = load_stress_scenarios()
            fold_stress_scores_list = []
            for fold_def in fold_defs:
                fs = run_mr_bb_rsi_fold_local_stress(
                    candles, strategy_config, engine_config, pair_rules,
                    bar_interval_seconds,
                    fold_test_start_idx=fold_def.test_start_idx,
                    fold_test_end_idx=fold_def.test_end_idx,
                    scenarios=scenarios,
                    objective_version=objective_version,
                    objective_weights=_obj_weights,
                    precomputed_signals=full_signals,
                )
                fold_stress_scores_list.append(fs)
            all_stress = [s for fs in fold_stress_scores_list for s in fs]
            if all_stress:
                stress_worst_score = float(min(all_stress))
                stress_worst_scenario = f"fold_stress_{int(np.argmin(all_stress))}"

        # 5. Aggregate
        if fold_stress_scores_list is not None:
            from pmm_lab.objective.robustness import robust_aggregate_v2
            final_score = robust_aggregate_v2(
                fold_scores, fold_stress_scores=fold_stress_scores_list, lambda_mad=lambda_mad,
            )
        else:
            final_score = robust_aggregate(fold_scores, lambda_mad=lambda_mad)

        # 6. user_attrs
        trial.set_user_attr("objective_score", final_score)
        trial.set_user_attr("fold_scores", [float(s) for s in fold_scores])
        trial.set_user_attr("pnl_pct_median", float(np.median(fold_pnls)))
        trial.set_user_attr("sharpe_median", float(np.median(fold_sharpes)))
        trial.set_user_attr("max_dd_median", float(np.median(fold_dds)))
        trial.set_user_attr("trade_count_median", float(np.median(fold_trades)))
        trial.set_user_attr("total_fees_median", float(np.median(fold_fees)))
        trial.set_user_attr("n_folds", len(fold_scores))
        if stress_worst_score is not None:
            trial.set_user_attr("stress_worst_score", float(stress_worst_score))
        if stress_worst_scenario is not None:
            trial.set_user_attr("stress_worst_scenario", stress_worst_scenario)
        if total_place_attempts > 0:
            trial.set_user_attr(
                "max_trades_per_day_binding_fraction",
                float(total_cap_rejects) / float(total_place_attempts),
            )
        else:
            trial.set_user_attr("max_trades_per_day_binding_fraction", 0.0)

        return float(final_score)

    return objective
