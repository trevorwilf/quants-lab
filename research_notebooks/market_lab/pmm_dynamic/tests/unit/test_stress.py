"""Tests for pmm_lab.objective.stress — stress testing engine."""

import pytest
import numpy as np

pytestmark = pytest.mark.slow
from dataclasses import replace

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.objective.stress import (
    load_stress_scenarios, apply_scenario, run_stress_tests,
    StressScenario, StressReport,
)

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


@pytest.fixture
def default_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
        latency_bars=1,
        slippage_bps=5.0,
        fill_participation_rate=0.1,
    )


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def sample_candles_100():
    """100-bar candle array for stress tests."""
    rng = np.random.default_rng(seed=42)
    n = 100
    start_ts = 1756833000
    interval = 300
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 50)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.05, 2.0)
        rows.append((start_ts + i * interval, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


class TestLoadStressScenarios:
    def test_load_scenarios_from_yaml(self):
        """Load configs/stress_scenarios.yaml. Assert >= 10 scenarios with name and description."""
        scenarios = load_stress_scenarios()
        assert len(scenarios) >= 10
        for s in scenarios:
            assert s.name
            assert s.description


class TestApplyScenario:
    def test_apply_fee_scenario(self, default_config, default_pair_rules):
        """Apply fees_1.5x → maker_fee is 1.5x original."""
        scenario = StressScenario(
            name="fees_1.5x",
            description="test",
            maker_fee_multiplier=1.5,
            taker_fee_multiplier=1.5,
        )
        new_config, new_rules = apply_scenario(default_config, default_pair_rules, scenario)
        assert abs(new_rules.fees.maker_fee - 0.001 * 1.5) < 1e-9
        assert abs(new_rules.fees.taker_fee - 0.002 * 1.5) < 1e-9

    def test_apply_latency_scenario(self, default_config, default_pair_rules):
        """Apply latency_plus2 → latency_bars increased by 2."""
        scenario = StressScenario(
            name="latency_plus2",
            description="test",
            latency_bars_add=2,
        )
        new_config, new_rules = apply_scenario(default_config, default_pair_rules, scenario)
        assert new_config.latency_bars == default_config.latency_bars + 2

    def test_apply_combined_scenario(self, default_config, default_pair_rules):
        """Apply combined_adverse → fees, latency, slippage, participation all modified."""
        scenario = StressScenario(
            name="combined_adverse",
            description="test",
            maker_fee_multiplier=1.5,
            taker_fee_multiplier=1.5,
            latency_bars_add=1,
            slippage_bps_multiplier=2.0,
            fill_participation_multiplier=0.5,
        )
        new_config, new_rules = apply_scenario(default_config, default_pair_rules, scenario)
        assert new_config.latency_bars == default_config.latency_bars + 1
        assert abs(new_config.slippage_bps - default_config.slippage_bps * 2.0) < 1e-9
        assert abs(new_config.fill_participation_rate - default_config.fill_participation_rate * 0.5) < 1e-9
        assert abs(new_rules.fees.maker_fee - 0.001 * 1.5) < 1e-9


class TestRunStressTests:
    def test_stress_report_has_all_scenarios(self, default_config, default_pair_rules, sample_candles_100):
        """run_stress_tests() → len(scenario_results) == len(scenarios)."""
        scenarios = load_stress_scenarios()
        report = run_stress_tests(
            sample_candles_100, default_config, default_pair_rules, 300,
            scenarios=scenarios,
        )
        assert len(report.scenario_results) == len(scenarios)

    def test_stress_worst_identified(self, default_config, default_pair_rules, sample_candles_100):
        """worst_scenario corresponds to lowest objective score."""
        report = run_stress_tests(
            sample_candles_100, default_config, default_pair_rules, 300,
        )
        scores = [(sr.scenario.name, sr.objective.raw_score) for sr in report.scenario_results]
        actual_worst = min(scores, key=lambda x: x[1])
        assert report.worst_scenario == actual_worst[0]
        assert abs(report.worst_score - actual_worst[1]) < 1e-9

    def test_baseline_included(self, default_config, default_pair_rules, sample_candles_100):
        """baseline_metrics and baseline_objective are populated."""
        report = run_stress_tests(
            sample_candles_100, default_config, default_pair_rules, 300,
        )
        assert report.baseline_metrics is not None
        assert report.baseline_objective is not None


class TestEmptyStressScenarios:
    def test_empty_scenarios_returns_baseline(self):
        """Empty scenario list must not crash — returns baseline-only report."""
        from tests.conftest import _make_sample_candles_5m
        from pmm_lab.sim.executor_model import SimConfig
        from pmm_lab.config.params import PairRules, FeeConfig
        from pmm_lab.objective.stress import run_stress_tests

        candles = _make_sample_candles_5m()
        config = SimConfig(
            buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
        )
        rules = PairRules(price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0,
                          fees=FeeConfig(0.001, 0.002))

        report = run_stress_tests(candles, config, rules, 300, scenarios=[])
        assert report.worst_scenario == "none"
        assert len(report.scenario_results) == 0
        assert report.worst_score == report.baseline_objective.raw_score


class TestVolumeMultiplier:
    def test_volume_multiplier_scales_fills(self):
        """volume_multiplier < 1.0 should reduce candle volume and potentially reduce fills."""
        from tests.conftest import _make_sample_candles_5m
        from pmm_lab.sim.executor_model import SimConfig
        from pmm_lab.config.params import PairRules, FeeConfig
        from pmm_lab.objective.stress import run_stress_tests, StressScenario

        candles = _make_sample_candles_5m()
        config = SimConfig(
            buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
        )
        rules = PairRules(price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0,
                          fees=FeeConfig(0.001, 0.002))

        thin_scenario = StressScenario(
            name="thin_liquidity",
            description="10% volume",
            volume_multiplier=0.1,
        )
        stressed = run_stress_tests(candles, config, rules, 300, scenarios=[thin_scenario])

        assert len(stressed.scenario_results) == 1
        assert stressed.scenario_results[0].scenario.name == "thin_liquidity"
        assert isinstance(stressed.scenario_results[0].objective.raw_score, float)

    def test_volume_1_0_matches_baseline(self):
        """volume_multiplier=1.0 must produce identical results to no multiplier."""
        from tests.conftest import _make_sample_candles_5m
        from pmm_lab.sim.executor_model import SimConfig
        from pmm_lab.config.params import PairRules, FeeConfig
        from pmm_lab.objective.stress import run_stress_tests, StressScenario

        candles = _make_sample_candles_5m()
        config = SimConfig(
            buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
        )
        rules = PairRules(price_tick=0.01, amount_step=0.000001,
                          min_notional_quote=5.0, fees=FeeConfig(0.001, 0.002))

        noop_scenario = StressScenario(
            name="noop", description="1x volume", volume_multiplier=1.0,
        )
        report = run_stress_tests(candles, config, rules, 300, scenarios=[noop_scenario])
        baseline_score = report.baseline_objective.raw_score
        scenario_score = report.scenario_results[0].objective.raw_score
        assert abs(baseline_score - scenario_score) < 1e-10, \
            "volume_multiplier=1.0 should produce identical score to baseline"
