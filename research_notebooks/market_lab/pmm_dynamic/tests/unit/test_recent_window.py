"""Tests for recent-window evaluation."""

import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.objective.recent_window import evaluate_recent_window, RecentWindowResult
from pmm_lab.objective.stress import load_stress_scenarios


@pytest.fixture
def simple_config():
    return SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        controller_compat=False,
    )


class TestRecentWindowEvaluation:
    """Core tests for recent-window evaluator."""

    def test_warm_start_excludes_pre_window(self, sample_candles_500, default_pair_rules, simple_config):
        """Recent window metrics should differ from full-dataset metrics."""
        from pmm_lab.sim.runner import CandleSimRunner
        from pmm_lab.metrics.metrics import compute_metrics

        # Full-dataset metrics
        runner = CandleSimRunner(simple_config, default_pair_rules)
        full_result = runner.run(sample_candles_500)
        full_metrics = compute_metrics(
            full_result, simple_config.total_amount_quote,
            sample_candles_500, 300,
        )

        # Recent-window metrics (last ~3.5 days of 5m bars = ~1000 bars,
        # but we only have 500, so use recent_days=1 to get a subset)
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=1, run_stress=False,
        )

        assert rw.metrics is not None
        assert rw.recent_bars < len(sample_candles_500)
        assert rw.recent_bars > 0
        # Metrics should differ since we're scoring different windows
        assert rw.metrics.pnl_pct != full_metrics.pnl_pct

    def test_acceptance_criteria_positive(self, sample_candles_500, default_pair_rules, simple_config):
        """Test that acceptance criteria logic works."""
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=5, run_stress=False,
            min_trades=0,  # permissive for test
            max_drawdown_pct=100.0,
        )

        assert isinstance(rw, RecentWindowResult)
        assert rw.metrics is not None
        assert rw.objective is not None
        # Whether it passes depends on actual backtest results, but the structure is correct
        assert isinstance(rw.passed, bool)
        assert isinstance(rw.reason, str)

    def test_acceptance_fails_on_high_min_trades(self, sample_candles_500, default_pair_rules, simple_config):
        """Requiring impossibly many trades should fail."""
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=1, run_stress=False,
            min_trades=10000,  # impossibly high
        )

        assert rw.passed is False
        assert "recent trades" in rw.reason

    def test_acceptance_fails_on_tight_drawdown(self, sample_candles_500, default_pair_rules, simple_config):
        """Setting max_drawdown_pct=0 should fail if any drawdown occurs."""
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=5, run_stress=False,
            max_drawdown_pct=0.0,
            min_trades=0,
        )
        # If there are any trades at all, there's likely some drawdown
        if rw.metrics.max_drawdown_pct > 0:
            assert rw.passed is False
            assert "max DD" in rw.reason

    def test_stress_integration(self, sample_candles_500, default_pair_rules, simple_config):
        """Stress testing works on recent window."""
        scenarios = load_stress_scenarios()
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=5, run_stress=True,
            scenarios=scenarios,
            min_trades=0,
            max_drawdown_pct=100.0,
        )

        assert rw.stress_report is not None
        assert len(rw.stress_report.scenario_results) == len(scenarios)
        assert rw.stress_report.worst_scenario is not None

    def test_no_bars_in_window(self, sample_candles_500, default_pair_rules, simple_config):
        """If start_ts is beyond all data, returns failed result."""
        last_ts = int(sample_candles_500["timestamp"][-1])
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            start_ts=last_ts + 86400,  # 1 day after last bar
            run_stress=False,
        )

        assert rw.passed is False
        assert rw.recent_bars == 0
        assert "No bars" in rw.reason

    def test_v2_scoring(self, sample_candles_500, default_pair_rules, simple_config):
        """v2 objective produces different results than v1."""
        rw_v1 = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=5, run_stress=False, objective_version=1,
            min_trades=0, max_drawdown_pct=100.0,
        )
        rw_v2 = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=5, run_stress=False, objective_version=2,
            min_trades=0, max_drawdown_pct=100.0,
        )

        assert rw_v1.objective.raw_score != rw_v2.objective.raw_score

    def test_result_timestamps_correct(self, sample_candles_500, default_pair_rules, simple_config):
        """Recent window timestamps are within the candle range."""
        rw = evaluate_recent_window(
            sample_candles_500, simple_config, default_pair_rules, 300,
            recent_days=3, run_stress=False,
        )

        first_ts = int(sample_candles_500["timestamp"][0])
        last_ts = int(sample_candles_500["timestamp"][-1])

        assert rw.recent_start_timestamp >= first_ts
        assert rw.recent_end_timestamp == last_ts
        assert rw.recent_start_timestamp <= rw.recent_end_timestamp
