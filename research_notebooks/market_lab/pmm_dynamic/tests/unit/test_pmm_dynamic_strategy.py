"""Tests for PMMDynamicStrategy."""

import numpy as np
import math
import pytest

from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def default_engine_config():
    return EngineConfig(total_amount_quote=100.0)


@pytest.fixture
def strategy_with_spreads():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


class TestFromSimConfig:
    """Create from SimConfig, verify all fields transferred."""

    def test_from_sim_config(self):
        sc = SimConfig(
            buy_spreads=[1.0, 2.0, 4.0],
            sell_spreads=[1.5, 3.0],
            buy_amounts_pct=[0.3, 0.3, 0.4],
            sell_amounts_pct=[0.6, 0.4],
            macd_fast=15,
            macd_slow=30,
            macd_signal=7,
            natr_length=20,
            timestamp_mode="close",
        )
        strat = PMMDynamicStrategy.from_sim_config(sc)
        assert strat.config.macd_fast == 15
        assert strat.config.macd_slow == 30
        assert strat.config.macd_signal == 7
        assert strat.config.natr_length == 20
        assert strat.config.timestamp_mode == "close"
        assert strat.config.buy_spreads == (1.0, 2.0, 4.0)
        assert strat.config.sell_spreads == (1.5, 3.0)
        assert strat.config.buy_amounts_pct == (0.3, 0.3, 0.4)
        assert strat.config.sell_amounts_pct == (0.6, 0.4)


class TestComputeSignals:
    """Test compute_signals method."""

    def test_compute_signals_returns_signal_output(self, sample_candles_5m, strategy_with_spreads):
        result = strategy_with_spreads.compute_signals(sample_candles_5m)
        assert isinstance(result, SignalOutput)

    def test_compute_signals_warmup_end(self, sample_candles_5m, strategy_with_spreads):
        result = strategy_with_spreads.compute_signals(sample_candles_5m)
        # Default: macd_slow=42, natr=14, macd_signal=9 -> warmup = 42+9+1 = 52
        # With "open" mode: +1 -> 53
        assert result.warmup_end == 53

    def test_compute_signals_has_reference_price(self, sample_candles_5m, strategy_with_spreads):
        result = strategy_with_spreads.compute_signals(sample_candles_5m)
        assert "reference_price" in result.data
        assert len(result.data["reference_price"]) == len(sample_candles_5m)

    def test_compute_signals_has_spread_multiplier(self, sample_candles_5m, strategy_with_spreads):
        result = strategy_with_spreads.compute_signals(sample_candles_5m)
        assert "spread_multiplier" in result.data
        assert len(result.data["spread_multiplier"]) == len(sample_candles_5m)


class TestBuildOrders:
    """Test build_orders method."""

    def test_build_orders_returns_tuple(
        self, sample_candles_5m, strategy_with_spreads,
        default_engine_config, default_pair_rules
    ):
        signals = strategy_with_spreads.compute_signals(sample_candles_5m)
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        result = strategy_with_spreads.build_orders(
            signals.warmup_end, signals, default_engine_config, default_pair_rules, inventory
        )
        assert isinstance(result, tuple)
        assert len(result) == 3
        orders, placed, rejected = result
        assert isinstance(orders, list)
        assert isinstance(placed, int)
        assert isinstance(rejected, int)

    def test_build_orders_buy_and_sell(
        self, sample_candles_5m, strategy_with_spreads,
        default_engine_config, default_pair_rules
    ):
        signals = strategy_with_spreads.compute_signals(sample_candles_5m)
        # Start with some base so sell orders can be placed
        inventory = Inventory(base_balance=0.001, quote_balance=100.0)
        orders, placed, rejected = strategy_with_spreads.build_orders(
            signals.warmup_end, signals, default_engine_config, default_pair_rules, inventory
        )
        buy_orders = [o for o in orders if o.side == "buy"]
        sell_orders = [o for o in orders if o.side == "sell"]
        assert len(buy_orders) > 0
        # Sell orders may or may not be placed depending on available base
        assert placed > 0

    def test_build_orders_spot_constraint(
        self, sample_candles_5m, strategy_with_spreads,
        default_engine_config, default_pair_rules
    ):
        signals = strategy_with_spreads.compute_signals(sample_candles_5m)
        # No base balance -> sell orders should be rejected
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = strategy_with_spreads.build_orders(
            signals.warmup_end, signals, default_engine_config, default_pair_rules, inventory
        )
        sell_orders = [o for o in orders if o.side == "sell"]
        assert len(sell_orders) == 0

    def test_build_orders_nan_signals_returns_empty(
        self, default_engine_config, default_pair_rules
    ):
        # Create signals with NaN at bar 0
        signals = SignalOutput(
            warmup_end=0,
            data={
                "reference_price": np.array([np.nan, 100.0]),
                "spread_multiplier": np.array([np.nan, 0.01]),
            },
        )
        strat = PMMDynamicStrategy(PMMDynamicStrategyConfig(
            buy_spreads=(1.0,), sell_spreads=(1.0,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = strat.build_orders(
            0, signals, default_engine_config, default_pair_rules, inventory
        )
        assert orders == []
        assert placed == 0
        assert rejected == 0
