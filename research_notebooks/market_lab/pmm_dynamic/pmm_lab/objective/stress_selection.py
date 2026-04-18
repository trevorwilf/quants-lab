"""
Phase-2 candidate selection with early pruning.

Orchestrates stress testing of top candidates from phase-1 optimization,
with signal caching, config deduplication, and scenario-level early pruning.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.runner_dispatch import run_simulation
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import (
    objective_v1, objective_v2, ObjectiveWeights, ObjectiveWeightsV2,
    ObjectiveDecomposition,
)
from pmm_lab.objective.stress import (
    StressScenario, StressReport, StressResult, apply_scenario,
    load_stress_scenarios,
)
from pmm_lab.objective.signal_cache import signal_cache_key

logger = logging.getLogger(__name__)

# Preferred scenario ordering for pruning (harsh scenarios first)
_HARSH_SCENARIO_ORDER = [
    "combined_adverse",
    "very_low_liquidity",
    "fees_2x",
    "extreme_slippage",
    "latency_plus3",
]


def _reorder_scenarios_for_pruning(
    scenarios: List[StressScenario],
) -> Tuple[List[StressScenario], List[int]]:
    """Reorder scenarios so harsh ones come first. Return (reordered, original_indices)."""
    name_to_idx = {s.name: i for i, s in enumerate(scenarios)}
    ordered = []
    used = set()

    for name in _HARSH_SCENARIO_ORDER:
        if name in name_to_idx:
            idx = name_to_idx[name]
            ordered.append((idx, scenarios[idx]))
            used.add(idx)

    for i, s in enumerate(scenarios):
        if i not in used:
            ordered.append((i, s))

    original_indices = [pair[0] for pair in ordered]
    reordered = [pair[1] for pair in ordered]
    return reordered, original_indices


def select_best_stressed_candidate(
    top_candidates: list,
    candles: np.ndarray,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    scenarios: Optional[List[StressScenario]] = None,
    signal_cache: Optional[dict] = None,
    objective_version: int = 1,
    objective_weights=None,
    diagnostics: bool = True,
    shared_signal_cache=None,
    dataset_key: str = "dev",
    regime_candles: Optional[np.ndarray] = None,
    apply_scenario_fn: Optional[Callable] = None,
) -> Tuple[Optional[dict], dict]:
    """Select the best candidate via stress testing with early pruning.

    Parameters
    ----------
    top_candidates : list
        List of dicts with at least "config" (SimConfig), "trial_number", "phase1_score".
        Must be in descending phase-1 score order.
    candles : np.ndarray
        Full candle dataset.
    pair_rules : PairRules
        Exchange rules.
    bar_interval_seconds : int
        Candle interval.
    scenarios : list, optional
        Stress scenarios. If None, loads from YAML.
    signal_cache : dict, optional
        Shared signal cache. If None, creates a local one.
    objective_version : int
        1 or 2.
    objective_weights : optional
        Objective weights.
    diagnostics : bool
        If True, populate diagnostics dict.

    Returns
    -------
    (best_candidate, diagnostics_dict)
        best_candidate is the winning dict (augmented with stress_report, robust_score, etc.)
        or None if no candidates.
        diagnostics_dict has: candidates_evaluated, candidates_pruned,
        signal_cache_hits, signal_cache_misses.
    """
    if scenarios is None:
        scenarios = load_stress_scenarios()

    if signal_cache is None:
        signal_cache = {}

    # Build scoring function
    if objective_version == 2:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
        _score = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
        _score = lambda m: objective_v1(m, _weights)

    diag = {
        "candidates_evaluated": 0,
        "candidates_pruned": 0,
        "candidates_fully_evaluated": 0,
        "signal_cache_hits": 0,
        "signal_cache_misses": 0,
    }

    if not top_candidates:
        return None, diag

    # Reorder scenarios for pruning efficiency
    pruning_scenarios, original_indices = _reorder_scenarios_for_pruning(scenarios)
    # Inverse mapping: pruning_order_idx -> original_order_idx
    restore_order = [0] * len(scenarios)
    for pruning_idx, orig_idx in enumerate(original_indices):
        restore_order[orig_idx] = pruning_idx

    incumbent = None  # best candidate so far
    incumbent_robust = float("-inf")

    for cand_idx, candidate in enumerate(top_candidates):
        config = candidate["config"]
        cand_engine_config = candidate.get("engine_config")
        initial_equity = (
            config.total_amount_quote if isinstance(config, SimConfig)
            else cand_engine_config.total_amount_quote if cand_engine_config is not None
            else 100.0
        )
        diag["candidates_evaluated"] += 1

        # Get or compute signals — config-aware probe so EMA's regime-hashed
        # dataset key is honored (Stage 2 fix: was using bare key and missing hits).
        key = signal_cache_key(config)
        if key in signal_cache:
            signals = signal_cache[key]
            diag["signal_cache_hits"] += 1
        else:
            cached = None
            if shared_signal_cache is not None:
                cached = shared_signal_cache.get_for_config(
                    config, dataset_key, regime_candles=regime_candles,
                )
            if cached is not None:
                signals = cached
                signal_cache[key] = signals
                diag["signal_cache_hits"] += 1
            else:
                if isinstance(config, SimConfig):
                    signals = CandleSimRunner(config, pair_rules).compute_signals(candles)
                else:
                    from pmm_lab.objective.signal_cache import SharedSignalCache
                    _tmp = shared_signal_cache if shared_signal_cache is not None else SharedSignalCache()
                    signals = _tmp.get_or_compute(
                        config, dataset_key, candles, pair_rules,
                        regime_candles=regime_candles,
                    )
                signal_cache[key] = signals
                diag["signal_cache_misses"] += 1

        # Run baseline
        baseline_result = run_simulation(
            config, pair_rules, candles, signals,
            engine_config=cand_engine_config, regime_candles=regime_candles,
        )
        baseline_metrics = compute_metrics(
            baseline_result, initial_equity, candles, bar_interval_seconds
        )
        baseline_obj = _score(baseline_metrics)
        baseline_score = baseline_obj.raw_score

        # Evaluate scenarios with early pruning
        scenario_results_pruning_order = []
        worst_score_so_far = baseline_score
        pruned = False

        for sc_idx, scenario in enumerate(pruning_scenarios):
            if apply_scenario_fn is not None:
                stressed_config, stressed_engine_config, stressed_rules = apply_scenario_fn(
                    config, cand_engine_config, pair_rules, scenario,
                )
            elif isinstance(config, SimConfig):
                stressed_config, stressed_rules = apply_scenario(config, pair_rules, scenario)
                stressed_engine_config = None
            else:
                # Non-SimConfig without apply_scenario_fn: skip stress scenarios for this candidate
                logger.debug(
                    "select_best_stressed_candidate: non-SimConfig %s without "
                    "apply_scenario_fn; skipping scenario %s.",
                    type(config).__name__, scenario.name,
                )
                continue
            sc_result = run_simulation(
                stressed_config, stressed_rules, candles, signals,
                engine_config=stressed_engine_config, regime_candles=regime_candles,
            )
            sc_metrics = compute_metrics(
                sc_result, initial_equity, candles, bar_interval_seconds
            )
            sc_obj = _score(sc_metrics)
            scenario_results_pruning_order.append(StressResult(
                scenario=scenario, metrics=sc_metrics, objective=sc_obj,
            ))

            if sc_obj.raw_score < worst_score_so_far:
                worst_score_so_far = sc_obj.raw_score

            # Early pruning: can this candidate possibly beat the incumbent?
            if cand_idx > 0 and incumbent is not None:
                upper_bound = 0.5 * baseline_score + 0.5 * worst_score_so_far
                if upper_bound <= incumbent_robust:
                    pruned = True
                    diag["candidates_pruned"] += 1
                    break

        if pruned:
            continue

        diag["candidates_fully_evaluated"] += 1

        if not scenario_results_pruning_order:
            # No scenarios could be run (non-SimConfig + no apply_scenario_fn).
            # Use baseline as the robust score — stress is informational elsewhere.
            worst_score = baseline_score
            stress_report = StressReport(
                baseline_metrics=baseline_metrics,
                baseline_objective=baseline_obj,
                scenario_results=[],
                worst_scenario="(stress skipped)",
                worst_score=worst_score,
            )
            robust_score = baseline_score
        else:
            # Restore original scenario order for the report
            scenario_results_original_order = [None] * len(scenarios)
            for pruning_idx, sr in enumerate(scenario_results_pruning_order):
                orig_idx = original_indices[pruning_idx]
                scenario_results_original_order[orig_idx] = sr

            # Find worst scenario (only among non-None slots)
            worst_idx = None
            worst_score = baseline_score
            for i, sr in enumerate(scenario_results_original_order):
                if sr is None:
                    continue
                if worst_idx is None or sr.objective.raw_score < worst_score:
                    worst_score = sr.objective.raw_score
                    worst_idx = i

            stress_report = StressReport(
                baseline_metrics=baseline_metrics,
                baseline_objective=baseline_obj,
                scenario_results=scenario_results_original_order,
                worst_scenario=(scenario_results_original_order[worst_idx].scenario.name
                                if worst_idx is not None else "(baseline)"),
                worst_score=worst_score,
            )

            robust_score = 0.5 * baseline_score + 0.5 * worst_score

        # Update incumbent (strictly greater — ties go to earlier candidate)
        if robust_score > incumbent_robust:
            incumbent_robust = robust_score
            incumbent = dict(candidate)
            incumbent["stress_report"] = stress_report
            incumbent["baseline_score"] = baseline_score
            incumbent["worst_scenario"] = stress_report.worst_scenario
            incumbent["worst_score"] = worst_score
            incumbent["robust_score"] = robust_score

    return incumbent, diag
