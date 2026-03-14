"""Integration tests for v2 fill realism features in SimEngine."""

import numpy as np
import pytest

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig


def _make_pmm_strategy():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


def _make_bollinger_strategy():
    return BollingerStrategy(BollingerStrategyConfig(
        bb_window=20, bb_stdev=2.0,
        buy_spreads=(0.3, 0.6),
        sell_spreads=(0.3, 0.6),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


class TestEngineTouchThroughFewerFills:
    def test_engine_touch_through_fewer_fills(self, sample_candles_500, default_pair_rules):
        strat = _make_pmm_strategy()
        cfg_v1 = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            touch_through=False,
        )
        cfg_v2 = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            touch_through=True,
        )
        r_v1 = SimEngine(cfg_v1, default_pair_rules).run(sample_candles_500, strat)
        r_v2 = SimEngine(cfg_v2, default_pair_rules).run(sample_candles_500, strat)
        assert r_v2.n_orders_filled <= r_v1.n_orders_filled


class TestEngineEntrySpreadReducesPnl:
    def test_engine_entry_spread_reduces_pnl(self, sample_candles_500, default_pair_rules):
        strat = _make_pmm_strategy()
        cfg_no = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            entry_spread_bps=0.0,
        )
        cfg_with = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            entry_spread_bps=20.0,
        )
        r_no = SimEngine(cfg_no, default_pair_rules).run(sample_candles_500, strat)
        r_with = SimEngine(cfg_with, default_pair_rules).run(sample_candles_500, strat)
        assert r_with.equity_curve[-1] <= r_no.equity_curve[-1] + 0.01


class TestEngineMakerProbabilityReducesTrades:
    def test_engine_maker_probability_reduces_trades(self, sample_candles_500, default_pair_rules):
        strat = _make_pmm_strategy()
        cfg_full = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            maker_fill_probability=1.0,
        )
        cfg_half = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            maker_fill_probability=0.5,
        )
        r_full = SimEngine(cfg_full, default_pair_rules).run(sample_candles_500, strat)
        r_half = SimEngine(cfg_half, default_pair_rules).run(sample_candles_500, strat)
        assert len(r_half.trades) <= len(r_full.trades)


class TestEngineV1DefaultsParity:
    def test_engine_v1_defaults_parity(self, sample_candles_5m, default_pair_rules):
        strat = _make_pmm_strategy()
        cfg_default = EngineConfig(total_amount_quote=100.0, executor_refresh_time=1500.0)
        cfg_explicit = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            touch_through=False, entry_spread_bps=0.0, maker_fill_probability=1.0,
        )
        r_default = SimEngine(cfg_default, default_pair_rules).run(sample_candles_5m, strat)
        r_explicit = SimEngine(cfg_explicit, default_pair_rules).run(sample_candles_5m, strat)
        np.testing.assert_array_equal(r_default.equity_curve, r_explicit.equity_curve)
        assert len(r_default.trades) == len(r_explicit.trades)


class TestEngineTouchThroughWithRebalance:
    def test_engine_touch_through_with_rebalance(self, sample_candles_500, default_pair_rules):
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            touch_through=True,
            skip_rebalance=False, position_rebalance_threshold_pct=0.01,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert len(result.equity_curve) == len(sample_candles_500)


class TestEngineAllV2Bollinger:
    def test_engine_all_v2_features_bollinger(self, sample_candles_500, default_pair_rules):
        strat = _make_bollinger_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            touch_through=True, entry_spread_bps=10.0, maker_fill_probability=0.8,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert isinstance(result.n_orders_filled, int)
        assert result.final_base_balance >= 0.0
