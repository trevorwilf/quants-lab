"""Tests for EngineConfig."""

import pytest
from dataclasses import FrozenInstanceError

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import _sim_config_to_engine_config


class TestEngineConfigDefaults:
    """Verify all default values match SimConfig defaults."""

    def test_engine_config_defaults(self):
        ec = EngineConfig()
        sc = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        )
        assert ec.total_amount_quote == sc.total_amount_quote
        assert ec.buy_side_weight == sc.buy_side_weight
        assert ec.executor_refresh_time == sc.executor_refresh_time
        assert ec.cooldown_time == sc.cooldown_time
        assert ec.stop_loss == sc.stop_loss
        assert ec.take_profit == sc.take_profit
        assert ec.time_limit == sc.time_limit
        assert ec.take_profit_order_type == sc.take_profit_order_type
        assert ec.trailing_stop_activation == sc.trailing_stop_activation
        assert ec.trailing_stop_delta == sc.trailing_stop_delta
        assert ec.fill_participation_rate == sc.fill_participation_rate
        assert ec.latency_bars == sc.latency_bars
        assert ec.slippage_bps == sc.slippage_bps


class TestEngineConfigFrozen:
    """Verify EngineConfig is frozen (immutable)."""

    def test_engine_config_frozen(self):
        ec = EngineConfig()
        with pytest.raises(FrozenInstanceError):
            ec.total_amount_quote = 200.0


class TestSimConfigToEngineConfigRoundtrip:
    """Create SimConfig, extract EngineConfig, verify all 13 fields match."""

    def test_sim_config_to_engine_config_roundtrip(self):
        sc = SimConfig(
            buy_spreads=[1.0, 2.0],
            sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5],
            sell_amounts_pct=[0.5, 0.5],
            total_amount_quote=200.0,
            buy_side_weight=0.6,
            executor_refresh_time=1500.0,
            cooldown_time=600.0,
            stop_loss=0.05,
            take_profit=0.02,
            time_limit=86400,
            take_profit_order_type="MARKET",
            trailing_stop_activation=0.01,
            trailing_stop_delta=0.005,
            fill_participation_rate=0.2,
            latency_bars=2,
            slippage_bps=10.0,
        )
        ec = _sim_config_to_engine_config(sc)
        assert ec.total_amount_quote == sc.total_amount_quote
        assert ec.buy_side_weight == sc.buy_side_weight
        assert ec.executor_refresh_time == sc.executor_refresh_time
        assert ec.cooldown_time == sc.cooldown_time
        assert ec.stop_loss == sc.stop_loss
        assert ec.take_profit == sc.take_profit
        assert ec.time_limit == sc.time_limit
        assert ec.take_profit_order_type == sc.take_profit_order_type
        assert ec.trailing_stop_activation == sc.trailing_stop_activation
        assert ec.trailing_stop_delta == sc.trailing_stop_delta
        assert ec.fill_participation_rate == sc.fill_participation_rate
        assert ec.latency_bars == sc.latency_bars
        assert ec.slippage_bps == sc.slippage_bps
