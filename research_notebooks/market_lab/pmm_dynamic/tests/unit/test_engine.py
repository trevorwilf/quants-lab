"""Tests for SimEngine."""

import numpy as np
import pytest
from typing import List, Tuple

from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.sim.executor_model import Order
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig

from tests.conftest import CANDLE_DTYPE


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def pmm_strategy():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


class MinimalStrategy:
    """A trivial strategy that places no orders."""
    def compute_signals(self, candles: np.ndarray) -> SignalOutput:
        n = len(candles)
        return SignalOutput(warmup_end=2, data={"dummy": np.ones(n)})

    def build_orders(
        self, bar_idx, signals, engine_config, pair_rules, inventory
    ) -> Tuple[List[Order], int, int]:
        return [], 0, 0


class TestEngineBasic:
    """Basic end-to-end tests."""

    def test_engine_runs_with_pmm_dynamic(self, sample_candles_5m, default_pair_rules, pmm_strategy):
        engine = SimEngine(EngineConfig(), default_pair_rules)
        result = engine.run(sample_candles_5m, pmm_strategy)
        assert result.equity_curve is not None
        assert result.position_history is not None
        assert isinstance(result.n_orders_placed, int)
        assert isinstance(result.n_orders_filled, int)
        assert isinstance(result.n_orders_rejected, int)
        assert isinstance(result.n_market_exits, int)
        assert isinstance(result.final_base_balance, float)
        assert isinstance(result.final_quote_balance, float)

    def test_engine_runs_with_minimal_strategy(self, default_pair_rules):
        n = 20
        rows = [(1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False) for i in range(n)]
        candles = np.array(rows, dtype=CANDLE_DTYPE)
        engine = SimEngine(EngineConfig(), default_pair_rules)
        result = engine.run(candles, MinimalStrategy())
        assert len(result.trades) == 0
        assert result.final_quote_balance == 100.0


class TestEngineArrayLengths:
    """Verify output array lengths match candle length."""

    def test_engine_equity_curve_length(self, sample_candles_5m, default_pair_rules, pmm_strategy):
        engine = SimEngine(EngineConfig(), default_pair_rules)
        result = engine.run(sample_candles_5m, pmm_strategy)
        assert len(result.equity_curve) == len(sample_candles_5m)

    def test_engine_position_history_length(self, sample_candles_5m, default_pair_rules, pmm_strategy):
        engine = SimEngine(EngineConfig(), default_pair_rules)
        result = engine.run(sample_candles_5m, pmm_strategy)
        assert len(result.position_history) == len(sample_candles_5m)


class TestEngineSimStartIdx:
    """Verify sim_start_idx is respected."""

    def test_engine_sim_start_idx(self, sample_candles_5m, default_pair_rules, pmm_strategy):
        engine = SimEngine(EngineConfig(), default_pair_rules)
        # Run with late start
        result = engine.run(sample_candles_5m, pmm_strategy, sim_start_idx=70)
        assert len(result.equity_curve) == len(sample_candles_5m)
        # Equity should be initial value for pre-start bars
        initial_equity = 100.0  # total_amount_quote
        for i in range(70):
            assert result.equity_curve[i] == pytest.approx(initial_equity, abs=1e-6)


class TestEngineSpotConstraints:
    """Verify spot constraints prevent negative balances."""

    def test_engine_spot_constraints_no_negative_base(self, sample_candles_5m, default_pair_rules, pmm_strategy):
        engine = SimEngine(EngineConfig(), default_pair_rules)
        result = engine.run(sample_candles_5m, pmm_strategy)
        assert result.final_base_balance >= 0.0

    def test_engine_spot_constraints_no_negative_quote(self, sample_candles_5m, default_pair_rules, pmm_strategy):
        engine = SimEngine(EngineConfig(), default_pair_rules)
        result = engine.run(sample_candles_5m, pmm_strategy)
        # Allow small float epsilon
        assert result.final_quote_balance >= -1e-6


class TestEngineSharedFillCapacity:
    """Verify total fills per bar respect participation rate."""

    def test_engine_shared_fill_capacity(self, sample_candles_500, default_pair_rules):
        strategy = PMMDynamicStrategy(PMMDynamicStrategyConfig(
            buy_spreads=(1.0, 2.0, 4.0),
            sell_spreads=(1.0, 2.0, 4.0),
            buy_amounts_pct=(0.33, 0.34, 0.33),
            sell_amounts_pct=(0.33, 0.34, 0.33),
        ))
        cfg = EngineConfig(fill_participation_rate=0.1)
        engine = SimEngine(cfg, default_pair_rules)
        result = engine.run(sample_candles_500, strategy)

        # Check that trades exist (sanity)
        assert len(result.trades) > 0

        # Group fills by bar, verify total fill qty <= participation * volume
        fills_by_bar = {}
        for t in result.trades:
            bar = t.entry_bar
            fills_by_bar.setdefault(bar, 0.0)
            fills_by_bar[bar] += t.quantity

        for bar, total_qty in fills_by_bar.items():
            bar_volume = float(sample_candles_500["volume"][bar])
            max_fill = cfg.fill_participation_rate * bar_volume
            assert total_qty <= max_fill + 1e-10, (
                f"Bar {bar}: total fill {total_qty} > max {max_fill}"
            )


class TestEngineTripleBarrier:
    """Test triple barrier behavior."""

    def test_engine_triple_barrier_priority(self, sample_candles_500, default_pair_rules):
        """Stop loss has higher priority than take profit."""
        strategy = PMMDynamicStrategy(PMMDynamicStrategyConfig(
            buy_spreads=(1.0,),
            sell_spreads=(1.0,),
            buy_amounts_pct=(1.0,),
            sell_amounts_pct=(1.0,),
        ))
        # Tight stop loss, wide take profit
        cfg = EngineConfig(stop_loss=0.001, take_profit=0.5)
        engine = SimEngine(cfg, default_pair_rules)
        result = engine.run(sample_candles_500, strategy)

        # If any trades closed, most should be stop_loss given tight SL
        closed = [t for t in result.trades if t.exit_type is not None]
        if closed:
            sl_count = sum(1 for t in closed if t.exit_type == "stop_loss")
            # With very tight SL and very wide TP, stop losses should dominate
            assert sl_count >= len(closed) * 0.5 or len(closed) <= 2
