"""
MACD-BB stress testing helpers.

Provides MACD-BB-specific stress testing that works with EngineConfig +
GenericSimRunner, without modifying the existing PMM stress module.
"""

import numpy as np
from dataclasses import replace
from typing import List, Optional

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.executor_model import SimResult
from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import (
    objective_v1, objective_v2, ObjectiveWeights, ObjectiveWeightsV2
)
from pmm_lab.objective.stress import StressScenario, load_stress_scenarios


def apply_scenario_engine_config(
    engine_config: EngineConfig,
    pair_rules: PairRules,
    scenario: StressScenario,
) -> tuple:
    """Apply a stress scenario to EngineConfig + PairRules."""
    new_entry_spread = engine_config.entry_spread_bps + scenario.entry_spread_bps_add + scenario.spread_widen_bps
    new_maker_fill = (scenario.maker_fill_probability_override
                      if scenario.maker_fill_probability_override is not None
                      else engine_config.maker_fill_probability)

    new_config = replace(
        engine_config,
        latency_bars=engine_config.latency_bars + scenario.latency_bars_add,
        slippage_bps=engine_config.slippage_bps * scenario.slippage_bps_multiplier,
        fill_participation_rate=engine_config.fill_participation_rate * scenario.fill_participation_multiplier,
        entry_spread_bps=new_entry_spread,
        maker_fill_probability=new_maker_fill,
    )

    new_fees = FeeConfig(
        maker_fee=pair_rules.fees.maker_fee * scenario.maker_fee_multiplier,
        taker_fee=pair_rules.fees.taker_fee * scenario.taker_fee_multiplier,
    )
    new_pair_rules = replace(pair_rules, fees=new_fees)

    return new_config, new_pair_rules


def run_macd_bb_fold_local_stress(
    candles: np.ndarray,
    strategy_config: MACDBBStrategyConfig,
    engine_config: EngineConfig,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    fold_test_start_idx: int,
    fold_test_end_idx: int,
    scenarios: Optional[List[StressScenario]] = None,
    objective_weights=None,
    objective_version: int = 1,
    precomputed_signals=None,
) -> List[float]:
    """Run stress tests for MACD-BB on a single fold's test window.

    Equivalent to run_fold_local_stress but uses GenericSimRunner.
    """
    if scenarios is None:
        scenarios = load_stress_scenarios()

    if objective_version == 2:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
        _score = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
        _score = lambda m: objective_v1(m, _weights)

    initial_equity = engine_config.total_amount_quote
    candle_slice = candles[:fold_test_end_idx]

    strategy = MACDBBStrategy(strategy_config)

    if precomputed_signals is None:
        precomputed_signals = strategy.compute_signals(candles)

    stress_scores = []
    for scenario in scenarios:
        stressed_config, stressed_rules = apply_scenario_engine_config(
            engine_config, pair_rules, scenario
        )

        if scenario.volume_multiplier != 1.0:
            stressed_slice = candle_slice.copy()
            stressed_slice["volume"] = (candle_slice["volume"].astype("float64") *
                                         scenario.volume_multiplier).astype(candle_slice["volume"].dtype)
        else:
            stressed_slice = candle_slice

        engine = SimEngine(stressed_config, stressed_rules)
        sim_result = engine.run_with_signals(
            stressed_slice, strategy, precomputed_signals,
            sim_start_idx=fold_test_start_idx,
        )

        test_eq = sim_result.equity_curve[fold_test_start_idx:fold_test_end_idx]
        test_pos = sim_result.position_history[fold_test_start_idx:fold_test_end_idx]
        test_candles = candles[fold_test_start_idx:fold_test_end_idx]
        test_trades = [t for t in sim_result.trades if t.entry_bar >= fold_test_start_idx]

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
        test_obj = _score(test_metrics)
        stress_scores.append(test_obj.raw_score)

    return stress_scores
