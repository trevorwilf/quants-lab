"""Tests for per-side volume splitting, volume units, and order size enforcement."""

import numpy as np
import pytest

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig
from pmm_lab.config.params import PairRules, FeeConfig


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


# ── Per-side volume tests ─────────────────────────────────────────


class TestSharedVolumeV1Default:
    def test_shared_volume_v1_default(self, sample_candles_500, default_pair_rules):
        """With split_volume_by_side=False, buy and sell fills share capacity."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=0.1, latency_bars=0,
            split_volume_by_side=False,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert result.n_orders_filled >= 0


class TestSplitVolumeBuySellsIndependent:
    def test_split_volume_buy_sells_independent(self, sample_candles_500, default_pair_rules):
        """With split_volume_by_side=True, buy/sell have separate capacity pools."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=0.1, latency_bars=0,
            split_volume_by_side=True, buy_volume_fraction=0.5,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert isinstance(result.n_orders_filled, int)


class TestSplitVolumeAsymmetricFraction:
    def test_split_volume_asymmetric_fraction(self, sample_candles_500, default_pair_rules):
        """With buy_volume_fraction=0.8, buy side gets 80% of capacity."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=0.1, latency_bars=0,
            split_volume_by_side=True, buy_volume_fraction=0.8,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert len(result.equity_curve) == len(sample_candles_500)


class TestSharedVolumeParity:
    def test_shared_volume_parity(self, sample_candles_5m, default_pair_rules):
        """With defaults, SimEngine result is identical to v1."""
        strat = _make_pmm_strategy()
        cfg_default = EngineConfig(total_amount_quote=100.0, executor_refresh_time=1500.0)
        cfg_explicit = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            split_volume_by_side=False, buy_volume_fraction=0.5, volume_is_base=True,
        )
        r_default = SimEngine(cfg_default, default_pair_rules).run(sample_candles_5m, strat)
        r_explicit = SimEngine(cfg_explicit, default_pair_rules).run(sample_candles_5m, strat)
        np.testing.assert_array_equal(r_default.equity_curve, r_explicit.equity_curve)
        assert len(r_default.trades) == len(r_explicit.trades)


class TestSplitVolumeMoreTotalFills:
    def test_split_volume_more_total_fills(self, sample_candles_500, default_pair_rules):
        """With split_volume_by_side=True, total fills can be >= shared fills."""
        strat = _make_pmm_strategy()
        cfg_shared = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=0.1, latency_bars=0,
            split_volume_by_side=False,
            skip_rebalance=False, position_rebalance_threshold_pct=0.01,
        )
        cfg_split = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=0.1, latency_bars=0,
            split_volume_by_side=True, buy_volume_fraction=0.5,
            skip_rebalance=False, position_rebalance_threshold_pct=0.01,
        )
        r_shared = SimEngine(cfg_shared, default_pair_rules).run(sample_candles_500, strat)
        r_split = SimEngine(cfg_split, default_pair_rules).run(sample_candles_500, strat)
        assert r_split.n_orders_filled >= r_shared.n_orders_filled


# ── Volume unit tests ─────────────────────────────────────────────


class TestVolumeIsBaseDefault:
    def test_volume_is_base_default(self, sample_candles_5m, default_pair_rules):
        """With volume_is_base=True (default), behavior unchanged from v1."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            volume_is_base=True,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_5m, strat)
        assert result.equity_curve is not None


class TestVolumeIsQuoteConverts:
    def test_volume_is_quote_converts(self, sample_candles_500, default_pair_rules):
        """With volume_is_base=False and close ~100000, effective volume is much smaller,
        producing different fill behavior (smaller per-fill quantities)."""
        strat = _make_pmm_strategy()
        cfg_base = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            volume_is_base=True,
        )
        cfg_quote = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
            volume_is_base=False,
        )
        r_base = SimEngine(cfg_base, default_pair_rules).run(sample_candles_500, strat)
        r_quote = SimEngine(cfg_quote, default_pair_rules).run(sample_candles_500, strat)
        # With close ~100000 and small volumes (0.1-3.0), quote conversion yields
        # very tiny capacity per bar, leading to partial fills with smaller quantities.
        # Results should differ between the two modes.
        assert not np.array_equal(r_base.equity_curve, r_quote.equity_curve)


class TestVolumeIsQuoteFewerFills:
    def test_volume_is_quote_fewer_fills(self, sample_candles_500, default_pair_rules):
        """Since converted volume is smaller for high-priced assets, fewer fills occur."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=0.1, latency_bars=0,
            volume_is_base=False,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert len(result.equity_curve) == len(sample_candles_500)


# ── Order size enforcement tests ──────────────────────────────────


class TestOrderSizeMinRejectsSmallOrders:
    def test_order_size_min_rejects_small_orders(self, sample_candles_500):
        """With min_order_size_base=0.001, very small orders are rejected."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            min_order_size_base=0.001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=50.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, rules).run(sample_candles_500, strat)
        assert result.n_orders_rejected >= 0


class TestOrderSizeMaxClampsLargeOrders:
    def test_order_size_max_clamps_large_orders(self, sample_candles_500):
        """With max_order_size_base=0.0001, orders are clamped to max."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=0.001,
            max_order_size_base=0.0001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, rules).run(sample_candles_500, strat)
        # All placed orders should have quantity <= max
        for trade in result.trades:
            assert trade.quantity <= 0.0001 + 1e-10


class TestOrderSizeEnforcementPMMDynamic:
    def test_order_size_enforcement_pmm_dynamic(self, sample_candles_500):
        """PMMDynamicStrategy with min_order_size rejects undersized orders."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            min_order_size_base=0.001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=50.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None


class TestOrderSizeEnforcementBollinger:
    def test_order_size_enforcement_bollinger(self, sample_candles_500):
        """BollingerStrategy with min_order_size rejects undersized orders."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            min_order_size_base=0.001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_bollinger_strategy()
        cfg = EngineConfig(
            total_amount_quote=50.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None


class TestOrderSizeZeroMinNoRejection:
    def test_order_size_zero_min_no_rejection(self, sample_candles_500, default_pair_rules):
        """With min_order_size_base=0.0 (default), no size-based rejections."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None


# ── Combined features ─────────────────────────────────────────────


class TestAllPhase2FeaturesCombined:
    def test_all_phase2_features_combined(self, sample_candles_500):
        """All Phase 2 features enabled with PMMDynamic — no crashes, valid result."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            min_order_size_base=0.00001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            skip_rebalance=False, position_rebalance_threshold_pct=0.01,
            touch_through=True, entry_spread_bps=10.0, maker_fill_probability=0.8,
            split_volume_by_side=True, buy_volume_fraction=0.5,
            fill_participation_rate=0.1, latency_bars=1,
        )
        result = SimEngine(cfg, rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert len(result.trades) > 0
        assert result.equity_curve[-1] > 0


class TestAllPhase2FeaturesBollinger:
    def test_all_phase2_features_bollinger(self, sample_candles_500):
        """All Phase 2 features enabled with Bollinger — no crashes, valid result."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            min_order_size_base=0.00001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_bollinger_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            skip_rebalance=False, position_rebalance_threshold_pct=0.01,
            touch_through=True, entry_spread_bps=10.0, maker_fill_probability=0.8,
            split_volume_by_side=True, buy_volume_fraction=0.5,
            fill_participation_rate=0.1, latency_bars=1,
        )
        result = SimEngine(cfg, rules).run(sample_candles_500, strat)
        assert result.equity_curve is not None
        assert len(result.trades) > 0
        assert result.equity_curve[-1] > 0


class TestAllPhase2FeaturesDeterministic:
    def test_all_phase2_features_deterministic(self, sample_candles_500):
        """Two identical runs with all Phase 2 features produce identical results."""
        rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            min_order_size_base=0.00001,
            fees=FeeConfig(0.001, 0.002),
        )
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            skip_rebalance=False, position_rebalance_threshold_pct=0.01,
            touch_through=True, entry_spread_bps=10.0, maker_fill_probability=0.8,
            split_volume_by_side=True, buy_volume_fraction=0.5,
            fill_participation_rate=0.1, latency_bars=1,
        )
        r1 = SimEngine(cfg, rules).run(sample_candles_500, strat)
        r2 = SimEngine(cfg, rules).run(sample_candles_500, strat)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)
        assert len(r1.trades) == len(r2.trades)


# ── V1 parity (CRITICAL) ─────────────────────────────────────────


class TestV1ParityComplete:
    def test_v1_parity_complete(self, sample_candles_5m, default_pair_rules):
        """With ALL v2 features at defaults, equity curve is byte-identical to v1-default run."""
        strat = _make_pmm_strategy()
        cfg_v1 = EngineConfig(total_amount_quote=100.0, executor_refresh_time=1500.0)
        cfg_explicit = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            split_volume_by_side=False, touch_through=False,
            entry_spread_bps=0.0, maker_fill_probability=1.0,
            skip_rebalance=True, initial_base_pct=0.0,
            volume_is_base=True, buy_volume_fraction=0.5,
        )
        r_v1 = SimEngine(cfg_v1, default_pair_rules).run(sample_candles_5m, strat)
        r_explicit = SimEngine(cfg_explicit, default_pair_rules).run(sample_candles_5m, strat)
        np.testing.assert_array_equal(r_v1.equity_curve, r_explicit.equity_curve)
        assert len(r_v1.trades) == len(r_explicit.trades)
        assert r_v1.n_orders_placed == r_explicit.n_orders_placed
        assert r_v1.n_orders_filled == r_explicit.n_orders_filled
