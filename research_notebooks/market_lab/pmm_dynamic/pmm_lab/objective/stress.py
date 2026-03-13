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
from pmm_lab.objective.objective import ObjectiveDecomposition, objective_v1, ObjectiveWeights


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
    objective_weights: ObjectiveWeights = ObjectiveWeights(),
) -> StressReport:
    """Run the baseline + all stress scenarios and return a StressReport.

    1. Run baseline (unmodified config).
    2. For each scenario: apply_scenario() -> run sim -> compute metrics -> compute objective.
    3. Identify the worst scenario (lowest objective score).
    4. Return StressReport.
    """
    if scenarios is None:
        scenarios = load_stress_scenarios()

    initial_equity = config.total_amount_quote

    # Run baseline
    baseline_runner = CandleSimRunner(config, pair_rules)
    baseline_result = baseline_runner.run(candles)
    baseline_metrics = compute_metrics(baseline_result, initial_equity, candles, bar_interval_seconds)
    baseline_objective = objective_v1(baseline_metrics, objective_weights)

    # Run each scenario
    scenario_results = []
    for scenario in scenarios:
        stressed_config, stressed_rules = apply_scenario(config, pair_rules, scenario)
        runner = CandleSimRunner(stressed_config, stressed_rules)
        sim_result = runner.run(candles)
        metrics = compute_metrics(sim_result, initial_equity, candles, bar_interval_seconds)
        obj = objective_v1(metrics, objective_weights)
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
