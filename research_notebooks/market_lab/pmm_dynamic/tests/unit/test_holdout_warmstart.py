"""Tests for warm-start holdout evaluation."""

import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.objective.holdout import evaluate_holdout
from tests.conftest import CANDLE_DTYPE


def _make_candles(n: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    start_ts = 1756833000
    interval = 300
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.5)
        open_p = max(price, 1.0)
        close_p = max(price + change, 1.0)
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.3))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.3))
        low_p = max(low_p, 1.0)
        vol = rng.uniform(100, 1000)
        rows.append((start_ts + i * interval, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def holdout_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
        controller_compat=False,
    )


@pytest.fixture
def holdout_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.000001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestHoldoutWarmStart:
    def test_cold_start_backward_compat(self, holdout_config, holdout_rules):
        """Legacy cold-start (no full_candles) still works."""
        candles = _make_candles(200)
        holdout = candles[100:]  # 100 bars — enough for warmup (needs 53)
        candidates = [(holdout_config, 0.5)]

        report = evaluate_holdout(
            holdout_candles=holdout,
            candidate_configs=candidates,
            pair_rules=holdout_rules,
            bar_interval_seconds=300,
            run_stress=False,
        )
        assert len(report.candidates) == 1

    def test_warm_start_produces_result(self, holdout_config, holdout_rules):
        """Warm-start with full_candles produces a valid report."""
        candles = _make_candles(200)
        holdout_start = 150
        holdout = candles[holdout_start:]
        candidates = [(holdout_config, 0.5)]

        report = evaluate_holdout(
            holdout_candles=holdout,
            candidate_configs=candidates,
            pair_rules=holdout_rules,
            bar_interval_seconds=300,
            run_stress=False,
            full_candles=candles,
            holdout_start_idx=holdout_start,
        )
        assert len(report.candidates) == 1

    def test_warm_start_changes_metrics(self, holdout_config, holdout_rules):
        """Warm-start may produce different metrics than cold-start (expected)."""
        candles = _make_candles(300)
        holdout_start = 200
        holdout = candles[holdout_start:]
        candidates = [(holdout_config, 0.5)]

        cold = evaluate_holdout(
            holdout_candles=holdout,
            candidate_configs=candidates,
            pair_rules=holdout_rules,
            bar_interval_seconds=300,
            run_stress=False,
        )
        warm = evaluate_holdout(
            holdout_candles=holdout,
            candidate_configs=candidates,
            pair_rules=holdout_rules,
            bar_interval_seconds=300,
            run_stress=False,
            full_candles=candles,
            holdout_start_idx=holdout_start,
        )
        # Both should produce valid results
        assert len(cold.candidates) == 1
        assert len(warm.candidates) == 1
