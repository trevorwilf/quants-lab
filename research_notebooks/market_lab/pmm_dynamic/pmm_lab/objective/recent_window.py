"""
Recent-window evaluation.

Warm-started evaluation of the most recent N days of candle data.
Used as an additional stop-ship gate to verify that the strategy
performs acceptably on the most recent market conditions.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List

import numpy as np

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.metrics.metrics import Metrics, compute_metrics
from pmm_lab.objective.objective import (
    objective_v1, objective_v2, ObjectiveDecomposition,
    ObjectiveWeights, ObjectiveWeightsV2, REJECT_SCORE,
)
from pmm_lab.objective.stress import (
    StressReport, StressScenario, run_stress_tests, load_stress_scenarios,
)

logger = logging.getLogger(__name__)


@dataclass
class RecentWindowResult:
    """Result of recent-window evaluation."""
    recent_bars: int
    recent_start_timestamp: int
    recent_end_timestamp: int
    metrics: Metrics
    objective: ObjectiveDecomposition
    stress_report: Optional[StressReport] = None
    passed: bool = False
    reason: str = ""


def evaluate_recent_window(
    full_candles: np.ndarray,
    config: SimConfig,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    recent_days: int = 28,
    start_ts: Optional[int] = None,
    objective_version: int = 2,
    objective_weights=None,
    run_stress: bool = True,
    scenarios: Optional[List[StressScenario]] = None,
    min_trades: int = 5,
    max_drawdown_pct: float = 50.0,
    min_stress_score: float = -10.0,
) -> RecentWindowResult:
    """Warm-started evaluation of the most recent N days.

    1. Identify the timestamp for last `recent_days` calendar days.
    2. Compute signals on full history.
    3. Run simulator warm-started at recent-window start.
    4. Score metrics only on the recent-window slice.
    5. Optionally run stress on the recent window.

    Parameters
    ----------
    full_candles : np.ndarray
        Complete candle dataset.
    config : SimConfig
        Strategy configuration.
    pair_rules : PairRules
        Exchange rules.
    bar_interval_seconds : int
        Candle interval.
    recent_days : int
        Number of recent calendar days to evaluate. Default 28.
    start_ts : int, optional
        Override for recent window start timestamp.
        If None, computed as last_ts - recent_days * 86400.
    objective_version : int
        1 or 2 (default 2).
    objective_weights : optional
        Objective weights.
    run_stress : bool
        Whether to run stress tests on the recent window.
    scenarios : list, optional
        Stress scenarios. If None, loads from YAML.
    min_trades : int
        Minimum trades required in recent window.
    max_drawdown_pct : float
        Maximum drawdown allowed in recent window.
    min_stress_score : float
        Minimum worst stress score allowed.

    Returns
    -------
    RecentWindowResult
    """
    n = len(full_candles)
    last_ts = int(full_candles["timestamp"][-1])

    # Determine recent window start
    if start_ts is None:
        start_ts = last_ts - recent_days * 86400

    # Find the index where recent window begins
    timestamps = full_candles["timestamp"]
    recent_start_idx = int(np.searchsorted(timestamps, start_ts))

    if recent_start_idx >= n:
        return RecentWindowResult(
            recent_bars=0,
            recent_start_timestamp=start_ts,
            recent_end_timestamp=last_ts,
            metrics=None,
            objective=None,
            passed=False,
            reason=f"No bars in recent {recent_days}d window",
        )

    recent_bars = n - recent_start_idx
    recent_candles = full_candles[recent_start_idx:]

    # Build scoring function
    if objective_version == 2:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeightsV2) else ObjectiveWeightsV2()
        _score = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights if isinstance(objective_weights, ObjectiveWeights) else ObjectiveWeights()
        _score = lambda m: objective_v1(m, _weights)

    initial_equity = config.total_amount_quote

    # Compute signals on full history, run warm-started at recent window
    runner = CandleSimRunner(config, pair_rules)
    signals = runner.compute_signals(full_candles)
    result = runner.run_with_signals(full_candles, signals, sim_start_idx=recent_start_idx)

    # Extract recent-window metrics
    window_eq = result.equity_curve[recent_start_idx:]
    window_pos = result.position_history[recent_start_idx:]
    window_trades = [t for t in result.trades if t.entry_bar >= recent_start_idx]

    window_result = SimResult(
        trades=window_trades,
        equity_curve=window_eq,
        position_history=window_pos,
        n_orders_placed=result.n_orders_placed,
        n_orders_filled=result.n_orders_filled,
        n_orders_rejected=result.n_orders_rejected,
        n_market_exits=result.n_market_exits,
        final_base_balance=result.final_base_balance,
        final_quote_balance=result.final_quote_balance,
    )

    metrics = compute_metrics(window_result, initial_equity, recent_candles, bar_interval_seconds)
    objective = _score(metrics)

    # Optional stress on recent window
    stress_report = None
    if run_stress:
        stress_report = run_stress_tests(
            full_candles, config, pair_rules, bar_interval_seconds,
            scenarios=scenarios,
            objective_version=objective_version,
            objective_weights=_weights,
            precomputed_signals=signals,
            score_start_idx=recent_start_idx,
            score_end_idx=n,
            sim_start_idx=recent_start_idx,
        )

    # Acceptance criteria
    reasons = []
    if objective.raw_score <= 0:
        reasons.append(f"recent objective score {objective.raw_score:.4f} <= 0")
    if metrics.pnl_pct < 0:
        reasons.append(f"recent PnL {metrics.pnl_pct:.4f}% < 0")
    if metrics.trade_count < min_trades:
        reasons.append(f"recent trades {metrics.trade_count} < {min_trades}")
    if metrics.max_drawdown_pct > max_drawdown_pct:
        reasons.append(f"recent max DD {metrics.max_drawdown_pct:.2f}% > {max_drawdown_pct}%")
    if run_stress and stress_report is not None:
        if stress_report.worst_score < min_stress_score:
            reasons.append(
                f"recent worst stress {stress_report.worst_score:.4f} < {min_stress_score}"
            )

    passed = len(reasons) == 0

    return RecentWindowResult(
        recent_bars=recent_bars,
        recent_start_timestamp=int(timestamps[recent_start_idx]),
        recent_end_timestamp=last_ts,
        metrics=metrics,
        objective=objective,
        stress_report=stress_report,
        passed=passed,
        reason="; ".join(reasons) if reasons else "",
    )
