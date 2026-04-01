"""Tests for MACD-BB objective wrapper integration."""

import numpy as np
import optuna
import pytest

from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.config.params import PairRules, FeeConfig
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
def pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


class TestMACDBBObjective:
    def test_creates_callable(self, pair_rules):
        candles = _make_candles(500)
        obj = create_objective(
            candles=candles,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash="test_hash",
            reference_price=100000.0,
            objective_version=2,
            run_stress=False,
            controller_compat=False,
            strategy_name="macd_bb",
        )
        assert callable(obj)

    def test_returns_float_score(self, pair_rules):
        candles = _make_candles(500)
        obj = create_objective(
            candles=candles,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash="test_hash",
            reference_price=100000.0,
            objective_version=2,
            run_stress=False,
            controller_compat=False,
            strategy_name="macd_bb",
            fixed_quote=100.0,
        )
        study = optuna.create_study(direction="maximize")
        study.optimize(obj, n_trials=2, show_progress_bar=False)
        completed = [t for t in study.trials
                     if t.state == optuna.trial.TrialState.COMPLETE]
        # At least some trials should complete (they might get pruned or rejected)
        # Check that score is a float for completed trials
        for t in completed:
            assert isinstance(t.value, float)

    def test_pmm_objective_still_works(self, pair_rules):
        """PMM Dynamic objective should still work with default strategy_name."""
        candles = _make_candles(500)
        obj = create_objective(
            candles=candles,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash="test_hash",
            reference_price=100000.0,
            objective_version=2,
            run_stress=False,
            controller_compat=False,
            # strategy_name defaults to "pmm_dynamic"
        )
        assert callable(obj)
