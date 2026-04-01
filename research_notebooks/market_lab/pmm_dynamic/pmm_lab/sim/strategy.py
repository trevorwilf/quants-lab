"""
Strategy protocol for the generic simulation engine.

Any trading strategy must implement this protocol to be runnable
by SimEngine. The engine handles fills, barriers, inventory, and equity.
The strategy handles signals, order construction, and warmup.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Protocol, runtime_checkable

from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules


@dataclass
class SignalOutput:
    """Output from Strategy.compute_signals().

    Contains:
    - warmup_end: first bar index where all signals are valid
    - data: dict of strategy-specific signal arrays, each length == n_candles
    """
    warmup_end: int
    data: Dict[str, np.ndarray] = field(default_factory=dict)

    def get(self, key: str, bar_idx: int) -> float:
        """Get a signal value at a specific bar. Returns NaN if unavailable."""
        arr = self.data.get(key)
        if arr is None or bar_idx >= len(arr):
            return float('nan')
        return float(arr[bar_idx])

    def is_valid(self, bar_idx: int) -> bool:
        """Check if signals are valid (past warmup) at this bar."""
        return bar_idx >= self.warmup_end

    def slice(self, start_idx: int, end_idx: int | None = None) -> "SignalOutput":
        """Return a view of the signal arrays for ``[start_idx:end_idx]``.

        The returned ``warmup_end`` is shifted into the sliced coordinate
        system, so ``is_valid()`` preserves the same absolute validity window
        as the parent signals.
        """
        if start_idx < 0:
            raise ValueError(f"start_idx must be >= 0, got {start_idx}")
        if end_idx is not None and end_idx < start_idx:
            raise ValueError(
                f"end_idx must be >= start_idx, got start_idx={start_idx}, end_idx={end_idx}"
            )

        sliced = {
            key: arr[start_idx:end_idx]
            for key, arr in self.data.items()
        }
        new_warmup_end = max(0, self.warmup_end - start_idx)
        return SignalOutput(warmup_end=new_warmup_end, data=sliced)


@runtime_checkable
class Strategy(Protocol):
    """Protocol that all trading strategies must implement.

    The engine calls:
    1. compute_signals(candles) once at the start -> SignalOutput
    2. build_orders(...) at each refresh -> list of Order objects

    The engine handles everything else: fills, barriers, inventory,
    equity tracking, and position management.
    """

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        """Compute all strategy signals from candle data.

        Must be causal: signal at bar t depends only on candles[0:t+1].

        Parameters
        ----------
        candles : np.ndarray
            Canonical structured candle array.

        Returns
        -------
        SignalOutput
            Signal arrays and warmup index.
        """
        ...

    def build_orders(
        self,
        bar_idx: int,
        signals: SignalOutput,
        engine_config: EngineConfig,
        pair_rules: PairRules,
        inventory: Inventory,
    ) -> Tuple[List[Order], int, int]:
        """Build orders for a single bar.

        Called by the engine when a refresh is triggered.

        Parameters
        ----------
        bar_idx : int
            Current bar index.
        signals : SignalOutput
            Pre-computed signals (from compute_signals).
        engine_config : EngineConfig
            Generic execution configuration.
        pair_rules : PairRules
            Exchange rules for rounding and min-notional.
        inventory : Inventory
            Current inventory state.

        Returns
        -------
        Tuple[List[Order], int placed, int rejected]
        """
        ...
