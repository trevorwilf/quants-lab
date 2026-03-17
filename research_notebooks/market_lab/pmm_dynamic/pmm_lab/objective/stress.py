"""
Stress testing engine.

Applies multiplier scenarios to a SimConfig and re-runs the simulation
under stressed conditions. Each scenario modifies specific fields of the
config (fees, latency, participation rate, slippage) and runs the same
candles through CandleSimRunner.
"""

import yaml
import numpy as np
from pathlib import Path
from dataclasses import dataclass, replace
from typing import List, Dict, Optional

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.metrics.metrics import Metrics, compute_metrics
from pmm_lab.objective.objective import ObjectiveDecomposition, objective_v1, objective_v2, ObjectiveWeights, ObjectiveWeightsV2


@dataclass(frozen=True)
class StressScenario:
    """One stress test scenario."""
    name: str
    description: str
    maker_fee_multiplier: float = 1.0
    taker_fee_multiplier: float = 1.0
    latency_bars_add: int = 0
    slippage_bps_multiplier: float = 1.0
    fill_participation_multiplier: float = 1.0


@dataclass
class StressResult:
    """Result of one stress scenario."""
    scenario: StressScenario
    metrics: Metrics
    objective: ObjectiveDecomposition


@dataclass
class StressReport:
    """Full stress test report across all scenarios."""
    baseline_metrics: Metrics
    baseline_objective: ObjectiveDecomposition
    scenario_results: List[StressResult]
    worst_scenario: str
    worst_score: float


def load_stress_scenarios(
    yaml_path: Optional[str] = None,
) -> List[StressScenario]:
    """Load stress scenarios from YAML config file.

    Default path: configs/stress_scenarios.yaml relative to project root.
    """
    if yaml_path is None:
        default_path = Path(__file__).resolve().parent.parent.parent / "configs" / "stress_scenarios.yaml"
        yaml_path = str(default_path)

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    scenarios = []
    for s in data["scenarios"]:
        scenarios.append(StressScenario(
            name=s["name"],
            description=s["description"],
            maker_fee_multiplier=s.get("maker_fee_multiplier", 1.0),
            taker_fee_multiplier=s.get("taker_fee_multiplier", 1.0),
            latency_bars_add=s.get("latency_bars_add", 0),
            slippage_bps_multiplier=s.get("slippage_bps_multiplier", 1.0),
            fill_participation_multiplier=s.get("fill_participation_multiplier", 1.0),
        ))

    return scenarios


def apply_scenario(
    config: SimConfig,
    pair_rules: PairRules,
    scenario: StressScenario,
) -> tuple:
    """Apply a stress scenario to a SimConfig and PairRules, returning modified copies.

    Modifications:
    - maker_fee *= maker_fee_multiplier
    - taker_fee *= taker_fee_multiplier
    - latency_bars += latency_bars_add
    - slippage_bps *= slippage_bps_multiplier
    - fill_participation_rate *= fill_participation_multiplier

    Returns (modified_config, modified_pair_rules).
    """
    # Modify SimConfig (frozen, use replace)
    new_config = replace(
        config,
        latency_bars=config.latency_bars + scenario.latency_bars_add,
        slippage_bps=config.slippage_bps * scenario.slippage_bps_multiplier,
        fill_participation_rate=config.fill_participation_rate * scenario.fill_participation_multiplier,
    )

    # Modify PairRules fees (frozen, use replace)
    new_fees = FeeConfig(
        maker_fee=pair_rules.fees.maker_fee * scenario.maker_fee_multiplier,
        taker_fee=pair_rules.fees.taker_fee * scenario.taker_fee_multiplier,
    )
    new_pair_rules = replace(pair_rules, fees=new_fees)

    return new_config, new_pair_rules


def run_stress_tests(
    candles: np.ndarray,
    config: SimConfig,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    scenarios: Optional[List[StressScenario]] = None,
    objective_weights=None,
    objective_version: int = 1,
    precomputed_signals=None,
    score_start_idx: Optional[int] = None,
    score_end_idx: Optional[int] = None,
    sim_start_idx: Optional[int] = None,
) -> StressReport:
    """Run the baseline + all stress scenarios and return a StressReport.

    1. Run baseline (unmodified config).
    2. For each scenario: apply_scenario() -> run sim -> compute metrics -> compute objective.
    3. Identify the worst scenario (lowest objective score).
    4. Return StressReport.

    Parameters
    ----------
    score_start_idx, score_end_idx : int, optional
        If provided, metrics are scored only on the candles[score_start_idx:score_end_idx]
        window. The full candle prefix is still used for feature warmup and simulation.
    sim_start_idx : int, optional
        If provided, simulation starts at this bar index (warm-start).
    """
    if scenarios is None:
        scenarios = load_stress_scenarios()

    # Build scoring function based on objective version
    if objective_version == 2:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
        _score = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
        _score = lambda m: objective_v1(m, _weights)

    initial_equity = config.total_amount_quote

    # Run baseline
    baseline_runner = CandleSimRunner(config, pair_rules)

    # Auto-precompute signals if not supplied — safe because apply_scenario()
    # does not modify indicator parameters (only fees, latency, slippage, fill rate)
    if precomputed_signals is None:
        precomputed_signals = baseline_runner.compute_signals(candles)

    baseline_result = baseline_runner.run_with_signals(candles, precomputed_signals, sim_start_idx=sim_start_idx)

    # Extract scoring window if specified
    if score_start_idx is not None:
        _end = score_end_idx if score_end_idx is not None else len(candles)
        baseline_metrics = _extract_window_metrics(
            baseline_result, candles, initial_equity, bar_interval_seconds,
            score_start_idx, _end,
        )
    else:
        baseline_metrics = compute_metrics(baseline_result, initial_equity, candles, bar_interval_seconds)
    baseline_objective = _score(baseline_metrics)

    # Run each scenario
    scenario_results = []
    for scenario in scenarios:
        stressed_config, stressed_rules = apply_scenario(config, pair_rules, scenario)
        runner = CandleSimRunner(stressed_config, stressed_rules)
        sim_result = runner.run_with_signals(candles, precomputed_signals, sim_start_idx=sim_start_idx)

        if score_start_idx is not None:
            _end = score_end_idx if score_end_idx is not None else len(candles)
            metrics = _extract_window_metrics(
                sim_result, candles, initial_equity, bar_interval_seconds,
                score_start_idx, _end,
            )
        else:
            metrics = compute_metrics(sim_result, initial_equity, candles, bar_interval_seconds)
        obj = _score(metrics)
        scenario_results.append(StressResult(
            scenario=scenario,
            metrics=metrics,
            objective=obj,
        ))

    # Find worst scenario
    worst_idx = 0
    worst_score = scenario_results[0].objective.raw_score
    for i, sr in enumerate(scenario_results):
        if sr.objective.raw_score < worst_score:
            worst_score = sr.objective.raw_score
            worst_idx = i

    return StressReport(
        baseline_metrics=baseline_metrics,
        baseline_objective=baseline_objective,
        scenario_results=scenario_results,
        worst_scenario=scenario_results[worst_idx].scenario.name,
        worst_score=worst_score,
    )


def _extract_window_metrics(
    sim_result: SimResult,
    candles: np.ndarray,
    initial_equity: float,
    bar_interval_seconds: int,
    start_idx: int,
    end_idx: int,
) -> Metrics:
    """Extract metrics for a scoring window from a full simulation result."""
    window_eq = sim_result.equity_curve[start_idx:end_idx]
    window_pos = sim_result.position_history[start_idx:end_idx]
    window_candles = candles[start_idx:end_idx]
    window_trades = [t for t in sim_result.trades if t.entry_bar >= start_idx]

    window_result = SimResult(
        trades=window_trades,
        equity_curve=window_eq,
        position_history=window_pos,
        n_orders_placed=sim_result.n_orders_placed,
        n_orders_filled=sim_result.n_orders_filled,
        n_orders_rejected=sim_result.n_orders_rejected,
        n_market_exits=sim_result.n_market_exits,
        final_base_balance=sim_result.final_base_balance,
        final_quote_balance=sim_result.final_quote_balance,
    )
    return compute_metrics(window_result, initial_equity, window_candles, bar_interval_seconds)


def run_fold_local_stress(
    candles: np.ndarray,
    config: SimConfig,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    fold_test_start_idx: int,
    fold_test_end_idx: int,
    scenarios: Optional[List[StressScenario]] = None,
    objective_weights=None,
    objective_version: int = 1,
    precomputed_signals=None,
) -> List[float]:
    """Run stress tests on a single fold's test window only.

    This avoids the leakage problem where full-dataset stress scores
    leak future data into the optimization target.

    Parameters
    ----------
    candles : np.ndarray
        Full candle array (needed for feature warmup).
    config : SimConfig
        Configuration to stress.
    pair_rules : PairRules
        Exchange rules.
    bar_interval_seconds : int
        Candle interval.
    fold_test_start_idx : int
        Start of the test window (inclusive).
    fold_test_end_idx : int
        End of the test window (exclusive).
    scenarios : List[StressScenario], optional
        Stress scenarios. If None, loads from YAML.
    objective_weights : ObjectiveWeights
        Weights for objective scoring.

    Returns
    -------
    List[float]
        Objective scores for each stress scenario on this fold's test window.
    """
    if scenarios is None:
        scenarios = load_stress_scenarios()

    # Build scoring function based on objective version
    if objective_version == 2:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
        _score = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
        _score = lambda m: objective_v1(m, _weights)

    initial_equity = config.total_amount_quote
    candle_slice = candles[:fold_test_end_idx]

    # Auto-precompute signals if not supplied
    if precomputed_signals is None:
        precomputed_signals = CandleSimRunner(config, pair_rules).compute_signals(candles)

    stress_scores = []
    for scenario in scenarios:
        stressed_config, stressed_rules = apply_scenario(config, pair_rules, scenario)
        runner = CandleSimRunner(stressed_config, stressed_rules)
        sim_result = runner.run_with_signals(candle_slice, precomputed_signals, sim_start_idx=fold_test_start_idx)

        # Extract test window
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
