"""Tests for the EMA regime-hold objective wrapper."""

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE


def _make_fast(n=1000, seed=5):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.03, 0.3)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.5))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_slow(n=100, seed=7):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(1.0, 1.3)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.8))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.8))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 8.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_missing_regime_raises_at_creation():
    candles = _make_fast()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    with pytest.raises(ValueError, match="regime_candles"):
        create_objective(
            candles=candles,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash="test",
            reference_price=100.0,
            strategy_name="ema_regime_hold",
            fixed_quote=100.0,
            regime_candles=None,  # explicit missing
        )


def test_ema_objective_one_trial_completes():
    fast = _make_fast()
    slow = _make_slow()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    objective = create_objective(
        candles=fast,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        dataset_hash="test_ema",
        reference_price=100.0,
        train_days=1.5,
        test_days=0.5,
        step_days=0.5,
        strategy_name="ema_regime_hold",
        fixed_quote=100.0,
        objective_version=1,
        run_stress=False,
        controller_compat=False,
        regime_candles=slow,
    )
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=1, catch=(Exception,))
    assert len(study.trials) == 1
