"""Tests for pmm_lab.objective.walkforward — walk-forward time-series CV."""

import numpy as np
import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.objective.walkforward import TimeSeriesCV, run_walk_forward

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n: int, seed: int = 42) -> np.ndarray:
    """Create n-bar candle array with random walks."""
    rng = np.random.default_rng(seed=seed)
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


@pytest.fixture
def default_config():
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


class TestTimeSeriesCV:
    def test_fold_count(self):
        """1000 bars at 5m interval, train=1d, test=0.5d, step=0.5d → multiple folds."""
        cv = TimeSeriesCV(
            n_bars=1000,
            bar_interval_seconds=300,
            train_days=1.0,
            test_days=0.5,
            step_days=0.5,
            embargo_bars=10,
        )
        folds = cv.get_folds()
        assert len(folds) >= 2

    def test_folds_non_overlapping_test(self):
        """No two folds have overlapping test windows."""
        cv = TimeSeriesCV(
            n_bars=2000,
            bar_interval_seconds=300,
            train_days=1.0,
            test_days=0.5,
            step_days=0.5,
            embargo_bars=10,
        )
        folds = cv.get_folds()
        for i in range(len(folds) - 1):
            assert folds[i].test_end_idx <= folds[i + 1].test_start_idx

    def test_embargo_enforced(self):
        """For each fold, test_start - train_end >= embargo_bars."""
        embargo = 20
        cv = TimeSeriesCV(
            n_bars=2000,
            bar_interval_seconds=300,
            train_days=1.0,
            test_days=0.5,
            step_days=0.5,
            embargo_bars=embargo,
        )
        folds = cv.get_folds()
        for f in folds:
            assert f.test_start_idx - f.train_end_idx >= embargo

    def test_embargo_default_calculation(self):
        """macd_slow=42, natr_length=14 → default embargo = max(42,14)+10 = 52."""
        cv = TimeSeriesCV(
            n_bars=5000,
            bar_interval_seconds=300,
            train_days=1.0,
            test_days=0.5,
            step_days=0.5,
            macd_slow=42,
            natr_length=14,
        )
        assert cv.embargo_bars == 52

    def test_fold_within_bounds(self):
        """All fold indices within [0, n_bars)."""
        n = 2000
        cv = TimeSeriesCV(
            n_bars=n,
            bar_interval_seconds=300,
            train_days=1.0,
            test_days=0.5,
            step_days=0.5,
            embargo_bars=10,
        )
        folds = cv.get_folds()
        for f in folds:
            assert f.train_start_idx >= 0
            assert f.test_end_idx <= n

    def test_too_few_bars_raises(self):
        """n_bars=50 with large windows → ValueError."""
        with pytest.raises(ValueError):
            cv = TimeSeriesCV(
                n_bars=50,
                bar_interval_seconds=300,
                train_days=30.0,
                test_days=14.0,
                step_days=14.0,
            )
            cv.get_folds()


class TestRunWalkForward:
    def test_walk_forward_deterministic(self, default_config, default_pair_rules):
        """Run twice with same inputs → identical results."""
        candles = _make_candles(1500)
        result1 = run_walk_forward(
            candles, default_config, default_pair_rules, 300, "hash1",
            train_days=1.0, test_days=0.5, step_days=0.5, embargo_bars=10,
        )
        result2 = run_walk_forward(
            candles, default_config, default_pair_rules, 300, "hash1",
            train_days=1.0, test_days=0.5, step_days=0.5, embargo_bars=10,
        )
        assert result1.aggregate_score == result2.aggregate_score
        assert result1.per_fold_scores == result2.per_fold_scores

    def test_walk_forward_produces_metrics(self, default_config, default_pair_rules):
        """Walk-forward → every FoldResult has non-None test_metrics and test_objective."""
        candles = _make_candles(1500)
        result = run_walk_forward(
            candles, default_config, default_pair_rules, 300, "hash1",
            train_days=1.0, test_days=0.5, step_days=0.5, embargo_bars=10,
        )
        assert len(result.folds) >= 2
        for fold in result.folds:
            assert fold.test_metrics is not None
            assert fold.test_objective is not None
