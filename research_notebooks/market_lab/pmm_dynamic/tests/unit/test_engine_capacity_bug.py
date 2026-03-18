"""Regression test for shared-capacity decrement bug.

The engine must decrement bar capacity by the ACTUALLY EXECUTED quantity,
not the originally requested fill quantity. When spot constraints reduce
the fill (e.g., not enough base to sell), the unused capacity must remain
available for subsequent orders on the same bar.
"""

import numpy as np
import pytest
from collections import defaultdict

from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.config.params import PairRules, FeeConfig

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n_bars, price=100.0, volume=10.0):
    """Create synthetic candle data."""
    rows = []
    for i in range(n_bars):
        rows.append((
            i * 300,
            price,
            price * 1.01,
            price * 0.99,
            price,
            volume,
            False,
        ))
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=0.0,
        fees=FeeConfig(maker_fee=0.0, taker_fee=0.0),
    )


class TestSharedCapacityDecrement:
    """Verify capacity is decremented by executed qty, not requested qty."""

    def test_sell_clamp_does_not_overconsume_capacity(self, default_pair_rules):
        """When sell is clamped by base inventory, capacity should reflect actual fill."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[0.5, 0.5],
            total_amount_quote=100.0,
            buy_side_weight=0.333,
            fill_participation_rate=1.0,
            latency_bars=0,
            controller_compat=False,
        )

        candles = _make_candles(100, price=100.0, volume=100.0)
        runner = CandleSimRunner(config, default_pair_rules)
        result = runner.run(candles)

        sell_trades = [t for t in result.trades if t.side == "sell"]
        buy_trades = [t for t in result.trades if t.side == "buy"]

        # With the bug fixed, buy orders should not be starved by
        # sell orders over-consuming capacity
        if len(sell_trades) > 0:
            assert len(buy_trades) > 0, (
                "Buy orders were completely starved — likely the capacity "
                "decrement bug is present"
            )

    def test_capacity_invariant_holds(self, default_pair_rules):
        """Total executed quantity per bar must not exceed bar capacity."""
        config = SimConfig(
            buy_spreads=[0.5, 1.0, 2.0],
            sell_spreads=[0.5, 1.0, 2.0],
            buy_amounts_pct=[0.33, 0.33, 0.34],
            sell_amounts_pct=[0.33, 0.33, 0.34],
            total_amount_quote=50.0,
            fill_participation_rate=0.1,
            latency_bars=0,
            controller_compat=False,
        )

        pair_rules = PairRules(
            price_tick=0.01,
            amount_step=0.001,
            min_notional_quote=0.0,
            fees=FeeConfig(maker_fee=0.001, taker_fee=0.001),
        )

        candles = _make_candles(100, price=100.0, volume=50.0)
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(candles)

        # Group trades by entry bar
        bar_fills = defaultdict(float)
        for t in result.trades:
            bar_fills[t.entry_bar] += t.quantity

        max_capacity = 0.1 * 50.0  # fill_participation_rate * volume
        for bar_idx, total_qty in bar_fills.items():
            assert total_qty <= max_capacity + 1e-9, (
                f"Bar {bar_idx}: total executed qty {total_qty} "
                f"exceeds capacity {max_capacity}"
            )
