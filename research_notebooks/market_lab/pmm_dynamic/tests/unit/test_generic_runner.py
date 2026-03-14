"""Tests for GenericSimRunner."""

import pytest

from pmm_lab.sim.generic_runner import GenericSimRunner
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig


@pytest.fixture
def pmm_strategy():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


@pytest.fixture
def bollinger_strategy():
    return BollingerStrategy(BollingerStrategyConfig(
        bb_window=20,
        bb_stdev=2.0,
        buy_spreads=(0.3, 0.6),
        sell_spreads=(0.3, 0.6),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0)


class TestGenericRunnerWithPMMDynamic:
    def test_generic_runner_with_pmm_dynamic(
        self, sample_candles_5m, default_pair_rules, pmm_strategy, engine_config
    ):
        runner = GenericSimRunner(engine_config, pmm_strategy, default_pair_rules)
        result = runner.run(sample_candles_5m)
        assert result.equity_curve is not None
        assert result.position_history is not None
        assert isinstance(result.n_orders_placed, int)
        assert isinstance(result.final_base_balance, float)
        assert isinstance(result.final_quote_balance, float)


class TestGenericRunnerWithBollinger:
    def test_generic_runner_with_bollinger(
        self, sample_candles_5m, default_pair_rules, bollinger_strategy, engine_config
    ):
        runner = GenericSimRunner(engine_config, bollinger_strategy, default_pair_rules)
        result = runner.run(sample_candles_5m)
        assert result.equity_curve is not None
        assert len(result.equity_curve) == len(sample_candles_5m)


class TestGenericRunnerArrayLength:
    def test_generic_runner_equity_curve_length(
        self, sample_candles_5m, default_pair_rules, bollinger_strategy, engine_config
    ):
        runner = GenericSimRunner(engine_config, bollinger_strategy, default_pair_rules)
        result = runner.run(sample_candles_5m)
        assert len(result.equity_curve) == len(sample_candles_5m)


class TestGenericRunnerSpotConstraints:
    def test_generic_runner_spot_constraints(
        self, sample_candles_5m, default_pair_rules, bollinger_strategy, engine_config
    ):
        runner = GenericSimRunner(engine_config, bollinger_strategy, default_pair_rules)
        result = runner.run(sample_candles_5m)
        assert result.final_base_balance >= 0.0


class TestGenericRunnerConfig:
    def test_generic_runner_config_accessible(
        self, default_pair_rules, bollinger_strategy, engine_config
    ):
        runner = GenericSimRunner(engine_config, bollinger_strategy, default_pair_rules)
        assert isinstance(runner.config, EngineConfig)
        assert runner.config.total_amount_quote == 100.0
