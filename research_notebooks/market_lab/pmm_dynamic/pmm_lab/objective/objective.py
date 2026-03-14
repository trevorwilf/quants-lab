"""
Objective functions for PMM Dynamic parameter optimization.

v1: linear PnL + Sharpe scoring
v2: log-return formulation with per-trade edge penalty (Sharpe removed)

Both versions available for backward compatibility.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from pmm_lab.metrics.metrics import Metrics


REJECT_SCORE = -1000.0   # returned when a trial is fundamentally invalid


@dataclass(frozen=True)
class ObjectiveWeights:
    """Weights for the objective function components."""
    w_pnl: float = 1.0
    w_sharpe: float = 0.5
    w_drawdown: float = 0.3
    w_fee_drag: float = 0.2
    w_inventory: float = 0.1
    w_trade_count_penalty: float = 0.1
    w_es: float = 0.3               # Expected Shortfall penalty weight
    sharpe_clip_min: float = -2.0    # clip Sharpe below this
    sharpe_clip_max: float = 5.0     # clip Sharpe above this
    min_trades_soft: int = 50         # below this, apply soft penalty
    min_trades_hard: int = 3         # at this or below, hard reject


@dataclass(frozen=True)
class ObjectiveDecomposition:
    """Breakdown of the objective score into components for logging."""
    raw_score: float
    pnl_component: float
    sharpe_component: float
    drawdown_component: float
    fee_drag_component: float
    inventory_component: float
    trade_count_penalty: float
    es_component: float = 0.0
    is_rejected: bool = False
    reject_reason: Optional[str] = None


def objective_v1(
    metrics: Metrics,
    weights: ObjectiveWeights = ObjectiveWeights(),
) -> ObjectiveDecomposition:
    """Compute the objective score for a single backtest run.

    Score formula:
      score = w_pnl * pnl_pct
            + w_sharpe * clip(sharpe, min, max)
            - w_drawdown * max_drawdown_pct
            - w_fee_drag * fee_drag_pct
            - w_inventory * (inventory_exposure_mean * 100)
            - w_trade_count_penalty * trade_penalty

    Where:
    - trade_penalty = max(0, (min_trades_soft - trade_count) / min_trades_soft) * 10

    Hard rejection (returns REJECT_SCORE):
    - trade_count <= min_trades_hard (default: 0 trades)

    Returns ObjectiveDecomposition with the full breakdown.
    """
    # Hard rejection
    if metrics.trade_count <= weights.min_trades_hard:
        return ObjectiveDecomposition(
            raw_score=REJECT_SCORE,
            pnl_component=0.0,
            sharpe_component=0.0,
            drawdown_component=0.0,
            fee_drag_component=0.0,
            inventory_component=0.0,
            trade_count_penalty=0.0,
            is_rejected=True,
            reject_reason=f"trade_count ({metrics.trade_count}) <= min_trades_hard ({weights.min_trades_hard})",
        )

    # Components
    pnl_comp = weights.w_pnl * metrics.pnl_pct

    clipped_sharpe = np.clip(metrics.sharpe, weights.sharpe_clip_min, weights.sharpe_clip_max)
    sharpe_comp = weights.w_sharpe * clipped_sharpe

    dd_comp = weights.w_drawdown * metrics.max_drawdown_pct

    fee_comp = weights.w_fee_drag * metrics.fee_drag_pct

    inv_comp = weights.w_inventory * (metrics.inventory_exposure_mean * 100.0)

    # Trade count penalty
    if metrics.trade_count < weights.min_trades_soft:
        trade_penalty = max(0.0, (weights.min_trades_soft - metrics.trade_count) / weights.min_trades_soft) * 10.0
    else:
        trade_penalty = 0.0
    tc_penalty_comp = weights.w_trade_count_penalty * trade_penalty

    # Expected Shortfall penalty (ES is negative for losses, so we penalize)
    es_comp = weights.w_es * abs(metrics.expected_shortfall_5pct) * 100.0

    raw_score = pnl_comp + sharpe_comp - dd_comp - fee_comp - inv_comp - tc_penalty_comp - es_comp

    return ObjectiveDecomposition(
        raw_score=raw_score,
        pnl_component=pnl_comp,
        sharpe_component=sharpe_comp,
        drawdown_component=dd_comp,
        fee_drag_component=fee_comp,
        inventory_component=inv_comp,
        trade_count_penalty=tc_penalty_comp,
        es_component=es_comp,
        is_rejected=False,
    )


@dataclass(frozen=True)
class ObjectiveWeightsV2:
    """Weights for the v2 log-return objective."""
    w_pnl: float = 1.0                  # log(1+r) reward
    w_drawdown: float = 0.75            # max drawdown penalty
    w_es: float = 1.0                   # expected shortfall penalty
    w_fee_drag: float = 0.50            # fee drag penalty
    w_inventory: float = 0.25           # p95 inventory exposure penalty
    w_trade_count: float = 0.20         # insufficient trade penalty
    w_edge: float = 0.30                # negative edge penalty
    min_trades_soft: int = 50
    min_trades_hard: int = 3
    estimated_round_trip_cost_bps: float = 10.0  # estimated cost per round-trip in bps


def objective_v2(
    metrics: Metrics,
    weights: ObjectiveWeightsV2 = ObjectiveWeightsV2(),
) -> ObjectiveDecomposition:
    """Compute the v2 objective score using log-return formulation.

    Score formula:
      score = w_pnl * log(1 + r)
            - w_drawdown * dd
            - w_es * |es_5pct|
            - w_fee_drag * fd
            - w_inventory * inv95
            - w_trade_count * trade_penalty
            - w_edge * negative_edge_penalty

    Where:
    - r = net_pnl_quote / initial_equity (decimal return, derived from pnl_pct / 100)
    - dd = max_drawdown_pct / 100 (decimal)
    - fd = fee_drag_pct / 100 (decimal)
    - inv95 = inventory_exposure_p95
    - trade_penalty = max(0, (min_trades_soft - n) / min_trades_soft) if n < soft
    - negative_edge_penalty = max(0, -median_trade_pnl / estimated_cost) if median_pnl < 0
    """
    # Hard rejection
    if metrics.trade_count <= weights.min_trades_hard:
        return ObjectiveDecomposition(
            raw_score=REJECT_SCORE,
            pnl_component=0.0, sharpe_component=0.0,
            drawdown_component=0.0, fee_drag_component=0.0,
            inventory_component=0.0, trade_count_penalty=0.0,
            es_component=0.0,
            is_rejected=True,
            reject_reason=f"trade_count ({metrics.trade_count}) <= min_trades_hard ({weights.min_trades_hard})",
        )

    # Convert percentages to decimals
    r = metrics.pnl_pct / 100.0
    dd = metrics.max_drawdown_pct / 100.0
    fd = metrics.fee_drag_pct / 100.0
    inv95 = metrics.inventory_exposure_p95

    # Log-return reward (damps outsized returns)
    log_return = math.log(1.0 + r) if r > -1.0 else -10.0  # guard against total loss
    pnl_comp = weights.w_pnl * log_return

    # Drawdown penalty
    dd_comp = weights.w_drawdown * dd

    # Expected shortfall penalty
    es_comp = weights.w_es * abs(metrics.expected_shortfall_5pct)

    # Fee drag penalty
    fee_comp = weights.w_fee_drag * fd

    # Inventory penalty (p95 instead of mean)
    inv_comp = weights.w_inventory * inv95

    # Trade count penalty
    if metrics.trade_count < weights.min_trades_soft:
        tc_penalty = max(0.0, (weights.min_trades_soft - metrics.trade_count) / weights.min_trades_soft)
    else:
        tc_penalty = 0.0
    tc_comp = weights.w_trade_count * tc_penalty

    # Per-trade edge penalty
    edge_penalty = 0.0
    if metrics.median_trade_pnl_quote < 0 and metrics.trade_count > 0:
        avg_trade_value = (metrics.gross_win_quote + metrics.gross_loss_quote) / metrics.trade_count if metrics.trade_count > 0 else 1.0
        if avg_trade_value > 0:
            edge_penalty = abs(metrics.median_trade_pnl_quote) / avg_trade_value
    edge_comp = weights.w_edge * edge_penalty

    raw_score = pnl_comp - dd_comp - es_comp - fee_comp - inv_comp - tc_comp - edge_comp

    return ObjectiveDecomposition(
        raw_score=raw_score,
        pnl_component=pnl_comp,
        sharpe_component=0.0,  # not used in v2, kept for dataclass compat
        drawdown_component=dd_comp,
        fee_drag_component=fee_comp,
        inventory_component=inv_comp,
        trade_count_penalty=tc_comp,
        es_component=es_comp,
        is_rejected=False,
    )
