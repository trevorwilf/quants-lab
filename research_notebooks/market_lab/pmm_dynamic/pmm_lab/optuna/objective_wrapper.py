"""
Optuna objective wrapper.

Connects suggest_params -> canonicalize -> walk-forward -> stress -> robust_aggregate
into a single callable that Optuna's study.optimize() can use.
"""

import numpy as np
import optuna
from typing import Optional

from pmm_lab.config.params import PairRules
from pmm_lab.data.hashing import hash_candles
from pmm_lab.optuna.search_space import suggest_params
from pmm_lab.optuna.canonicalizer import canonicalize_params
from pmm_lab.objective.walkforward import run_walk_forward, WalkForwardResult
from pmm_lab.objective.stress import run_stress_tests
from pmm_lab.objective.robustness import robust_aggregate
from pmm_lab.objective.objective import REJECT_SCORE, ObjectiveWeights


def create_objective(
    candles: np.ndarray,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    dataset_hash: str,
    reference_price: float,
    train_days: float = 42.0,
    test_days: float = 14.0,
    step_days: float = 14.0,
    embargo_bars: Optional[int] = None,
    objective_weights=None,           # ObjectiveWeights or ObjectiveWeightsV2
    objective_version: int = 1,        # 1 = v1, 2 = v2
    run_stress: bool = True,
    lambda_mad: float = 0.5,
    fixed_quote: Optional[float] = None,  # if set, passed to suggest_params
):
    """Create an Optuna-compatible objective function (closure).

    Returns a callable: objective(trial) -> float
    """
    # Select objective function
    if objective_version == 2:
        from pmm_lab.objective.objective import objective_v2, ObjectiveWeightsV2
        _obj_weights = objective_weights if objective_weights is not None else ObjectiveWeightsV2()
        obj_fn = lambda m: objective_v2(m, _obj_weights)
    else:
        from pmm_lab.objective.objective import objective_v1, ObjectiveWeights as OW
        _obj_weights = objective_weights if objective_weights is not None else OW()
        obj_fn = lambda m: objective_v1(m, _obj_weights)

    # Stress tests always use v1 objective (stress.py hardcodes objective_v1)
    _stress_weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()

    def objective(trial: optuna.Trial) -> float:
        # 1. Suggest params
        raw_params = suggest_params(trial, fixed_quote=fixed_quote)

        # 2. Canonicalize
        config, reject_reason = canonicalize_params(raw_params, pair_rules, reference_price)

        if config is None:
            trial.set_user_attr("reject_reason", reject_reason)
            trial.set_user_attr("objective_score", REJECT_SCORE)
            trial.set_user_attr("dataset_hash", dataset_hash)
            return REJECT_SCORE

        trial.set_user_attr("reject_reason", None)
        trial.set_user_attr("buy_n_levels", len(config.buy_spreads))
        trial.set_user_attr("sell_n_levels", len(config.sell_spreads))
        trial.set_user_attr("dataset_hash", dataset_hash)

        # 3. Walk-forward with per-fold pruning
        from pmm_lab.objective.walkforward import TimeSeriesCV
        n_bars = len(candles)

        cv = TimeSeriesCV(
            n_bars=n_bars,
            bar_interval_seconds=bar_interval_seconds,
            train_days=train_days,
            test_days=test_days,
            step_days=step_days,
            embargo_bars=embargo_bars,
            macd_slow=config.macd_slow,
            natr_length=config.natr_length,
        )

        try:
            fold_defs = cv.get_folds()
        except ValueError:
            trial.set_user_attr("reject_reason", "insufficient data for walk-forward folds")
            trial.set_user_attr("objective_score", REJECT_SCORE)
            return REJECT_SCORE

        from pmm_lab.sim.runner import CandleSimRunner
        from pmm_lab.metrics.metrics import compute_metrics
        from pmm_lab.sim.executor_model import SimResult

        initial_equity = config.total_amount_quote
        fold_scores = []
        fold_pnls = []
        fold_sharpes = []
        fold_dds = []
        fold_trades = []
        fold_fees = []

        for fold_def in fold_defs:
            # Slice candles for feature warmup through test end
            candle_slice = candles[:fold_def.test_end_idx]

            runner = CandleSimRunner(config, pair_rules)
            sim_result = runner.run(candle_slice, sim_start_idx=fold_def.test_start_idx)

            # Extract test window
            test_eq = sim_result.equity_curve[fold_def.test_start_idx:fold_def.test_end_idx]
            test_pos = sim_result.position_history[fold_def.test_start_idx:fold_def.test_end_idx]
            test_candles = candles[fold_def.test_start_idx:fold_def.test_end_idx]
            test_trades = [t for t in sim_result.trades if t.entry_bar >= fold_def.test_start_idx]

            test_sim_result = SimResult(
                trades=test_trades,
                equity_curve=test_eq,
                position_history=test_pos,
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

            # Per-fold pruning
            running_median = float(np.median(fold_scores))
            trial.report(running_median, step=fold_def.fold_index)
            if trial.should_prune():
                raise optuna.TrialPruned()

        # 4. Fold-local stress (v2) or full-dataset stress (v1 compat)
        stress_worst_scenario = None
        stress_worst_score = None
        all_scores = list(fold_scores)
        fold_stress_scores_list = None

        if run_stress:
            from pmm_lab.objective.stress import run_fold_local_stress, load_stress_scenarios
            scenarios = load_stress_scenarios()
            fold_stress_scores_list = []

            for fold_def in fold_defs:
                fold_stress = run_fold_local_stress(
                    candles, config, pair_rules, bar_interval_seconds,
                    fold_test_start_idx=fold_def.test_start_idx,
                    fold_test_end_idx=fold_def.test_end_idx,
                    scenarios=scenarios,
                    objective_weights=_stress_weights if isinstance(_obj_weights, ObjectiveWeights) else ObjectiveWeights(),
                )
                fold_stress_scores_list.append(fold_stress)

            # Flatten for worst-scenario tracking
            all_stress = [s for fold_s in fold_stress_scores_list for s in fold_s]
            if all_stress:
                worst_idx = int(np.argmin(all_stress))
                stress_worst_score = float(min(all_stress))
                stress_worst_scenario = f"fold_stress_{worst_idx}"

        # 5. Compute robust aggregate
        if fold_stress_scores_list is not None:
            from pmm_lab.objective.robustness import robust_aggregate_v2
            final_score = robust_aggregate_v2(
                fold_scores,
                fold_stress_scores=fold_stress_scores_list,
                lambda_mad=lambda_mad,
            )
        else:
            final_score = robust_aggregate(all_scores, lambda_mad=lambda_mad)

        # 6. Log user attrs
        trial.set_user_attr("objective_score", final_score)
        # Log fold-level scores for replay verification
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

        return final_score

    return objective
