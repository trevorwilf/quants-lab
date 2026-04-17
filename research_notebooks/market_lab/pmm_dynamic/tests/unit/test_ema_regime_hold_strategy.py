"""Tests for EMARegimeHoldStrategy."""

from dataclasses import replace

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.strategy import Strategy
from pmm_lab.strategies.ema_regime_hold import (
    EMARegimeHoldStrategy,
    EMARegimeHoldStrategyConfig,
)
from tests.conftest import CANDLE_DTYPE


def _make_fast(n=800, seed=31):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.4)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.15))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.15))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_slow(n=100, seed=37):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 1.2)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.6))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.6))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 8.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def fast():
    return _make_fast()


@pytest.fixture
def slow():
    return _make_slow()


@pytest.fixture
def config(slow):
    base = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10,
        regime_ema_slow=20,
        regime_adx_length=14,
        regime_adx_threshold=0.0,
        volume_filter_window=48,
        min_volume_quantile=0.0,
        hold_mode="reentry",
    )
    return replace(base, _regime_candles=slow)


@pytest.fixture
def strategy(config):
    return EMARegimeHoldStrategy(config)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0)


class TestProtocol:
    def test_implements_strategy(self, strategy):
        assert isinstance(strategy, Strategy)


class TestHoldMode:
    def test_rejects_hold_mode_at_init(self):
        bad = EMARegimeHoldStrategyConfig(hold_mode="hold")
        with pytest.raises(NotImplementedError):
            EMARegimeHoldStrategy(bad)


class TestUnwiredRegime:
    def test_missing_regime_candles_raises(self):
        base = EMARegimeHoldStrategyConfig()
        strat = EMARegimeHoldStrategy(base)  # _regime_candles=None by default
        fake_candles = _make_fast(n=50)
        with pytest.raises(ValueError, match="regime_candles"):
            strat.compute_signals(fake_candles)


class TestComputeSignals:
    def test_returns_signal_output(self, strategy, fast):
        out = strategy.compute_signals(fast)
        for key in ("signal", "trend_on", "vol_ok", "close_price", "timestamp"):
            assert key in out.data


class TestBuildOrders:
    def test_buy_on_entry_signal(self, strategy, fast, engine_config, pair_rules):
        signals = strategy.compute_signals(fast)
        entry_bars = np.where(signals.data["signal"] == 1.0)[0]
        if len(entry_bars) == 0:
            pytest.skip("No entry signals")
        bar_idx = int(entry_bars[0])
        inv = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, _ = strategy.build_orders(
            bar_idx, signals, engine_config, pair_rules, inv
        )
        assert placed == 1
        assert orders[0].side == "buy"

    def test_no_order_on_zero_signal(self, strategy, fast, engine_config, pair_rules):
        signals = strategy.compute_signals(fast)
        zeros = np.where(signals.data["signal"] == 0.0)[0]
        zeros_past = zeros[zeros >= signals.warmup_end]
        if len(zeros_past) == 0:
            pytest.skip("No zero bars past warmup")
        inv = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, _ = strategy.build_orders(
            int(zeros_past[0]), signals, engine_config, pair_rules, inv
        )
        assert placed == 0

    def test_insufficient_quote_rejects_via_d13(self, strategy, fast, engine_config, pair_rules):
        signals = strategy.compute_signals(fast)
        entry_bars = np.where(signals.data["signal"] == 1.0)[0]
        if len(entry_bars) == 0:
            pytest.skip("No entry signals")
        inv = Inventory(base_balance=0.0, quote_balance=1.0)
        _, placed, rejected = strategy.build_orders(
            int(entry_bars[0]), signals, engine_config, pair_rules, inv
        )
        assert placed == 0
        assert rejected == 1

    def test_min_notional_rejection(self, strategy, fast):
        signals = strategy.compute_signals(fast)
        entry_bars = np.where(signals.data["signal"] == 1.0)[0]
        if len(entry_bars) == 0:
            pytest.skip("No entry signals")
        high = PairRules(
            price_tick=0.01, amount_step=0.001, min_notional_quote=10_000.0,
            fees=FeeConfig(0.001, 0.002),
        )
        small_ec = EngineConfig(total_amount_quote=5.0)
        inv = Inventory(base_balance=0.0, quote_balance=5.0)
        _, placed, rejected = strategy.build_orders(
            int(entry_bars[0]), signals, small_ec, high, inv
        )
        assert placed == 0
        assert rejected == 1
