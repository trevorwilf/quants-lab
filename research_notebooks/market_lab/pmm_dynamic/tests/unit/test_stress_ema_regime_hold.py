"""Basic tests for EMA regime-hold stress runner."""

from dataclasses import replace

import numpy as np

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.objective.stress_ema_regime_hold import run_ema_regime_hold_fold_local_stress
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
from tests.conftest import CANDLE_DTYPE


def _make_fast(n=800):
    rng = np.random.default_rng(seed=61)
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


def _make_slow(n=80):
    rng = np.random.default_rng(seed=67)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.8, 1.0)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.6))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.6))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 5.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_stress_returns_scores():
    fast = _make_fast()
    slow = _make_slow()

    base_cfg = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=20,
        regime_adx_length=14, regime_adx_threshold=0.0,
        volume_filter_window=48, min_volume_quantile=0.0,
    )
    strategy_config = replace(base_cfg, _regime_candles=slow)

    engine_config = EngineConfig(total_amount_quote=100.0, executor_refresh_time=300.0)
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    scores = run_ema_regime_hold_fold_local_stress(
        candles=fast,
        strategy_config=strategy_config,
        engine_config=engine_config,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        fold_test_start_idx=200,
        fold_test_end_idx=700,
        regime_candles=slow,
    )
    assert len(scores) > 0
    for s in scores:
        assert np.isfinite(s)
