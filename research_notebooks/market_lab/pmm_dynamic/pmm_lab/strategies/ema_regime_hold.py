"""
EMA regime-hold directional strategy.

Wraps `compute_ema_regime_hold_features` in the Strategy protocol. Because
the feature requires two candle arrays (signal timeframe + regime timeframe)
and the engine only hands us one in `compute_signals(candles)`, the regime
candle array must be attached to the strategy config before `compute_signals`
is called. The canonicalizer (Phase 6) is responsible for that wiring.

Design notes:
 - `hold_mode='hold'` raises NotImplementedError at __init__ (D4 —
   defense in depth with canonicalizer).
 - Long-only (D5).
 - D13 inventory pre-check identical to MR.
 - No rolling 24h cap (not part of the EMA controller).
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
from pmm_lab.features.ema_regime_hold_features import (
    EMARegimeHoldFeatureConfig,
    compute_ema_regime_hold_features,
)
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.strategy import SignalOutput

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EMARegimeHoldStrategyConfig:
    """EMA regime-hold strategy parameters.

    Defaults mirror the live controller's Pydantic defaults.

    `_regime_candles` is a *private* field wired up by the canonicalizer.
    It is not typed in the dataclass frontmatter because ndarray isn't a
    dataclass-friendly type; `compare=False` + `repr=False` ensures it
    doesn't interfere with equality/hashing.
    """

    regime_ema_fast: int = 50
    regime_ema_slow: int = 200
    regime_adx_length: int = 14
    regime_adx_threshold: float = 20.0
    volume_filter_window: int = 288
    min_volume_quantile: float = 0.30
    hold_mode: str = "reentry"

    # Execution invariants
    max_executors_per_side: int = 1

    # Mode
    timestamp_mode: str = "open"
    controller_compat: bool = False

    # Private: wired up by the canonicalizer. Using default=None keeps the
    # dataclass frozen semantics intact.
    _regime_candles: Optional[np.ndarray] = field(default=None, compare=False, repr=False)

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
            elif isinstance(val, np.ndarray):
                val = val.tobytes()
            parts.append(val)
        return tuple(parts)

    def __post_init__(self):
        if self.max_executors_per_side != 1:
            raise ValueError(
                f"EMARegimeHoldStrategy requires max_executors_per_side=1; "
                f"got {self.max_executors_per_side}"
            )


class EMARegimeHoldStrategy:
    """EMA regime-hold directional trading strategy."""

    def __init__(self, config: EMARegimeHoldStrategyConfig):
        if config.hold_mode != "reentry":
            raise NotImplementedError(
                "hold_mode='hold' requires a regime-close engine hook that is "
                "out of scope for this MVP (see D4). Only 'reentry' is supported."
            )
        self.config = config

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        if self.config._regime_candles is None:
            raise ValueError(
                "EMARegimeHoldStrategy.compute_signals called without regime_candles "
                "set on the strategy config. The canonicalizer must attach "
                "`_regime_candles` via dataclasses.replace(...) before optimizer "
                "dispatch. See canonicalizer_ema_regime_hold.py."
            )
        feat = EMARegimeHoldFeatureConfig(
            regime_ema_fast=self.config.regime_ema_fast,
            regime_ema_slow=self.config.regime_ema_slow,
            regime_adx_length=self.config.regime_adx_length,
            regime_adx_threshold=self.config.regime_adx_threshold,
            volume_filter_window=self.config.volume_filter_window,
            min_volume_quantile=self.config.min_volume_quantile,
            hold_mode=self.config.hold_mode,
            timestamp_mode=self.config.timestamp_mode,
            controller_compat=self.config.controller_compat,
        )
        return compute_ema_regime_hold_features(candles, self.config._regime_candles, feat)

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
        # Long-only defense
        if signal_val != 1.0:
            return orders, 0, 0

        entry_price = signals.get("close_price", bar_idx)
        if np.isnan(entry_price) or entry_price <= 0:
            return orders, 0, 0

        capital_per_entry = engine_config.total_amount_quote / self.config.max_executors_per_side
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

    def reset_state(self) -> None:
        """No-op — EMA strategy has no instance state to reset."""
        return
