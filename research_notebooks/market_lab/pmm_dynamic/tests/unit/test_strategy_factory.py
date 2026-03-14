"""Tests for strategy factory."""

import pytest

from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.strategies.factory import create_strategy, available_strategies, register_strategy
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig


class TestAvailableStrategies:
    def test_available_strategies_includes_builtins(self):
        avail = available_strategies()
        assert "pmm_dynamic" in avail
        assert "bollinger" in avail


class TestCreateStrategy:
    def test_create_pmm_dynamic(self):
        strat = create_strategy("pmm_dynamic", PMMDynamicStrategyConfig(
            buy_spreads=(1.0,), sell_spreads=(1.0,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        assert isinstance(strat, PMMDynamicStrategy)

    def test_create_bollinger(self):
        strat = create_strategy("bollinger", BollingerStrategyConfig(
            buy_spreads=(0.5,), sell_spreads=(0.5,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        assert isinstance(strat, BollingerStrategy)


class TestUnknownStrategy:
    def test_unknown_strategy_raises_key_error(self):
        with pytest.raises(KeyError, match="nonexistent"):
            create_strategy("nonexistent", {})


class TestRegisterCustom:
    def test_register_custom_strategy(self):
        import numpy as np

        class DummyConfig:
            pass

        class DummyStrategy:
            def __init__(self, config):
                self.config = config

            def compute_signals(self, candles):
                return SignalOutput(warmup_end=0)

            def build_orders(self, bar_idx, signals, engine_config, pair_rules, inventory):
                return [], 0, 0

        register_strategy("dummy_test", DummyStrategy)
        assert "dummy_test" in available_strategies()

        strat = create_strategy("dummy_test", DummyConfig())
        assert isinstance(strat, DummyStrategy)


class TestCreatedStrategiesImplementProtocol:
    def test_created_strategies_implement_protocol(self):
        pmm = create_strategy("pmm_dynamic", PMMDynamicStrategyConfig(
            buy_spreads=(1.0,), sell_spreads=(1.0,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        boll = create_strategy("bollinger", BollingerStrategyConfig(
            buy_spreads=(0.5,), sell_spreads=(0.5,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        assert isinstance(pmm, Strategy)
        assert isinstance(boll, Strategy)
