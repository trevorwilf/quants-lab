"""End-to-end engine integration for EMA regime-hold strategy."""

from dataclasses import replace

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.ema_regime_hold import (
    EMARegimeHoldStrategy,
    EMARegimeHoldStrategyConfig,
)
from tests.conftest import CANDLE_DTYPE


def _make_trending_fast(n: int = 1500) -> np.ndarray:
    rng = np.random.default_rng(seed=19)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.08, 0.3)  # small positive drift
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.15))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.15))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.3, 3.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_trending_slow(n: int = 150) -> np.ndarray:
    rng = np.random.default_rng(seed=23)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(1.2, 1.5)  # strong positive drift
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.8))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.8))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 10.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_ema_engine_integration_runs_without_error():
    fast = _make_trending_fast()
    slow = _make_trending_slow()

    base = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=20,
        regime_adx_length=14, regime_adx_threshold=0.0,
        volume_filter_window=48, min_volume_quantile=0.0,
        hold_mode="reentry",
    )
    cfg = replace(base, _regime_candles=slow)
    strategy = EMARegimeHoldStrategy(cfg)

    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    engine_config = EngineConfig(
        total_amount_quote=100.0, executor_refresh_time=300.0, cooldown_time=300.0,
        stop_loss=0.05, take_profit=0.03, time_limit=86400,
    )
    engine = SimEngine(engine_config, pair_rules)
    result = engine.run(fast, strategy)

    # Invariants
    assert np.all(np.isfinite(result.equity_curve[1:]))
    assert result.force_close_failures == 0
    for trade in result.trades:
        assert trade.side == "buy"
