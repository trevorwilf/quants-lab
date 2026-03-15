"""
Holdout validation.

Splits candle data into development (first 80%) and holdout (last 20%).
The optimizer only sees development data. After optimization, the top-k
candidates are evaluated on the holdout to verify generalization.

Usage:
    dev, holdout = split_holdout(candles, holdout_fraction=0.20)
    # ... run optimization on dev ...
    report = evaluate_holdout(holdout, top_k_configs, pair_rules, ...)
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.metrics.metrics import Metrics, compute_metrics
from pmm_lab.objective.objective import (
    objective_v1, objective_v2, ObjectiveDecomposition,
    ObjectiveWeights, REJECT_SCORE,
)
from pmm_lab.objective.stress import run_stress_tests, StressReport
from pmm_lab.features.regime import classify_regime, RegimeClassification

logger = logging.getLogger(__name__)


def split_holdout(
    candles: np.ndarray,
    holdout_fraction: float = 0.20,
    min_holdout_bars: int = 100,
) -> Tuple[np.ndarray, np.ndarray]:
    """Split candles into development and holdout portions.

    Parameters
    ----------
    candles : np.ndarray
        Full candle array.
    holdout_fraction : float
        Fraction of data reserved for holdout (default 20%).
    min_holdout_bars : int
        Minimum bars in holdout. If holdout would be smaller, raises ValueError.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (development_candles, holdout_candles)
    """
    n = len(candles)
    holdout_size = max(int(n * holdout_fraction), min_holdout_bars)

    if holdout_size >= n:
        raise ValueError(
            f"Holdout size ({holdout_size}) >= total bars ({n}). "
            f"Need more data or reduce holdout_fraction."
        )

    split_idx = n - holdout_size
    return candles[:split_idx], candles[split_idx:]


@dataclass
class HoldoutCandidateResult:
    """Result of evaluating one candidate on holdout data."""
    rank: int
    config: SimConfig
    metrics: Metrics
    objective: ObjectiveDecomposition
    stress_report: Optional[StressReport] = None
    regime: Optional[RegimeClassification] = None
    development_score: float = 0.0  # the score from optimization (for comparison)


@dataclass
class HoldoutReport:
    """Full holdout validation report."""
    holdout_bars: int
    holdout_start_timestamp: int
    holdout_end_timestamp: int
    regime: RegimeClassification
    candidates: List[HoldoutCandidateResult]
    best_holdout_rank: int                    # which candidate scored best on holdout
    best_holdout_score: float
    dev_vs_holdout_collapse: bool             # True if holdout score << development score
    passed: bool                              # overall holdout validation pass/fail


def evaluate_holdout(
    holdout_candles: np.ndarray,
    candidate_configs: List[Tuple[SimConfig, float]],  # (config, dev_score) pairs
    pair_rules: PairRules,
    bar_interval_seconds: int,
    run_stress: bool = True,
    objective_version: int = 1,
    objective_weights=None,
    collapse_threshold: float = 0.60,
) -> HoldoutReport:
    """Evaluate top-k candidates on holdout data.

    Parameters
    ----------
    holdout_candles : np.ndarray
        The held-out candle data (never seen during optimization).
    candidate_configs : List[Tuple[SimConfig, float]]
        List of (config, development_score) tuples, ranked best first.
    pair_rules : PairRules
        Exchange rules.
    bar_interval_seconds : int
        Candle interval.
    run_stress : bool
        Whether to run stress tests on holdout.
    objective_version : int
        1 or 2.
    objective_weights : optional
        Objective weights.
    collapse_threshold : float
        If holdout_score < dev_score * (1 - collapse_threshold), it's a collapse.

    Returns
    -------
    HoldoutReport
    """
    # Select objective function
    if objective_version == 2:
        from pmm_lab.objective.objective import ObjectiveWeightsV2
        _weights = objective_weights or ObjectiveWeightsV2()
        obj_fn = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights or ObjectiveWeights()
        obj_fn = lambda m: objective_v1(m, _weights)

    # Classify holdout regime
    holdout_regime = classify_regime(holdout_candles)

    candidates = []
    for rank, (config, dev_score) in enumerate(candidate_configs):
        initial_equity = config.total_amount_quote

        # Run simulation on holdout
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(holdout_candles)
        metrics = compute_metrics(result, initial_equity, holdout_candles, bar_interval_seconds)
        obj = obj_fn(metrics)

        # Optional stress on holdout
        stress_report = None
        if run_stress:
            stress_report = run_stress_tests(
                holdout_candles, config, pair_rules, bar_interval_seconds,
            )

        candidates.append(HoldoutCandidateResult(
            rank=rank,
            config=config,
            metrics=metrics,
            objective=obj,
            stress_report=stress_report,
            regime=holdout_regime,
            development_score=dev_score,
        ))

    # Find best on holdout
    valid_candidates = [c for c in candidates if c.objective.raw_score != REJECT_SCORE]
    if valid_candidates:
        best = max(valid_candidates, key=lambda c: c.objective.raw_score)
        best_rank = best.rank
        best_score = best.objective.raw_score
    else:
        best_rank = -1
        best_score = REJECT_SCORE

    # Check for collapse: best holdout score vs its dev score
    collapse = False
    if valid_candidates and best_score != REJECT_SCORE:
        best_dev = best.development_score
        if best_dev > 0 and best_score < best_dev * (1 - collapse_threshold):
            collapse = True
        elif best_dev > 0 and best_score < 0:
            collapse = True

    # Overall pass: holdout score > 0 and no dramatic collapse
    passed = bool(best_score > 0 and not collapse)

    return HoldoutReport(
        holdout_bars=len(holdout_candles),
        holdout_start_timestamp=int(holdout_candles["timestamp"][0]),
        holdout_end_timestamp=int(holdout_candles["timestamp"][-1]),
        regime=holdout_regime,
        candidates=candidates,
        best_holdout_rank=best_rank,
        best_holdout_score=best_score,
        dev_vs_holdout_collapse=collapse,
        passed=passed,
    )
