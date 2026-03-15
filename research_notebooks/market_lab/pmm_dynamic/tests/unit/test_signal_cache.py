"""Tests for signal caching optimization (compute-once, reuse across folds)."""

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig


@pytest.fixture
def default_sim_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestSignalCacheParity:
    """Verify run_with_signals() produces identical results to run()."""

    def test_single_run_parity(self, sample_candles_5m, default_sim_config, default_pair_rules):
        """run_with_signals(full_signals) == run(candles) for identical candle input."""
        runner = CandleSimRunner(default_sim_config, default_pair_rules)
        # Method A: original
        result_a = runner.run(sample_candles_5m)
        # Method B: pre-computed
        signals = runner.compute_signals(sample_candles_5m)
        result_b = runner.run_with_signals(sample_candles_5m, signals)
        # Must be bit-identical
        assert_array_equal(result_a.equity_curve, result_b.equity_curve)
        assert len(result_a.trades) == len(result_b.trades)
        for ta, tb in zip(result_a.trades, result_b.trades):
            assert ta.entry_price == tb.entry_price
            assert ta.pnl_quote == tb.pnl_quote

    def test_fold_slice_parity(self, sample_candles_5m, default_sim_config, default_pair_rules):
        """Signals computed on full array give same results when used on a prefix slice."""
        runner = CandleSimRunner(default_sim_config, default_pair_rules)
        full_signals = runner.compute_signals(sample_candles_5m)

        # Slice to first 80 bars
        slice_end = 80
        candle_slice = sample_candles_5m[:slice_end]

        # Method A: run() on slice (computes signals on slice)
        result_a = runner.run(candle_slice)
        # Method B: run_with_signals() on slice using full signals
        result_b = runner.run_with_signals(candle_slice, full_signals)

        assert_array_equal(result_a.equity_curve, result_b.equity_curve)
        assert len(result_a.trades) == len(result_b.trades)

    def test_fold_slice_with_sim_start_idx_parity(self, sample_candles_5m, default_sim_config, default_pair_rules):
        """sim_start_idx works correctly with pre-computed signals."""
        runner = CandleSimRunner(default_sim_config, default_pair_rules)
        full_signals = runner.compute_signals(sample_candles_5m)

        sim_start = 60
        slice_end = 90
        candle_slice = sample_candles_5m[:slice_end]

        result_a = runner.run(candle_slice, sim_start_idx=sim_start)
        result_b = runner.run_with_signals(candle_slice, full_signals, sim_start_idx=sim_start)

        assert_array_equal(result_a.equity_curve, result_b.equity_curve)
        assert len(result_a.trades) == len(result_b.trades)

    def test_stress_with_precomputed_signals_parity(self, sample_candles_5m, default_sim_config, default_pair_rules):
        """Stress tests with precomputed signals match stress tests without."""
        from pmm_lab.objective.stress import run_stress_tests
        runner = CandleSimRunner(default_sim_config, default_pair_rules)
        signals = runner.compute_signals(sample_candles_5m)

        report_a = run_stress_tests(sample_candles_5m, default_sim_config, default_pair_rules, 300)
        report_b = run_stress_tests(sample_candles_5m, default_sim_config, default_pair_rules, 300,
                                     precomputed_signals=signals)

        assert report_a.worst_scenario == report_b.worst_scenario
        assert abs(report_a.worst_score - report_b.worst_score) < 1e-10
        assert abs(report_a.baseline_objective.raw_score - report_b.baseline_objective.raw_score) < 1e-10

    def test_backward_compat_no_precomputed(self, sample_candles_5m, default_sim_config, default_pair_rules):
        """Existing code without precomputed_signals still works (backward compat)."""
        runner = CandleSimRunner(default_sim_config, default_pair_rules)
        result = runner.run(sample_candles_5m)
        assert len(result.equity_curve) == len(sample_candles_5m)
        assert result.equity_curve[-1] > 0
