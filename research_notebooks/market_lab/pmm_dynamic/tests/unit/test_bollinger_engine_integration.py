"""Full pipeline integration tests for Bollinger strategy."""

import numpy as np
import pytest

from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.generic_runner import GenericSimRunner
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import objective_v1
from pmm_lab.config.params import PairRules, FeeConfig


@pytest.fixture
def bollinger_config():
    return BollingerStrategyConfig(
        bb_window=20,
        bb_stdev=2.0,
        buy_spreads=(0.3, 0.6),
        sell_spreads=(0.3, 0.6),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    )


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0, executor_refresh_time=1500.0)


class TestBollingerProducesTrades:
    def test_bollinger_produces_trades(
        self, sample_candles_500, default_pair_rules, bollinger_config, engine_config
    ):
        strategy = BollingerStrategy(bollinger_config)
        engine = SimEngine(engine_config, default_pair_rules)
        result = engine.run(sample_candles_500, strategy)
        assert len(result.trades) > 0, "Bollinger strategy produced no trades on 500-bar data"


class TestBollingerEquityNotFlat:
    def test_bollinger_equity_not_flat(
        self, sample_candles_500, default_pair_rules, bollinger_config, engine_config
    ):
        strategy = BollingerStrategy(bollinger_config)
        engine = SimEngine(engine_config, default_pair_rules)
        result = engine.run(sample_candles_500, strategy)
        eq = result.equity_curve
        assert np.std(eq) > 0, "Equity curve is flat — strategy is not doing anything"


class TestBollingerMetrics:
    def test_bollinger_metrics_computable(
        self, sample_candles_500, default_pair_rules, bollinger_config, engine_config
    ):
        strategy = BollingerStrategy(bollinger_config)
        runner = GenericSimRunner(engine_config, strategy, default_pair_rules)
        result = runner.run(sample_candles_500)
        metrics = compute_metrics(result, engine_config.total_amount_quote, sample_candles_500, 300)
        assert metrics.trade_count >= 0
        assert isinstance(metrics.pnl_pct, float)
        assert isinstance(metrics.sharpe, float)


class TestBollingerObjective:
    def test_bollinger_objective_computable(
        self, sample_candles_500, default_pair_rules, bollinger_config, engine_config
    ):
        strategy = BollingerStrategy(bollinger_config)
        runner = GenericSimRunner(engine_config, strategy, default_pair_rules)
        result = runner.run(sample_candles_500)
        metrics = compute_metrics(result, engine_config.total_amount_quote, sample_candles_500, 300)
        obj = objective_v1(metrics)
        assert isinstance(obj.raw_score, float)


class TestBollingerDeterministic:
    def test_bollinger_deterministic(
        self, sample_candles_500, default_pair_rules, bollinger_config, engine_config
    ):
        strategy = BollingerStrategy(bollinger_config)
        r1 = SimEngine(engine_config, default_pair_rules).run(sample_candles_500, strategy)
        r2 = SimEngine(engine_config, default_pair_rules).run(sample_candles_500, strategy)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)
        assert len(r1.trades) == len(r2.trades)
        assert r1.n_orders_placed == r2.n_orders_placed


class TestBollingerDifferentWindow:
    def test_bollinger_different_window_different_results(
        self, sample_candles_500, default_pair_rules, engine_config
    ):
        cfg10 = BollingerStrategyConfig(
            bb_window=10, bb_stdev=2.0,
            buy_spreads=(0.3, 0.6), sell_spreads=(0.3, 0.6),
            buy_amounts_pct=(0.5, 0.5), sell_amounts_pct=(0.5, 0.5),
        )
        cfg30 = BollingerStrategyConfig(
            bb_window=30, bb_stdev=2.0,
            buy_spreads=(0.3, 0.6), sell_spreads=(0.3, 0.6),
            buy_amounts_pct=(0.5, 0.5), sell_amounts_pct=(0.5, 0.5),
        )
        r10 = SimEngine(engine_config, default_pair_rules).run(
            sample_candles_500, BollingerStrategy(cfg10)
        )
        r30 = SimEngine(engine_config, default_pair_rules).run(
            sample_candles_500, BollingerStrategy(cfg30)
        )
        # Different windows should produce different trade counts or equity
        assert not np.array_equal(r10.equity_curve, r30.equity_curve) or \
            len(r10.trades) != len(r30.trades), \
            "bb_window=10 and bb_window=30 produced identical results"


class TestBollingerVsPMMDynamic:
    def test_bollinger_vs_pmm_dynamic_different_results(
        self, sample_candles_500, default_pair_rules, engine_config, bollinger_config
    ):
        pmm_config = PMMDynamicStrategyConfig(
            buy_spreads=(1.0, 2.0), sell_spreads=(1.0, 2.0),
            buy_amounts_pct=(0.5, 0.5), sell_amounts_pct=(0.5, 0.5),
        )
        r_pmm = SimEngine(engine_config, default_pair_rules).run(
            sample_candles_500, PMMDynamicStrategy(pmm_config)
        )
        r_boll = SimEngine(engine_config, default_pair_rules).run(
            sample_candles_500, BollingerStrategy(bollinger_config)
        )
        assert not np.array_equal(r_pmm.equity_curve, r_boll.equity_curve), \
            "PMM Dynamic and Bollinger produced identical equity curves — strategies not independent"
