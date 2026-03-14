"""Tests for Strategy protocol."""

import numpy as np
from typing import List, Tuple

from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig

from tests.conftest import CANDLE_DTYPE


class TestPMMDynamicImplementsStrategy:
    """Verify PMMDynamicStrategy satisfies the Strategy protocol."""

    def test_pmm_dynamic_implements_strategy(self):
        strat = PMMDynamicStrategy(PMMDynamicStrategyConfig(
            buy_spreads=(1.0,), sell_spreads=(1.0,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        assert isinstance(strat, Strategy)


class TestStrategyProtocolRequirements:
    """Verify that partial implementations are not Strategy."""

    def test_strategy_protocol_requires_compute_signals(self):
        class MissingComputeSignals:
            def build_orders(self, bar_idx, signals, engine_config, pair_rules, inventory):
                return [], 0, 0

        assert not isinstance(MissingComputeSignals(), Strategy)

    def test_strategy_protocol_requires_build_orders(self):
        class MissingBuildOrders:
            def compute_signals(self, candles):
                return SignalOutput(warmup_end=0)

        assert not isinstance(MissingBuildOrders(), Strategy)


class TestMinimalStrategyImplementation:
    """Verify a trivial strategy runs through SimEngine without error."""

    def test_minimal_strategy_implementation(self):
        class MinimalStrategy:
            def compute_signals(self, candles: np.ndarray) -> SignalOutput:
                n = len(candles)
                return SignalOutput(
                    warmup_end=2,
                    data={"dummy": np.ones(n)},
                )

            def build_orders(
                self, bar_idx, signals, engine_config, pair_rules, inventory
            ) -> Tuple[List[Order], int, int]:
                return [], 0, 0

        # Build a small candle array
        n = 20
        rows = []
        for i in range(n):
            rows.append((1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False))
        candles = np.array(rows, dtype=CANDLE_DTYPE)

        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
        )
        engine = SimEngine(EngineConfig(), rules)
        result = engine.run(candles, MinimalStrategy())

        assert len(result.equity_curve) == n
        assert len(result.position_history) == n
        assert result.n_orders_placed == 0
        assert result.n_orders_filled == 0
        assert result.final_base_balance == 0.0
        assert result.final_quote_balance == 100.0
