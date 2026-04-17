"""Walk-forward verification for EMA regime-hold."""

import numpy as np
import optuna

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE


def _make_fast(n=10000, seed=103):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.02, 0.3)
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


def _make_slow(n=500, seed=107):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.6, 1.2)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.6))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.6))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 8.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_ema_walkforward_produces_multiple_folds():
    fast = _make_fast()
    slow = _make_slow()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    obj = create_objective(
        candles=fast, pair_rules=pair_rules,
        bar_interval_seconds=300,
        dataset_hash="test_wf_ema", reference_price=100.0,
        train_days=3.0, test_days=1.0, step_days=1.0,
        strategy_name="ema_regime_hold", fixed_quote=100.0,
        objective_version=1, run_stress=False, controller_compat=False,
        regime_candles=slow,
    )
    study = optuna.create_study(direction="maximize")
    study.optimize(obj, n_trials=1, catch=(Exception,))
    trial = study.trials[0]
    if trial.user_attrs.get("reject_reason") is None:
        assert trial.user_attrs.get("n_folds", 0) >= 3
