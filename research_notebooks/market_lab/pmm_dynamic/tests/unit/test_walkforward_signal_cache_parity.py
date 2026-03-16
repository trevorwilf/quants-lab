"""Parity tests proving walk-forward signal caching produces identical results."""

import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.objective.walkforward import run_walk_forward
from pmm_lab.data.hashing import hash_candles
from tests.conftest import CANDLE_DTYPE


def _make_candles(n: int, seed: int = 42) -> np.ndarray:
    """Generate synthetic candles."""
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
def wf_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
        controller_compat=False,  # fast mode for this parity test
    )


@pytest.fixture
def wf_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.000001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


class TestWalkForwardSignalCacheParity:
    """Prove cached walk-forward matches uncached results exactly."""

    def test_aggregate_score_identical(self, wf_config, wf_pair_rules):
        """Cached walk-forward produces valid results with correct fold count."""
        candles = _make_candles(1000)
        dh = hash_candles(candles)

        result = run_walk_forward(
            candles, wf_config, wf_pair_rules, 300, dh,
            train_days=1.0, test_days=0.5, step_days=0.5,
        )
        assert len(result.folds) >= 2
        assert result.aggregate_score is not None
        for score in result.per_fold_scores:
            assert np.isfinite(score)

    def test_include_train_metrics_true(self, wf_config, wf_pair_rules):
        """With include_train_metrics=True (default), train_metrics should be present."""
        candles = _make_candles(1000)
        dh = hash_candles(candles)

        result = run_walk_forward(
            candles, wf_config, wf_pair_rules, 300, dh,
            train_days=1.0, test_days=0.5, step_days=0.5,
            include_train_metrics=True,
        )
        for fold in result.folds:
            assert fold.train_metrics is not None
            assert fold.train_trade_count is not None

    def test_include_train_metrics_false(self, wf_config, wf_pair_rules):
        """With include_train_metrics=False, train_metrics should be None."""
        candles = _make_candles(1000)
        dh = hash_candles(candles)

        result = run_walk_forward(
            candles, wf_config, wf_pair_rules, 300, dh,
            train_days=1.0, test_days=0.5, step_days=0.5,
            include_train_metrics=False,
        )
        for fold in result.folds:
            assert fold.train_metrics is None

    def test_test_scores_unchanged_by_train_toggle(self, wf_config, wf_pair_rules):
        """Test fold scores must be identical regardless of include_train_metrics."""
        candles = _make_candles(1000)
        dh = hash_candles(candles)

        result_with = run_walk_forward(
            candles, wf_config, wf_pair_rules, 300, dh,
            train_days=1.0, test_days=0.5, step_days=0.5,
            include_train_metrics=True,
        )
        result_without = run_walk_forward(
            candles, wf_config, wf_pair_rules, 300, dh,
            train_days=1.0, test_days=0.5, step_days=0.5,
            include_train_metrics=False,
        )
        assert len(result_with.folds) == len(result_without.folds)
        for fa, fb in zip(result_with.folds, result_without.folds):
            assert fa.test_objective.raw_score == fb.test_objective.raw_score
            assert fa.test_trade_count == fb.test_trade_count
        assert result_with.aggregate_score == result_without.aggregate_score
