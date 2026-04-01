"""Tests for MACD-BB stress testing integration."""

import numpy as np
import pytest

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.objective.stress import load_stress_scenarios
from pmm_lab.objective.stress_macd_bb import (
    apply_scenario_engine_config,
    run_macd_bb_fold_local_stress,
)
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=500, seed=99):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1756833000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 100)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 40))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 40))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.1, 3.0)
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def candles():
    return _make_candles()


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0, stop_loss=0.05, take_profit=0.03)


@pytest.fixture
def strategy_config():
    return MACDBBStrategyConfig(
        bb_length=20, bb_std=2.0,
        bb_long_threshold=0.2, bb_short_threshold=0.8,
        macd_fast=12, macd_slow=26, macd_signal=9,
        controller_compat=False,
    )


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


class TestApplyScenario:
    def test_applies_latency(self, engine_config, pair_rules):
        scenarios = load_stress_scenarios()
        for sc in scenarios:
            new_ec, new_pr = apply_scenario_engine_config(engine_config, pair_rules, sc)
            assert new_ec.latency_bars == engine_config.latency_bars + sc.latency_bars_add


class TestFoldLocalStress:
    def test_returns_list_of_scores(self, candles, strategy_config, engine_config, pair_rules):
        scenarios = load_stress_scenarios()
        scores = run_macd_bb_fold_local_stress(
            candles, strategy_config, engine_config, pair_rules,
            bar_interval_seconds=300,
            fold_test_start_idx=200,
            fold_test_end_idx=300,
            scenarios=scenarios[:2],  # just 2 for speed
            objective_version=2,
        )
        assert isinstance(scores, list)
        assert len(scores) == 2
        for s in scores:
            assert isinstance(s, float)
