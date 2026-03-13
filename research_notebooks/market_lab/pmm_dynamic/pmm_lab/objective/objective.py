"""
Objective function v1: robust scoring for PMM Dynamic parameter optimization.

The objective balances profitability, risk, and cost to produce a scalar score
that rewards robust strategies over fragile high-PnL ones.
"""

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
