"""
MACD+BB directional trading strategy implementation.

Implements the Strategy protocol for the Hummingbot macd_bb_v1 controller.
Signal computation (BBands, MACD) and directional order placement are
strategy-specific. Everything else (fills, barriers, inventory) is handled
by SimEngine.

MVP: max_executors_per_side = 1 (single entry per signal direction).
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules
from pmm_lab.features.macd_bb_features import (
    MACDBBFeatureConfig,
    compute_macd_bb_features,
)
from pmm_lab.config.exchange_rules import round_price, round_amount, check_min_notional, check_order_size


@dataclass(frozen=True)
class MACDBBStrategyConfig:
    """MACD+BB strategy-specific parameters."""
    # Indicator config
    bb_length: int = 100
    bb_std: float = 2.0
    bb_long_threshold: float = 0.0
    bb_short_threshold: float = 1.0
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9

    # Execution
    max_executors_per_side: int = 1  # MVP: fixed at 1

    # Mode
    timestamp_mode: str = "open"
    controller_compat: bool = True


class MACDBBStrategy:
    """MACD+BB directional trading strategy.

    Implements the Strategy protocol:
    - compute_signals: BBands + MACD -> directional signal (+1, -1, 0)
    - build_orders: single entry order when signal fires

    MVP constraint: max_executors_per_side = 1. The engine's existing
    cooldown + triple-barrier handles position lifecycle.
    """

    def __init__(self, config: MACDBBStrategyConfig):
        self.config = config

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Compute MACD+BB signals: bbp, macd, macdh, signal."""
        feat_config = MACDBBFeatureConfig(
            bb_length=self.config.bb_length,
            bb_std=self.config.bb_std,
            bb_long_threshold=self.config.bb_long_threshold,
            bb_short_threshold=self.config.bb_short_threshold,
            macd_fast=self.config.macd_fast,
            macd_slow=self.config.macd_slow,
            macd_signal=self.config.macd_signal,
            timestamp_mode=self.config.timestamp_mode,
            controller_compat=self.config.controller_compat,
        )
        return compute_macd_bb_features(candles, feat_config)

    def build_orders(
        self,
        bar_idx: int,
        signals: SignalOutput,
        engine_config: EngineConfig,
        pair_rules: PairRules,
        inventory: Inventory,
    ) -> Tuple[List[Order], int, int]:
        """Build a single directional order based on signal.

        Signal +1 -> BUY order at close price (market-equivalent entry)
        Signal -1 -> SELL order at close price
        Signal  0 -> no order

        Capital per entry: total_amount_quote / max_executors_per_side
        """
        orders: List[Order] = []
        n_placed = 0
        n_rejected = 0

        signal_val = signals.get("signal", bar_idx)
        if np.isnan(signal_val) or signal_val == 0.0:
            return orders, n_placed, n_rejected

        # Use close price from signals as entry (market-equivalent)
        entry_price = signals.get("close_price", bar_idx)
        if np.isnan(entry_price) or entry_price <= 0:
            return orders, n_placed, n_rejected

        # Capital per entry
        capital_per_entry = engine_config.total_amount_quote / self.config.max_executors_per_side

        if signal_val == 1.0:
            # Long: place BUY order
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
            orders.append(Order(
                side="buy",
                price=price,
                quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx,
                active_bar=bar_idx + engine_config.latency_bars,
                level=0,
            ))
            n_placed = 1

        elif signal_val == -1.0:
            # Short: place SELL order
            price = round_price(entry_price, pair_rules)
            if price <= 0:
                return orders, 0, 1
            base_amount = capital_per_entry / price
            base_amount = round_amount(base_amount, pair_rules)

            # Spot constraint: clamp to available base
            if inventory.enforce_spot_constraints:
                available = inventory.available_base_for_sell()
                if base_amount > available:
                    base_amount = round_amount(available, pair_rules)
                    if base_amount <= 0 or not check_min_notional(price, base_amount, pair_rules):
                        return orders, 0, 1

            base_amount, size_reject = check_order_size(base_amount, pair_rules)
            if size_reject:
                return orders, 0, 1
            if not check_min_notional(price, base_amount, pair_rules):
                return orders, 0, 1
            orders.append(Order(
                side="sell",
                price=price,
                quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx,
                active_bar=bar_idx + engine_config.latency_bars,
                level=0,
            ))
            n_placed = 1

        return orders, n_placed, n_rejected
