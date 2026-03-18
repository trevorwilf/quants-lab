"""
PMM Dynamic strategy implementation.

Implements the Strategy protocol for the PMM Dynamic market-making controller.
Signal computation (NATR, MACD z-score) and order ladder construction are
strategy-specific. Everything else (fills, barriers, inventory) is handled
by SimEngine.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules
from pmm_lab.features.pmm_dynamic_features import (
    PMMDynamicConfig, compute_pmm_dynamic_features
)
from pmm_lab.features.alignment import align_features
from pmm_lab.config.exchange_rules import round_price, round_price_up, round_amount, check_min_notional, check_order_size


@dataclass(frozen=True)
class PMMDynamicStrategyConfig:
    """PMM Dynamic strategy-specific parameters."""
    # Indicator config
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9
    natr_length: int = 14
    controller_compat: bool = True  # Match live controller sliding-window behavior
    timestamp_mode: str = "open"

    # Spread ladders (in NATR multiplier units)
    buy_spreads: tuple = ()        # e.g., (1.0, 2.0, 4.0)
    sell_spreads: tuple = ()       # e.g., (1.0, 2.0, 4.0)
    buy_amounts_pct: tuple = ()    # per-level percentage of buy-side capital
    sell_amounts_pct: tuple = ()   # per-level percentage of sell-side capital


class PMMDynamicStrategy:
    """PMM Dynamic market-making strategy.

    Implements the Strategy protocol:
    - compute_signals: NATR + MACD z-score -> reference_price, spread_multiplier
    - build_orders: spread ladder from reference_price +/- spread * spread_multiplier
    """

    def __init__(self, config: PMMDynamicStrategyConfig):
        self.config = config

    @classmethod
    def from_sim_config(cls, sim_config) -> 'PMMDynamicStrategy':
        """Create from a legacy SimConfig for backward compatibility."""
        controller_compat = sim_config.controller_compat
        return cls(PMMDynamicStrategyConfig(
            macd_fast=sim_config.macd_fast,
            macd_slow=sim_config.macd_slow,
            macd_signal=sim_config.macd_signal,
            natr_length=sim_config.natr_length,
            controller_compat=controller_compat,
            timestamp_mode=sim_config.timestamp_mode,
            buy_spreads=tuple(sim_config.buy_spreads),
            sell_spreads=tuple(sim_config.sell_spreads),
            buy_amounts_pct=tuple(sim_config.buy_amounts_pct),
            sell_amounts_pct=tuple(sim_config.sell_amounts_pct),
        ))

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Compute PMM Dynamic signals: reference_price and spread_multiplier."""
        feat_config = PMMDynamicConfig(
            macd_fast=self.config.macd_fast,
            macd_slow=self.config.macd_slow,
            macd_signal=self.config.macd_signal,
            natr_length=self.config.natr_length,
            controller_compat=self.config.controller_compat,
        )
        raw_features = compute_pmm_dynamic_features(candles, feat_config)
        features = align_features(raw_features, timestamp_mode=self.config.timestamp_mode)

        return SignalOutput(
            warmup_end=features.warmup_end,
            data={
                "reference_price": features.reference_price,
                "spread_multiplier": features.spread_multiplier,
                "natr": features.natr,
                "macd_signal_z": features.macd_signal_z,
            },
        )

    def build_orders(
        self,
        bar_idx: int,
        signals: SignalOutput,
        engine_config: EngineConfig,
        pair_rules: PairRules,
        inventory: Inventory,
    ) -> Tuple[List[Order], int, int]:
        """Build buy and sell order ladders using PMM Dynamic spread formula.

        This is the EXACT same logic as v1 CandleSimRunner._build_order_ladder(),
        extracted into the strategy.
        """
        cfg = engine_config
        scfg = self.config
        rules = pair_rules
        orders: List[Order] = []
        n_placed = 0
        n_rejected = 0

        reference_price = signals.get("reference_price", bar_idx)
        spread_multiplier = signals.get("spread_multiplier", bar_idx)

        if np.isnan(reference_price) or np.isnan(spread_multiplier):
            return orders, n_placed, n_rejected

        # Capital allocation — use current available balances
        available_quote = inventory.available_quote_for_buy()
        buy_capital = min(cfg.buy_side_weight * cfg.total_amount_quote, available_quote)
        sell_capital = (1.0 - cfg.buy_side_weight) * cfg.total_amount_quote

        # Buy side
        for i, spread in enumerate(scfg.buy_spreads):
            price = reference_price * (1.0 - spread * spread_multiplier)
            price = round_price(price, rules)
            if price <= 0:
                n_rejected += 1
                continue

            amount_pct = scfg.buy_amounts_pct[i] if i < len(scfg.buy_amounts_pct) else 0.0
            quote_amount = buy_capital * amount_pct
            base_amount = quote_amount / price if price > 0 else 0.0
            base_amount = round_amount(base_amount, rules)

            base_amount, size_reject = check_order_size(base_amount, rules)
            if size_reject:
                n_rejected += 1
                continue

            if not check_min_notional(price, base_amount, rules):
                n_rejected += 1
                continue

            orders.append(Order(
                side="buy",
                price=price,
                quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx,
                active_bar=bar_idx + cfg.latency_bars,
                level=i,
            ))
            n_placed += 1

        # Sell side
        for i, spread in enumerate(scfg.sell_spreads):
            price = reference_price * (1.0 + spread * spread_multiplier)
            price = round_price_up(price, rules)
            if price <= 0:
                n_rejected += 1
                continue

            amount_pct = scfg.sell_amounts_pct[i] if i < len(scfg.sell_amounts_pct) else 0.0
            quote_amount = sell_capital * amount_pct
            base_amount = quote_amount / price if price > 0 else 0.0
            base_amount = round_amount(base_amount, rules)

            # Clamp to available base (spot constraint)
            if inventory.enforce_spot_constraints:
                available = inventory.available_base_for_sell()
                if base_amount > available:
                    base_amount = round_amount(available, rules)
                    if base_amount <= 0 or not check_min_notional(price, base_amount, rules):
                        n_rejected += 1
                        continue

            base_amount, size_reject = check_order_size(base_amount, rules)
            if size_reject:
                n_rejected += 1
                continue

            if not check_min_notional(price, base_amount, rules):
                n_rejected += 1
                continue

            orders.append(Order(
                side="sell",
                price=price,
                quantity=base_amount,
                remaining_quantity=base_amount,
                placed_bar=bar_idx,
                active_bar=bar_idx + cfg.latency_bars,
                level=i,
            ))
            n_placed += 1

        return orders, n_placed, n_rejected
