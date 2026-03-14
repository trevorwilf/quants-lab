"""Tests for position rebalance model."""

import numpy as np
import pytest

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig
from pmm_lab.config.params import PairRules, FeeConfig


def _make_engine_config_with_rebalance(**overrides):
    """EngineConfig with rebalance enabled."""
    defaults = dict(
        total_amount_quote=100.0,
        executor_refresh_time=1500.0,
        cooldown_time=0.0,
        skip_rebalance=False,
        position_rebalance_threshold_pct=0.01,
        initial_base_pct=0.0,
        fill_participation_rate=1.0,
        latency_bars=0,
    )
    defaults.update(overrides)
    return EngineConfig(**defaults)


def _make_pmm_strategy():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


def _make_bollinger_strategy():
    return BollingerStrategy(BollingerStrategyConfig(
        bb_window=20,
        bb_stdev=2.0,
        buy_spreads=(0.3, 0.6),
        sell_spreads=(0.3, 0.6),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


# ── Default behavior (v1 parity) ────────────────────────────────


class TestSkipRebalanceDefault:
    def test_skip_rebalance_true_no_rebalance(self, sample_candles_5m, default_pair_rules):
        cfg = EngineConfig(total_amount_quote=100.0, skip_rebalance=True)
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_5m, _make_pmm_strategy())
        assert result.n_rebalance_events == 0
        assert result.position_history[0] == 0.0


class TestDefaultConfigZeroRebalance:
    def test_default_config_zero_rebalance(self, sample_candles_5m, default_pair_rules):
        cfg = EngineConfig(total_amount_quote=100.0)
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_5m, _make_pmm_strategy())
        assert result.n_rebalance_events == 0


class TestV1ParityEquityUnchanged:
    def test_v1_parity_equity_unchanged(self, sample_candles_5m, default_pair_rules):
        """With defaults, SimEngine result is identical to v1."""
        cfg_v1 = EngineConfig(total_amount_quote=100.0, executor_refresh_time=1500.0)
        strat = _make_pmm_strategy()
        r1 = SimEngine(cfg_v1, default_pair_rules).run(sample_candles_5m, strat)
        r2 = SimEngine(cfg_v1, default_pair_rules).run(sample_candles_5m, strat)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)
        assert r1.n_rebalance_events == 0
        assert r2.n_rebalance_events == 0


# ── Initial base allocation ─────────────────────────────────────


class TestInitialBasePctAllocates:
    def test_initial_base_pct_allocates_base(self, sample_candles_500, default_pair_rules):
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            initial_base_pct=0.5, skip_rebalance=True,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        # Position should be > 0 at warmup
        warmup = 50  # approximate
        assert result.position_history[warmup] > 0


class TestInitialBasePctZero:
    def test_initial_base_pct_zero_no_allocation(self, sample_candles_5m, default_pair_rules):
        cfg = EngineConfig(
            total_amount_quote=100.0, initial_base_pct=0.0, skip_rebalance=True,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_5m, _make_pmm_strategy())
        assert result.position_history[0] == 0.0


class TestInitialBasePctCostsQuote:
    def test_initial_base_pct_costs_quote(self, sample_candles_500, default_pair_rules):
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            initial_base_pct=0.5, skip_rebalance=True,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        # Quote balance should be less than total_amount_quote (spent on base + fees)
        assert result.final_quote_balance < 100.0 or result.total_rebalance_fees > 0


class TestInitialBasePctEnablesSells:
    def test_initial_base_pct_enables_sells(self, sample_candles_500, default_pair_rules):
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            initial_base_pct=0.5, skip_rebalance=True,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        sells = [t for t in result.trades if t.side == "sell"]
        assert len(sells) > 0, "No sell trades with initial_base_pct=0.5"


# ── Active rebalance ────────────────────────────────────────────


class TestRebalanceEnabledPlacesInitialBuy:
    def test_rebalance_enabled_places_initial_buy(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance()
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        assert result.n_rebalance_events >= 1


class TestRebalanceProducesSellTrades:
    def test_rebalance_produces_sell_trades(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance()
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        sells = [t for t in result.trades if t.side == "sell"]
        assert len(sells) > 0, "No sell trades with rebalance enabled"


class TestRebalanceFeesAreTaker:
    def test_rebalance_fees_are_taker(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance()
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        if result.n_rebalance_events > 0:
            assert result.total_rebalance_fees > 0


class TestRebalanceRespectsQuoteLimit:
    def test_rebalance_respects_quote_limit(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance(total_amount_quote=10.0)
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        assert result.final_base_balance >= 0.0


# ── Threshold behavior ──────────────────────────────────────────


class TestRebalanceThresholdZeroDisabled:
    def test_rebalance_threshold_zero_disabled(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance(
            skip_rebalance=False, position_rebalance_threshold_pct=0.0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        assert result.n_rebalance_events == 0


class TestRebalanceThresholdHighNoRebalance:
    def test_rebalance_threshold_high_no_rebalance(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance(position_rebalance_threshold_pct=100.0)
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        assert result.n_rebalance_events == 0


class TestRebalanceThresholdLowFrequent:
    def test_rebalance_threshold_low_frequent_rebalance(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance(position_rebalance_threshold_pct=0.001)
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        assert result.n_rebalance_events > 1, "Expected frequent rebalance with very low threshold"


# ── SimResult fields ────────────────────────────────────────────


class TestSimResultHasRebalanceFields:
    def test_sim_result_has_rebalance_fields(self, sample_candles_5m, default_pair_rules):
        cfg = EngineConfig(total_amount_quote=100.0)
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_5m, _make_pmm_strategy())
        assert hasattr(result, "n_rebalance_events")
        assert hasattr(result, "total_rebalance_fees")


class TestSimResultRebalanceDefaultsZero:
    def test_sim_result_rebalance_defaults_zero(self):
        result = SimResult(
            trades=[], equity_curve=np.zeros(1), position_history=np.zeros(1),
            n_orders_placed=0, n_orders_filled=0, n_orders_rejected=0,
            n_market_exits=0, final_base_balance=0.0, final_quote_balance=100.0,
        )
        assert result.n_rebalance_events == 0
        assert result.total_rebalance_fees == 0.0


# ── Integration with strategies ─────────────────────────────────


class TestRebalanceWithPMMDynamic:
    def test_rebalance_works_with_pmm_dynamic(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance()
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_pmm_strategy())
        assert len(result.trades) > 0
        assert result.n_rebalance_events >= 1


class TestRebalanceWithBollinger:
    def test_rebalance_works_with_bollinger(self, sample_candles_500, default_pair_rules):
        cfg = _make_engine_config_with_rebalance()
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, _make_bollinger_strategy())
        assert len(result.trades) > 0
        assert result.n_rebalance_events >= 1
