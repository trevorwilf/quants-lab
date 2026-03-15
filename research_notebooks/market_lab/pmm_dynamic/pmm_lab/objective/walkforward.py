"""
Walk-forward time-series cross-validation.

Splits a candle dataset into chronological train/test folds with mandatory
embargo between them to prevent indicator warmup leakage.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

from pmm_lab.config.defaults import INTERVAL_SECONDS
from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.metrics.metrics import Metrics, compute_metrics
from pmm_lab.objective.objective import ObjectiveDecomposition, objective_v1, objective_v2, ObjectiveWeights, ObjectiveWeightsV2
from pmm_lab.objective.robustness import robust_aggregate
from pmm_lab.data.hashing import hash_candles


@dataclass(frozen=True)
class FoldDefinition:
    """Definition of one train/test fold."""
    fold_index: int
    train_start_idx: int       # inclusive bar index
    train_end_idx: int         # exclusive bar index
    embargo_end_idx: int       # exclusive — test starts here
    test_start_idx: int        # inclusive bar index (== embargo_end_idx)
    test_end_idx: int          # exclusive bar index


@dataclass
class FoldResult:
    """Result of evaluating one fold."""
    fold_index: int
    train_metrics: Metrics
    test_metrics: Metrics
    test_objective: ObjectiveDecomposition
    train_trade_count: int
    test_trade_count: int


@dataclass
class WalkForwardResult:
    """Result of a full walk-forward evaluation."""
    folds: List[FoldResult]
    fold_definitions: List[FoldDefinition]
    aggregate_score: float              # robust aggregate of test objectives
    per_fold_scores: List[float]        # test objective score per fold
    config_used: SimConfig
    dataset_hash: str


class TimeSeriesCV:
    """Generate walk-forward fold definitions for a candle array."""

    def __init__(
        self,
        n_bars: int,
        bar_interval_seconds: int,
        train_days: float = 42.0,
        test_days: float = 14.0,
        step_days: float = 14.0,
        embargo_bars: Optional[int] = None,
        macd_slow: int = 42,
        natr_length: int = 14,
    ):
        self.n_bars = n_bars
        self.bar_interval_seconds = bar_interval_seconds
        self.train_days = train_days
        self.test_days = test_days
        self.step_days = step_days
        self.macd_slow = macd_slow
        self.natr_length = natr_length

        if embargo_bars is None:
            self.embargo_bars = max(macd_slow, natr_length) + 10
        else:
            self.embargo_bars = embargo_bars

        # Convert days to bars
        bars_per_day = 86400.0 / bar_interval_seconds
        self.train_bars = int(train_days * bars_per_day)
        self.test_bars = int(test_days * bars_per_day)
        self.step_bars = int(step_days * bars_per_day)

    def get_folds(self) -> List[FoldDefinition]:
        """Generate all fold definitions.

        Rules:
        1. Each fold's train window starts at train_start_idx and ends at train_end_idx.
        2. Embargo gap of embargo_bars separates train_end from test_start.
        3. test_start_idx = train_end_idx + embargo_bars.
        4. test_end_idx = test_start_idx + test_bars.
        5. Folds step forward by step_bars each iteration.
        6. A fold is only included if test_end_idx <= n_bars.
        7. At least 2 folds must be generated, otherwise raise ValueError.
        """
        folds = []
        fold_idx = 0
        train_start = 0

        while True:
            train_end = train_start + self.train_bars
            embargo_end = train_end + self.embargo_bars
            test_start = embargo_end
            test_end = test_start + self.test_bars

            if test_end > self.n_bars:
                break

            folds.append(FoldDefinition(
                fold_index=fold_idx,
                train_start_idx=train_start,
                train_end_idx=train_end,
                embargo_end_idx=embargo_end,
                test_start_idx=test_start,
                test_end_idx=test_end,
            ))

            fold_idx += 1
            train_start += self.step_bars

        if len(folds) < 2:
            raise ValueError(
                f"Cannot generate at least 2 folds with n_bars={self.n_bars}, "
                f"train_bars={self.train_bars}, test_bars={self.test_bars}, "
                f"embargo_bars={self.embargo_bars}, step_bars={self.step_bars}"
            )

        return folds


def run_walk_forward(
    candles: np.ndarray,
    config: SimConfig,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    dataset_hash: str,
    train_days: float = 42.0,
    test_days: float = 14.0,
    step_days: float = 14.0,
    embargo_bars: Optional[int] = None,
    objective_weights=None,
    objective_version: int = 1,
) -> WalkForwardResult:
    """Run a full walk-forward evaluation.

    For each fold:
    1. Slice candles from 0 to test_end_idx (for feature warmup).
    2. Run CandleSimRunner with sim_start_idx=test_start_idx on that slice.
    3. Compute metrics and objective on the test portion only.
    4. Record FoldResult.

    After all folds, compute aggregate score using robust_aggregate().
    """
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

    fold_defs = cv.get_folds()
    initial_equity = config.total_amount_quote

    fold_results = []
    per_fold_scores = []

    for fold_def in fold_defs:
        # Slice candles: full history up to test end for feature warmup
        candle_slice = candles[:fold_def.test_end_idx]

        # Run simulation — features computed on full slice, sim starts at test_start_idx
        runner = CandleSimRunner(config, pair_rules)
        sim_result = runner.run(candle_slice, sim_start_idx=fold_def.test_start_idx)

        # Compute test metrics: use only the test window portion of equity/position
        test_eq = sim_result.equity_curve[fold_def.test_start_idx:fold_def.test_end_idx]
        test_pos = sim_result.position_history[fold_def.test_start_idx:fold_def.test_end_idx]
        test_candles = candles[fold_def.test_start_idx:fold_def.test_end_idx]

        # Count test trades (trades with entry_bar >= test_start_idx)
        test_trades = [t for t in sim_result.trades if t.entry_bar >= fold_def.test_start_idx]

        # Build a SimResult for the test window
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
        # Score test fold with the correct objective version
        if objective_version == 2:
            _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
            test_obj = objective_v2(test_metrics, _weights)
        else:
            _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
            test_obj = objective_v1(test_metrics, _weights)

        # Train diagnostics: use the declared rolling train window
        train_candle_slice = candles[:fold_def.train_end_idx]  # need full history for feature warmup
        train_runner = CandleSimRunner(config, pair_rules)
        train_sim_result = train_runner.run(
            train_candle_slice,
            sim_start_idx=fold_def.train_start_idx,  # start sim at train window start
        )
        train_candles_window = candles[fold_def.train_start_idx:fold_def.train_end_idx]

        # Extract train-window metrics
        train_eq = train_sim_result.equity_curve[fold_def.train_start_idx:fold_def.train_end_idx]
        train_pos = train_sim_result.position_history[fold_def.train_start_idx:fold_def.train_end_idx]
        train_trades = [t for t in train_sim_result.trades if t.entry_bar >= fold_def.train_start_idx]

        train_sim_window = SimResult(
            trades=train_trades,
            equity_curve=train_eq,
            position_history=train_pos,
            n_orders_placed=train_sim_result.n_orders_placed,
            n_orders_filled=train_sim_result.n_orders_filled,
            n_orders_rejected=train_sim_result.n_orders_rejected,
            n_market_exits=train_sim_result.n_market_exits,
            final_base_balance=train_sim_result.final_base_balance,
            final_quote_balance=train_sim_result.final_quote_balance,
        )

        train_metrics = compute_metrics(
            train_sim_window, initial_equity,
            train_candles_window, bar_interval_seconds
        )

        fold_results.append(FoldResult(
            fold_index=fold_def.fold_index,
            train_metrics=train_metrics,
            test_metrics=test_metrics,
            test_objective=test_obj,
            train_trade_count=train_metrics.trade_count,
            test_trade_count=test_metrics.trade_count,
        ))

        per_fold_scores.append(test_obj.raw_score)

    aggregate_score = robust_aggregate(per_fold_scores)

    return WalkForwardResult(
        folds=fold_results,
        fold_definitions=fold_defs,
        aggregate_score=aggregate_score,
        per_fold_scores=per_fold_scores,
        config_used=config,
        dataset_hash=dataset_hash,
    )
