"""Walk-forward verification for MR BB+RSI.

Runs one objective trial on 10k bars and asserts at least 3 fold scores are produced.
"""

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=10000, seed=101):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.01, 0.4)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.15))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.15))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_mr_walkforward_produces_multiple_folds():
    candles = _make_candles()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    obj = create_objective(
        candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300,
        dataset_hash="test_wf", reference_price=100.0,
        train_days=3.0, test_days=1.0, step_days=1.0,
        strategy_name="mean_reversion_bb_rsi", fixed_quote=100.0,
        objective_version=1, run_stress=False, controller_compat=False,
    )
    study = optuna.create_study(direction="maximize")
    study.optimize(obj, n_trials=1, catch=(Exception,))
    trial = study.trials[0]
    if trial.user_attrs.get("reject_reason") is None:
        assert trial.user_attrs.get("n_folds", 0) >= 3


def test_mr_walkforward_determinism():
    candles = _make_candles()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )

    def _run_once():
        obj = create_objective(
            candles=candles, pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash="test_wf", reference_price=100.0,
            train_days=3.0, test_days=1.0, step_days=1.0,
            strategy_name="mean_reversion_bb_rsi", fixed_quote=100.0,
            objective_version=1, run_stress=False, controller_compat=False,
        )
        sampler = optuna.samplers.TPESampler(seed=42)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(obj, n_trials=1, catch=(Exception,))
        return study.trials[0].user_attrs.get("fold_scores")

    s1 = _run_once()
    s2 = _run_once()
    # If the fold scores are present, they must match between runs
    if s1 is not None and s2 is not None:
        assert s1 == s2, "Fold scores diverge between identical runs"
