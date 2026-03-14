"""Tests for fold-local stress and robust_aggregate_v2."""

import numpy as np
import pytest

from pmm_lab.objective.stress import run_fold_local_stress, run_stress_tests, load_stress_scenarios
from pmm_lab.objective.robustness import robust_aggregate, robust_aggregate_v2
from pmm_lab.objective.objective import REJECT_SCORE
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig


def _make_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


def _make_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


class TestFoldLocalStressReturnsScores:
    def test_fold_local_stress_returns_scores(self, sample_candles_500):
        config = _make_config()
        rules = _make_rules()
        scenarios = load_stress_scenarios()
        scores = run_fold_local_stress(
            sample_candles_500, config, rules, 300,
            fold_test_start_idx=200, fold_test_end_idx=300,
            scenarios=scenarios,
        )
        assert isinstance(scores, list)
        assert len(scores) == len(scenarios)
        for s in scores:
            assert isinstance(s, float)


class TestFoldLocalStressDiffersFromFull:
    def test_fold_local_stress_scores_differ_from_full(self, sample_candles_500):
        config = _make_config()
        rules = _make_rules()
        # Full dataset stress
        full_report = run_stress_tests(sample_candles_500, config, rules, 300)
        full_scores = [sr.objective.raw_score for sr in full_report.scenario_results]
        # Fold-local stress (bars 200-300)
        fold_scores = run_fold_local_stress(
            sample_candles_500, config, rules, 300,
            fold_test_start_idx=200, fold_test_end_idx=300,
        )
        assert len(fold_scores) == len(full_scores)
        # Scores should differ (different candle windows)
        assert fold_scores != full_scores


class TestFoldLocalStressAllScenariosRun:
    def test_fold_local_stress_all_scenarios_run(self, sample_candles_500):
        config = _make_config()
        rules = _make_rules()
        scenarios = load_stress_scenarios()
        scores = run_fold_local_stress(
            sample_candles_500, config, rules, 300,
            fold_test_start_idx=100, fold_test_end_idx=200,
            scenarios=scenarios,
        )
        assert len(scores) == len(scenarios)


class TestRobustAggregateV2Basic:
    def test_robust_aggregate_v2_basic(self):
        fold_scores = [5.0, 4.0, 3.0, 2.0]
        result = robust_aggregate_v2(fold_scores)
        median_val = float(np.median(fold_scores))
        # Result should be <= median (MAD penalty)
        assert result <= median_val


class TestRobustAggregateV2WithStress:
    def test_robust_aggregate_v2_with_stress(self):
        fold_scores = [5.0, 4.0, 3.0, 2.0]
        # Stress scores are worse (lower) than baseline
        fold_stress_scores = [
            [3.0, 2.0, 1.0],
            [2.5, 1.5, 0.5],
            [2.0, 1.0, 0.0],
            [1.5, 0.5, -0.5],
        ]
        result_with_stress = robust_aggregate_v2(
            fold_scores, fold_stress_scores=fold_stress_scores,
        )
        result_no_stress = robust_aggregate_v2(fold_scores)
        # With stress, result should be lower (stress is conservative)
        assert result_with_stress < result_no_stress


class TestRobustAggregateV2WithSensitivity:
    def test_robust_aggregate_v2_with_sensitivity(self):
        fold_scores = [5.0, 4.0, 3.0, 2.0]
        result_no_sens = robust_aggregate_v2(fold_scores, sensitivity_penalty=0.0)
        result_with_sens = robust_aggregate_v2(fold_scores, sensitivity_penalty=0.5)
        assert result_with_sens < result_no_sens


class TestRobustAggregateV2BackwardCompat:
    def test_robust_aggregate_v2_backward_compat(self):
        """With no stress and no sensitivity, result matches robust_aggregate v1."""
        fold_scores = [5.0, 4.0, 3.0, 2.0]
        v1_result = robust_aggregate(fold_scores, lambda_mad=0.5)
        v2_result = robust_aggregate_v2(
            fold_scores,
            fold_stress_scores=None,
            lambda_mad=0.5,
            sensitivity_penalty=0.0,
            sensitivity_weight=0.0,
        )
        assert abs(v1_result - v2_result) < 1e-9
