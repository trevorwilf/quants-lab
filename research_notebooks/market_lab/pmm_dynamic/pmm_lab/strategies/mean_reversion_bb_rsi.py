"""
Mean-reversion BB+RSI directional strategy.

Wraps `compute_mr_bb_rsi_features` in the Strategy protocol so it can be
driven by `SimEngine.run_with_signals`.

Design notes:
 - Long-only (D5): rejects any attempt to build a sell order.
 - D13 inventory guard: before building, require
   `inventory.available_quote_for_buy() >= capital_per_entry * 0.99`.
 - D3 rolling 24h cap: tracked per-instance in `_entry_timestamps`. Because
   `run_with_signals` does NOT reset state, callers must instantiate a fresh
   strategy per fold/run, OR call `strategy.reset_state()` between runs.
 - `max_executors_per_side` is an invariant: must be 1 for this MVP
   (`__post_init__` rejects non-1 values).
 - Placed-order tracking (not filled-order): we add to `_entry_timestamps`
   only when all gates pass and an Order is enqueued. This is a conservative
   over-approximation — an order that is placed but does not fill still
   counts against the daily cap. That mirrors the live controller's
   creation-time gate rather than fill-time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from pmm_lab.config.exchange_rules import (
    check_min_notional,
    check_order_size,
    round_amount,
    round_price,
)
from pmm_lab.config.params import PairRules
from pmm_lab.features.mean_reversion_bb_rsi_features import (
    MRBBRSIFeatureConfig,
    compute_mr_bb_rsi_features,
)
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.strategy import SignalOutput

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MeanReversionBBRSIStrategyConfig:
    """MR BB+RSI strategy parameters.

    Defaults mirror the live controller's Pydantic defaults.
    """

    bb_length: int = 80
    bb_std: float = 2.0
    bbp_entry_threshold: float = 0.20
    rsi_length: int = 14
    rsi_entry_threshold: float = 40.0
    use_trend_filter: bool = True
    trend_ema_length: int = 200
    min_trend_slope: float = 0.0  # fixed at 0.0 per D17 — not optimized
    atr_length: int = 14
    max_atr_pct_for_entry: float = 0.10
    volume_filter_window: int = 288
    min_volume_quantile: float = 0.30

    # Live-safety gates
    max_spread_pct: float = 0.006  # not enforced in backtest (D2); still exported
    max_trades_per_day: int = 6   # enforced in backtest via rolling 24h counter (D3)

    # Execution invariants
    max_executors_per_side: int = 1

    # Mode
    timestamp_mode: str = "open"
    controller_compat: bool = False

    def to_fingerprint(self) -> tuple:
        """Produce a hashable fingerprint of ALL fields. Exact match only.

        Mirrors `pmm_lab.sim.executor_model.SimConfig.to_fingerprint`.
        Used by Phase-2 candidate dedup in sweep notebooks.
        """
        from dataclasses import fields
        parts = []
        for f in fields(self):
            val = getattr(self, f.name)
            if isinstance(val, list):
                val = tuple(val)
            parts.append(val)
        return tuple(parts)

    def __post_init__(self):
        if self.max_executors_per_side != 1:
            raise ValueError(
                f"MeanReversionBBRSIStrategy requires max_executors_per_side=1 "
                f"(MVP invariant per D); got {self.max_executors_per_side}"
            )


class MeanReversionBBRSIStrategy:
    """MR BB+RSI directional trading strategy.

    Implements the Strategy protocol:
     - compute_signals: wraps compute_mr_bb_rsi_features.
     - build_orders: constructs a single BUY when signal=1 and all gates pass.

    State:
     - `self._entry_timestamps` holds timestamps of successfully-placed orders,
       used by the rolling-24h cap (D3). **The engine does not call a reset hook**,
       so the caller must instantiate a fresh Strategy per fold/run, OR call
       `reset_state()` explicitly.
    """

    def __init__(self, config: MeanReversionBBRSIStrategyConfig):
        self.config = config
        self._entry_timestamps: List[int] = []

    def reset_state(self) -> None:
        """Clear the rolling 24h placed-order buffer."""
        self._entry_timestamps = []

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        feat = MRBBRSIFeatureConfig(
            bb_length=self.config.bb_length,
            bb_std=self.config.bb_std,
            bbp_entry_threshold=self.config.bbp_entry_threshold,
            rsi_length=self.config.rsi_length,
            rsi_entry_threshold=self.config.rsi_entry_threshold,
            use_trend_filter=self.config.use_trend_filter,
            trend_ema_length=self.config.trend_ema_length,
            min_trend_slope=self.config.min_trend_slope,
            atr_length=self.config.atr_length,
            max_atr_pct_for_entry=self.config.max_atr_pct_for_entry,
            volume_filter_window=self.config.volume_filter_window,
            min_volume_quantile=self.config.min_volume_quantile,
            timestamp_mode=self.config.timestamp_mode,
            controller_compat=self.config.controller_compat,
        )
        return compute_mr_bb_rsi_features(candles, feat)

    def build_orders(
        self,
        bar_idx: int,
        signals: SignalOutput,
        engine_config: EngineConfig,
        pair_rules: PairRules,
        inventory: Inventory,
    ) -> Tuple[List[Order], int, int]:
        orders: List[Order] = []

        signal_val = signals.get("signal", bar_idx)
        if np.isnan(signal_val) or signal_val == 0.0:
            return orders, 0, 0

        # Long-only defense — D5
        if signal_val != 1.0:
            return orders, 0, 0

        entry_price = signals.get("close_price", bar_idx)
        if np.isnan(entry_price) or entry_price <= 0:
            return orders, 0, 0

        # D3: rolling 24h placed-order cap
        current_ts = signals.get("timestamp", bar_idx)
        if np.isnan(current_ts):
            return orders, 0, 0
        current_ts_int = int(current_ts)
        cutoff_ts = current_ts_int - 86400
        self._entry_timestamps = [t for t in self._entry_timestamps if t >= cutoff_ts]
        if (
            self.config.max_trades_per_day > 0
            and len(self._entry_timestamps) >= self.config.max_trades_per_day
        ):
            logger.debug(
                "MR: 24h cap bound at bar %d: placed=%d cap=%d",
                bar_idx, len(self._entry_timestamps), self.config.max_trades_per_day,
            )
            return orders, 0, 1

        capital_per_entry = engine_config.total_amount_quote / self.config.max_executors_per_side

        # D13: pre-check quote balance with 99% tolerance
        if inventory.available_quote_for_buy() < capital_per_entry * 0.99:
            return orders, 0, 1

        price = round_price(entry_price, pair_rules)
        if price <= 0:
            return orders, 0, 1
        base_amount = capital_per_entry / price
        base_amount = round_amount(base_amount, pair_rules)
        base_amount, size_reject = check_order_size(base_amount, pair_rules)
        if size_reject:
            return orders, 0, 1
        if not check_min_notional(price, base_amount, pair_rules):
            return orders, 0, 1

        # All gates passed — record placed-order timestamp and enqueue.
        self._entry_timestamps.append(current_ts_int)
        orders.append(Order(
            side="buy",
            price=price,
            quantity=base_amount,
            remaining_quantity=base_amount,
            placed_bar=bar_idx,
            active_bar=bar_idx + engine_config.latency_bars,
            level=0,
        ))
        return orders, 1, 0
