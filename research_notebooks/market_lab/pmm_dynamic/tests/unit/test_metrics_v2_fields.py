"""Tests for v2 metric fields: median_trade_pnl_quote, inventory_exposure_p95."""

import numpy as np
import pytest

from pmm_lab.metrics.metrics import Metrics, compute_metrics
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.config.params import PairRules, FeeConfig


def _make_pmm_strategy():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


class TestMetricsHasMedianTradePnl:
    def test_metrics_has_median_trade_pnl(self):
        m = Metrics(
            pnl_pct=5.0, net_pnl_quote=5.0, max_drawdown_pct=10.0, sharpe=1.5,
            trade_count=20, fill_count=40, n_winning=12, n_losing=8,
            gross_win_quote=30.0, gross_loss_quote=15.0, profit_factor=2.0,
            total_fees_quote=1.0, maker_fees_quote=0.5, taker_fees_quote=0.5,
            fee_drag_pct=1.0, inventory_exposure_mean=0.05, inventory_exposure_max=0.1,
            expected_shortfall_5pct=0.0, volume_zero_bar_count=0, volume_zero_bar_fraction=0.0,
            median_trade_pnl_quote=0.5, inventory_exposure_p95=0.08,
        )
        assert isinstance(m.median_trade_pnl_quote, float)
        assert m.median_trade_pnl_quote == 0.5


class TestMetricsHasInventoryP95:
    def test_metrics_has_inventory_p95(self):
        m = Metrics(
            pnl_pct=5.0, net_pnl_quote=5.0, max_drawdown_pct=10.0, sharpe=1.5,
            trade_count=20, fill_count=40, n_winning=12, n_losing=8,
            gross_win_quote=30.0, gross_loss_quote=15.0, profit_factor=2.0,
            total_fees_quote=1.0, maker_fees_quote=0.5, taker_fees_quote=0.5,
            fee_drag_pct=1.0, inventory_exposure_mean=0.05, inventory_exposure_max=0.1,
            expected_shortfall_5pct=0.0, volume_zero_bar_count=0, volume_zero_bar_fraction=0.0,
            median_trade_pnl_quote=0.5, inventory_exposure_p95=0.08,
        )
        assert isinstance(m.inventory_exposure_p95, float)
        assert m.inventory_exposure_p95 == 0.08


class TestMedianTradePnlCorrect:
    def test_median_trade_pnl_correct(self, sample_candles_500, default_pair_rules):
        """Run a known config, verify median_trade_pnl_quote matches manual calculation."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)

        # Manual calculation
        trade_pnls = [t.pnl_quote for t in result.trades if t.pnl_quote is not None]
        expected_median = float(np.median(trade_pnls)) if trade_pnls else 0.0
        assert abs(metrics.median_trade_pnl_quote - expected_median) < 1e-10


class TestInventoryP95HigherThanMean:
    def test_inventory_p95_higher_than_mean(self, sample_candles_500, default_pair_rules):
        """p95 >= mean (by definition of percentiles)."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)
        assert metrics.inventory_exposure_p95 >= metrics.inventory_exposure_mean - 1e-10


class TestMedianTradePnlZeroNoTrades:
    def test_median_trade_pnl_zero_no_trades(self, sample_candles_5m, default_pair_rules):
        """With 0 trades, median_trade_pnl_quote is 0.0."""
        # Use a config that won't produce any trades (very high spreads)
        strat = PMMDynamicStrategy(PMMDynamicStrategyConfig(
            buy_spreads=(100.0,), sell_spreads=(100.0,),
            buy_amounts_pct=(1.0,), sell_amounts_pct=(1.0,),
        ))
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_5m, strat)
        metrics = compute_metrics(result, 100.0, sample_candles_5m, 300)
        assert metrics.median_trade_pnl_quote == 0.0


class TestOldMetricsFieldsUnchanged:
    def test_old_metrics_fields_unchanged(self, sample_candles_500, default_pair_rules):
        """All v1 fields still computed correctly."""
        strat = _make_pmm_strategy()
        cfg = EngineConfig(
            total_amount_quote=100.0, executor_refresh_time=1500.0,
            fill_participation_rate=1.0, latency_bars=0,
        )
        result = SimEngine(cfg, default_pair_rules).run(sample_candles_500, strat)
        metrics = compute_metrics(result, 100.0, sample_candles_500, 300)

        # Verify all v1 fields exist and are reasonable
        assert isinstance(metrics.pnl_pct, float)
        assert isinstance(metrics.net_pnl_quote, float)
        assert isinstance(metrics.max_drawdown_pct, float)
        assert isinstance(metrics.sharpe, float)
        assert isinstance(metrics.trade_count, int)
        assert isinstance(metrics.fill_count, int)
        assert isinstance(metrics.profit_factor, float)
        assert isinstance(metrics.total_fees_quote, float)
        assert isinstance(metrics.fee_drag_pct, float)
        assert isinstance(metrics.inventory_exposure_mean, float)
        assert isinstance(metrics.inventory_exposure_max, float)
        assert isinstance(metrics.expected_shortfall_5pct, float)
        assert metrics.max_drawdown_pct >= 0
        assert metrics.total_fees_quote >= 0
