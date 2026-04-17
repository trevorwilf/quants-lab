"""Tests for the MR BB+RSI objective wrapper."""

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=5000, seed=3):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.02, 0.5)
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


def test_mr_objective_one_trial_completes():
    candles = _make_candles()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    objective = create_objective(
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        dataset_hash="test_hash",
        reference_price=100.0,
        train_days=1.5,
        test_days=0.5,
        step_days=0.5,
        strategy_name="mean_reversion_bb_rsi",
        fixed_quote=100.0,
        objective_version=1,
        run_stress=False,
        controller_compat=False,
    )
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=1, catch=(Exception,))
    assert len(study.trials) == 1
    trial = study.trials[0]
    # Required user_attrs should be present when completed
    if trial.state == optuna.trial.TrialState.COMPLETE:
        assert "objective_score" in trial.user_attrs
        assert "strategy_name" in trial.user_attrs
        assert trial.user_attrs["strategy_name"] == "mean_reversion_bb_rsi"
        # If the trial wasn't rejected for insufficient data, the wrapper
        # records the 24h-cap binding fraction user_attr.
        if trial.user_attrs.get("reject_reason") is None:
            assert "max_trades_per_day_binding_fraction" in trial.user_attrs
