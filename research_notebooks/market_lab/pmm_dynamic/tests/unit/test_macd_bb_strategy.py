"""Tests for MACDBBStrategy."""

import numpy as np
import math
import pytest

from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig

from tests.conftest import CANDLE_DTYPE


def _make_candles(n=300, seed=42):
    """Generate n-bar candle array suitable for MACD+BB."""
    rng = np.random.default_rng(seed=seed)
    start_ts = 1756833000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 100)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 40))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 40))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.1, 3.0)
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def macd_bb_strategy():
    return MACDBBStrategy(MACDBBStrategyConfig(
        bb_length=20, bb_std=2.0,
        bb_long_threshold=0.2,
        bb_short_threshold=0.8,
        macd_fast=12, macd_slow=26, macd_signal=9,
        controller_compat=False,
    ))


@pytest.fixture
def macd_bb_candles():
    return _make_candles(300, seed=42)


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestProtocol:
    def test_implements_strategy(self, macd_bb_strategy):
        assert isinstance(macd_bb_strategy, Strategy)


class TestComputeSignals:
    def test_returns_signal_output(self, macd_bb_candles, macd_bb_strategy):
        result = macd_bb_strategy.compute_signals(macd_bb_candles)
        assert isinstance(result, SignalOutput)

    def test_has_required_keys(self, macd_bb_candles, macd_bb_strategy):
        result = macd_bb_strategy.compute_signals(macd_bb_candles)
        for key in ("bbp", "macd", "macdh", "signal", "close_price"):
            assert key in result.data, f"Missing key: {key}"


class TestBuildOrders:
    def test_buy_on_long_signal(self, macd_bb_candles, macd_bb_strategy, engine_config, pair_rules):
        signals = macd_bb_strategy.compute_signals(macd_bb_candles)
        # Find a bar with long signal
        signal_arr = signals.data["signal"]
        long_bars = np.where(signal_arr == 1.0)[0]
        if len(long_bars) == 0:
            pytest.skip("No long signals in test data")
        bar_idx = int(long_bars[0])
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = macd_bb_strategy.build_orders(
            bar_idx, signals, engine_config, pair_rules, inventory
        )
        assert placed == 1
        assert len(orders) == 1
        assert orders[0].side == "buy"

    def test_sell_on_short_signal(self, macd_bb_candles, macd_bb_strategy, engine_config, pair_rules):
        signals = macd_bb_strategy.compute_signals(macd_bb_candles)
        signal_arr = signals.data["signal"]
        short_bars = np.where(signal_arr == -1.0)[0]
        if len(short_bars) == 0:
            pytest.skip("No short signals in test data")
        bar_idx = int(short_bars[0])
        inventory = Inventory(base_balance=1.0, quote_balance=100.0)
        orders, placed, rejected = macd_bb_strategy.build_orders(
            bar_idx, signals, engine_config, pair_rules, inventory
        )
        assert placed == 1
        assert len(orders) == 1
        assert orders[0].side == "sell"

    def test_no_order_on_neutral(self, macd_bb_candles, macd_bb_strategy, engine_config, pair_rules):
        signals = macd_bb_strategy.compute_signals(macd_bb_candles)
        signal_arr = signals.data["signal"]
        neutral_bars = np.where(signal_arr == 0.0)[0]
        if len(neutral_bars) == 0:
            pytest.skip("No neutral signals")
        bar_idx = int(neutral_bars[0])
        # Must be past warmup
        if bar_idx < signals.warmup_end:
            bar_idx = signals.warmup_end
            while bar_idx < len(signal_arr) and signal_arr[bar_idx] != 0.0:
                bar_idx += 1
            if bar_idx >= len(signal_arr):
                pytest.skip("No neutral bar past warmup")
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = macd_bb_strategy.build_orders(
            bar_idx, signals, engine_config, pair_rules, inventory
        )
        assert placed == 0
        assert len(orders) == 0

    def test_capital_allocation(self, macd_bb_candles, engine_config, pair_rules):
        strategy = MACDBBStrategy(MACDBBStrategyConfig(
            bb_length=20, bb_std=2.0,
            bb_long_threshold=0.2, bb_short_threshold=0.8,
            macd_fast=12, macd_slow=26, macd_signal=9,
            max_executors_per_side=1,
            controller_compat=False,
        ))
        signals = strategy.compute_signals(macd_bb_candles)
        signal_arr = signals.data["signal"]
        long_bars = np.where(signal_arr == 1.0)[0]
        if len(long_bars) == 0:
            pytest.skip("No long signals")
        bar_idx = int(long_bars[0])
        inventory = Inventory(base_balance=0.0, quote_balance=200.0)
        ec = EngineConfig(total_amount_quote=200.0)
        orders, placed, rejected = strategy.build_orders(
            bar_idx, signals, ec, pair_rules, inventory
        )
        if placed > 0:
            notional = orders[0].price * orders[0].quantity
            # Should be close to total_amount_quote / max_executors_per_side = 200
            assert notional <= 200.0 + 1.0  # allow rounding tolerance

    def test_min_notional_rejection(self, macd_bb_candles, pair_rules):
        """Tiny capital should be rejected by min notional check."""
        strategy = MACDBBStrategy(MACDBBStrategyConfig(
            bb_length=20, bb_std=2.0,
            bb_long_threshold=0.2, bb_short_threshold=0.8,
            macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False,
        ))
        signals = strategy.compute_signals(macd_bb_candles)
        signal_arr = signals.data["signal"]
        long_bars = np.where(signal_arr == 1.0)[0]
        if len(long_bars) == 0:
            pytest.skip("No long signals")
        bar_idx = int(long_bars[0])
        # Very small capital
        ec = EngineConfig(total_amount_quote=0.001)
        high_min_rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=10.0,
            fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
        )
        inventory = Inventory(base_balance=0.0, quote_balance=0.001)
        orders, placed, rejected = strategy.build_orders(
            bar_idx, signals, ec, high_min_rules, inventory
        )
        assert placed == 0
        assert rejected == 1
