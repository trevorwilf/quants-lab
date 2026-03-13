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
from pmm_lab.objective.stress import run_stress_tests, StressReport
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
    objective_weights: ObjectiveWeights = ObjectiveWeights(),
    run_stress: bool = True,
    lambda_mad: float = 0.5,
):
    """Create an Optuna-compatible objective function (closure).

    Returns a callable: objective(trial) -> float
    """

    def objective(trial: optuna.Trial) -> float:
        # 1. Suggest params
        raw_params = suggest_params(trial)

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
        from pmm_lab.objective.objective import objective_v1
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
            test_obj = objective_v1(test_metrics, objective_weights)

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

        # 4. Optionally run stress tests on full dataset
        stress_worst_scenario = None
        stress_worst_score = None
        all_scores = list(fold_scores)

        if run_stress:
            # Run stress tests on FOLD TEST WINDOWS ONLY (not full dataset)
            # to avoid leaking full-dataset information into the optimization target.
            stress_scores_all_folds = []
            for fold_def in fold_defs:
                fold_candles = candles[:fold_def.test_end_idx]
                fold_stress = run_stress_tests(
                    fold_candles, config, pair_rules, bar_interval_seconds,
                    objective_weights=objective_weights,
                )
                worst_fold_stress = fold_stress.worst_score
                stress_scores_all_folds.append(worst_fold_stress)

            all_scores.extend(stress_scores_all_folds)
            stress_worst_scenario = "fold_stress_aggregate"
            stress_worst_score = float(np.min(stress_scores_all_folds)) if stress_scores_all_folds else None

        # 5. Compute robust aggregate
        final_score = robust_aggregate(all_scores, lambda_mad=lambda_mad)

        # 6. Log user attrs
        trial.set_user_attr("objective_score", final_score)
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
