"""Engine must not emit per-run 'no orders placed' warnings.

Context: selective strategies (MR, EMA) legitimately produce zero orders
on most bars including the first executable bar after warmup. During a
sweep, engine.run() is called thousands of times; a per-run warning
produces unhelpful log spam. Strategies that never place any order
across a run are surfaced via SimResult.n_orders_placed.

This test documents the contract: the engine module emits ZERO log
records whose message contains 'no orders placed', at ANY level
(DEBUG/INFO/WARNING/ERROR). A demotion to DEBUG would still fail the
test — the contract is absence, not just silence-by-default.
"""

import logging
from typing import List, Tuple

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.strategy import SignalOutput
from tests.conftest import CANDLE_DTYPE


class _NoOpStrategy:
    """Minimal strategy stub that never places orders.

    Matches the interface SimEngine.run() requires: compute_signals()
    returns a valid SignalOutput (mirrors MinimalStrategy in test_engine.py),
    and build_orders() always returns empty.
    """

    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        n = len(candles)
        return SignalOutput(warmup_end=2, data={"dummy": np.ones(n)})

    def build_orders(
        self, bar_idx, signals, engine_config, pair_rules, inventory
    ) -> Tuple[List[Order], int, int]:
        return [], 0, 0


def _make_candles(n: int = 20) -> np.ndarray:
    """Build a minimal candles array of shape (n,) with CANDLE_DTYPE."""
    rows = [
        (1000 + i * 300, 100.0, 100.5, 99.5, 100.0, 1.0, False)
        for i in range(n)
    ]
    return np.array(rows, dtype=CANDLE_DTYPE)


def _default_pair_rules() -> PairRules:
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def test_engine_does_not_emit_no_orders_warning(caplog):
    """Running the engine with a strategy that never places orders must
    produce ZERO log records whose message contains 'no orders placed',
    at ANY level."""
    # Capture every level — a demotion to DEBUG would still fail this test.
    caplog.set_level(logging.DEBUG, logger="pmm_lab.sim.engine")

    engine = SimEngine(EngineConfig(), _default_pair_rules())
    candles = _make_candles()
    result = engine.run(candles, _NoOpStrategy())

    offending = [r for r in caplog.records if "no orders placed" in r.getMessage()]
    assert offending == [], (
        f"engine.py emitted {len(offending)} 'no orders placed' log "
        f"record(s); expected zero. Sample: "
        f"{offending[0].getMessage() if offending else 'N/A'}"
    )

    # Sanity: the run did what we asked — zero orders, no exception.
    assert result.n_orders_placed == 0
