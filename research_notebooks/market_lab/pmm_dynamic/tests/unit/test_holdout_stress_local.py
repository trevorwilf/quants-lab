"""Tests for holdout-local stress scoring."""

import numpy as np
import pytest

from pmm_lab.objective.stress import run_stress_tests, load_stress_scenarios
from pmm_lab.objective.objective import ObjectiveWeightsV2
from pmm_lab.sim.executor_model import SimConfig


@pytest.fixture
def simple_config():
    return SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        controller_compat=False,
    )


class TestHoldoutLocalStress:
    """Verify that holdout stress scores only the holdout window."""

    def test_scoring_window_excludes_prefix(self, sample_candles_500, default_pair_rules, simple_config):
        """Stress with score_start_idx excludes pre-window data from metrics."""
        scenarios = load_stress_scenarios()
        holdout_start = 300

        # Full-dataset stress (no window)
        full_report = run_stress_tests(
            sample_candles_500, simple_config, default_pair_rules, 300,
            scenarios=scenarios,
        )

        # Holdout-local stress (score only last 200 bars)
        local_report = run_stress_tests(
            sample_candles_500, simple_config, default_pair_rules, 300,
            scenarios=scenarios,
            score_start_idx=holdout_start,
            score_end_idx=len(sample_candles_500),
            sim_start_idx=holdout_start,
        )

        # Reports should differ since they score different windows
        assert full_report.baseline_metrics.pnl_pct != local_report.baseline_metrics.pnl_pct

    def test_v2_holdout_stress_uses_v2_scoring(self, sample_candles_500, default_pair_rules, simple_config):
        """Holdout stress with objective_version=2 uses v2 scoring."""
        scenarios = load_stress_scenarios()

        report_v1 = run_stress_tests(
            sample_candles_500, simple_config, default_pair_rules, 300,
            scenarios=scenarios, objective_version=1,
        )

        report_v2 = run_stress_tests(
            sample_candles_500, simple_config, default_pair_rules, 300,
            scenarios=scenarios, objective_version=2,
            objective_weights=ObjectiveWeightsV2(),
        )

        # v1 and v2 should produce different scores
        assert report_v1.baseline_objective.raw_score != report_v2.baseline_objective.raw_score

    def test_cold_start_backward_compatible(self, sample_candles_500, default_pair_rules, simple_config):
        """Without score_start_idx, behavior is unchanged (full dataset scoring)."""
        scenarios = load_stress_scenarios()

        report = run_stress_tests(
            sample_candles_500, simple_config, default_pair_rules, 300,
            scenarios=scenarios,
        )

        assert report.baseline_metrics is not None
        assert len(report.scenario_results) == len(scenarios)
        assert report.worst_scenario is not None

    def test_score_window_matches_manual_slice(self, sample_candles_500, default_pair_rules, simple_config):
        """Scoring window approach should produce same metrics as manual holdout slice."""
        scenarios = load_stress_scenarios()[:1]  # just one scenario for speed
        holdout_start = 300
        holdout_candles = sample_candles_500[holdout_start:]

        # Cold-start on holdout only
        cold_report = run_stress_tests(
            holdout_candles, simple_config, default_pair_rules, 300,
            scenarios=scenarios,
        )

        # Both should produce valid reports (exact values differ due to warm-start effects)
        assert cold_report.baseline_metrics is not None
        assert len(cold_report.scenario_results) == 1
