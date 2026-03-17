"""Tests for stress_selection early-pruning module."""

import numpy as np
import pytest
from dataclasses import replace

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.objective.stress import run_stress_tests, load_stress_scenarios
from pmm_lab.objective.stress_selection import select_best_stressed_candidate


@pytest.fixture
def base_config():
    return SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        controller_compat=False,
    )


def _make_candidates(base_config, n=5):
    """Create n candidates with slightly varied configs."""
    candidates = []
    for i in range(n):
        cfg = replace(base_config, buy_spreads=[1.0 + i * 0.1])
        candidates.append({
            "trial_number": i,
            "phase1_score": 10.0 - i,  # descending order
            "config": cfg,
        })
    return candidates


class TestSelectBestStressedCandidate:
    """Core correctness tests for early-pruning selection."""

    def test_same_winner_with_and_without_pruning(self, sample_candles_500, default_pair_rules, base_config):
        """Pruning produces the same winner as exhaustive evaluation."""
        scenarios = load_stress_scenarios()
        candidates = _make_candidates(base_config, n=5)

        # Exhaustive: evaluate all candidates fully
        exhaustive_results = []
        for cand in candidates:
            report = run_stress_tests(
                sample_candles_500, cand["config"], default_pair_rules, 300,
                scenarios=scenarios,
            )
            robust = 0.5 * report.baseline_objective.raw_score + 0.5 * report.worst_score
            exhaustive_results.append({
                "trial_number": cand["trial_number"],
                "robust_score": robust,
                "baseline_score": report.baseline_objective.raw_score,
                "worst_score": report.worst_score,
                "worst_scenario": report.worst_scenario,
                "stress_report": report,
            })
        exhaustive_best = max(exhaustive_results, key=lambda r: r["robust_score"])

        # Pruning path
        best, diag = select_best_stressed_candidate(
            candidates, sample_candles_500, default_pair_rules, 300,
            scenarios=scenarios,
        )

        # Same winner
        assert best is not None
        assert best["trial_number"] == exhaustive_best["trial_number"]
        assert best["robust_score"] == pytest.approx(exhaustive_best["robust_score"], abs=1e-10)
        assert best["baseline_score"] == pytest.approx(exhaustive_best["baseline_score"], abs=1e-10)
        assert best["worst_score"] == pytest.approx(exhaustive_best["worst_score"], abs=1e-10)
        assert best["worst_scenario"] == exhaustive_best["worst_scenario"]

    def test_scenario_order_preserved_in_winner(self, sample_candles_500, default_pair_rules, base_config):
        """Winner's StressReport.scenario_results are in original YAML order."""
        scenarios = load_stress_scenarios()
        candidates = _make_candidates(base_config, n=3)

        best, _ = select_best_stressed_candidate(
            candidates, sample_candles_500, default_pair_rules, 300,
            scenarios=scenarios,
        )

        assert best is not None
        report = best["stress_report"]
        # Verify scenario order matches original
        for i, sr in enumerate(report.scenario_results):
            assert sr.scenario.name == scenarios[i].name

    def test_diagnostics_populated(self, sample_candles_500, default_pair_rules, base_config):
        """Diagnostic counters are populated."""
        scenarios = load_stress_scenarios()
        candidates = _make_candidates(base_config, n=5)

        _, diag = select_best_stressed_candidate(
            candidates, sample_candles_500, default_pair_rules, 300,
            scenarios=scenarios,
        )

        assert diag["candidates_evaluated"] == 5
        assert diag["candidates_fully_evaluated"] >= 1
        assert diag["signal_cache_hits"] + diag["signal_cache_misses"] == 5

    def test_single_candidate(self, sample_candles_500, default_pair_rules, base_config):
        """Single candidate: no pruning possible, returns that candidate."""
        scenarios = load_stress_scenarios()
        candidates = _make_candidates(base_config, n=1)

        best, diag = select_best_stressed_candidate(
            candidates, sample_candles_500, default_pair_rules, 300,
            scenarios=scenarios,
        )

        assert best is not None
        assert best["trial_number"] == 0
        assert diag["candidates_pruned"] == 0
        assert diag["candidates_fully_evaluated"] == 1

    def test_empty_candidates(self, sample_candles_500, default_pair_rules):
        """Empty candidate list returns None."""
        best, diag = select_best_stressed_candidate(
            [], sample_candles_500, default_pair_rules, 300,
        )
        assert best is None
        assert diag["candidates_evaluated"] == 0

    def test_identical_configs_same_result(self, sample_candles_500, default_pair_rules, base_config):
        """All candidates with identical config: first one wins (ties go to earlier)."""
        scenarios = load_stress_scenarios()
        candidates = [
            {"trial_number": 0, "phase1_score": 10.0, "config": base_config},
            {"trial_number": 1, "phase1_score": 9.0, "config": base_config},
            {"trial_number": 2, "phase1_score": 8.0, "config": base_config},
        ]

        best, diag = select_best_stressed_candidate(
            candidates, sample_candles_500, default_pair_rules, 300,
            scenarios=scenarios,
        )

        assert best is not None
        # First candidate wins ties
        assert best["trial_number"] == 0

    def test_signal_cache_reused_across_candidates(self, sample_candles_500, default_pair_rules, base_config):
        """Signal cache is shared — same signal params hit cache."""
        scenarios = load_stress_scenarios()
        # All candidates have same signal params (different trade params)
        candidates = []
        for i in range(3):
            cfg = replace(base_config, stop_loss=0.02 + i * 0.01)
            candidates.append({
                "trial_number": i, "phase1_score": 10.0 - i, "config": cfg,
            })

        cache = {}
        best, diag = select_best_stressed_candidate(
            candidates, sample_candles_500, default_pair_rules, 300,
            scenarios=scenarios, signal_cache=cache,
        )

        # All 3 candidates should share the same signals
        assert diag["signal_cache_misses"] == 1
        assert diag["signal_cache_hits"] == 2
