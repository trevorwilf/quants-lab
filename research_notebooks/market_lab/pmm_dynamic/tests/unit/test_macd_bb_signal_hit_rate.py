"""Verify that MACD-BB simulation actually places orders when signals exist."""

import numpy as np
import pytest

from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig
from pmm_lab.sim.generic_runner import GenericSimRunner
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.config.params import PairRules, FeeConfig

from tests.conftest import CANDLE_DTYPE


def _make_candles(n=500):
    """Generate synthetic candles with trends that trigger MACD-BB signals."""
    rng = np.random.default_rng(42)
    candles = np.zeros(n, dtype=CANDLE_DTYPE)
    candles["timestamp"] = np.arange(n) * 300 + 1756833000  # 5m bars

    price = 100.0
    prices = []
    for i in range(n):
        trend = 2.0 * np.sin(2 * np.pi * i / 120)
        noise = rng.normal(0, 0.3)
        price = max(1.0, price + trend + noise)
        prices.append(price)

    prices = np.array(prices)
    candles["close"] = prices
    candles["open"] = np.roll(prices, 1)
    candles["open"][0] = prices[0]
    candles["high"] = np.maximum(candles["open"], candles["close"]) * (1 + rng.uniform(0, 0.005, n))
    candles["low"] = np.minimum(candles["open"], candles["close"]) * (1 - rng.uniform(0, 0.005, n))
    candles["volume"] = rng.uniform(100, 10000, n)
    candles["is_forward_fill"] = False
    return candles


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=1.0,
        min_order_size_base=0.001,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def strategy_config():
    return MACDBBStrategyConfig(
        bb_length=20, bb_std=2.0,
        bb_long_threshold=0.2, bb_short_threshold=0.8,
        macd_fast=12, macd_slow=26, macd_signal=9,
        controller_compat=False,
    )


class TestSignalHitRate:
    def test_orders_placed_with_correct_refresh(self, pair_rules, strategy_config):
        """With executor_refresh_time = bar_interval, strategy should place orders."""
        candles = _make_candles(500)
        engine_cfg = EngineConfig(
            total_amount_quote=1000.0,
            executor_refresh_time=300.0,   # = bar interval -> checks every bar
            cooldown_time=300.0,
            stop_loss=0.05, take_profit=0.05, time_limit=86400,
        )
        strategy = MACDBBStrategy(strategy_config)
        runner = GenericSimRunner(engine_cfg, strategy, pair_rules)
        result = runner.run(candles)

        assert result.n_orders_placed > 0, (
            f"No orders placed! Signals exist but engine missed them. "
            f"Check executor_refresh_time ({engine_cfg.executor_refresh_time}) "
            f"vs bar interval (300)."
        )

    def test_fast_refresh_places_more_than_slow(self, pair_rules, strategy_config):
        """With large executor_refresh_time, most directional signals are missed."""
        candles = _make_candles(500)

        engine_cfg_slow = EngineConfig(
            total_amount_quote=1000.0,
            executor_refresh_time=3120.0,  # default PMM refresh -> misses signals
            cooldown_time=300.0,
            stop_loss=0.05, take_profit=0.05, time_limit=86400,
        )
        engine_cfg_fast = EngineConfig(
            total_amount_quote=1000.0,
            executor_refresh_time=300.0,   # bar interval -> catches signals
            cooldown_time=300.0,
            stop_loss=0.05, take_profit=0.05, time_limit=86400,
        )

        strategy_slow = MACDBBStrategy(strategy_config)
        strategy_fast = MACDBBStrategy(strategy_config)
        runner_slow = GenericSimRunner(engine_cfg_slow, strategy_slow, pair_rules)
        runner_fast = GenericSimRunner(engine_cfg_fast, strategy_fast, pair_rules)

        result_slow = runner_slow.run(candles)
        result_fast = runner_fast.run(candles)

        assert result_fast.n_orders_placed >= result_slow.n_orders_placed, (
            f"Fast refresh ({result_fast.n_orders_placed}) should place >= "
            f"slow refresh ({result_slow.n_orders_placed})"
        )
