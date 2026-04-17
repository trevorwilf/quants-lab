"""Basic tests for MR BB+RSI stress runner."""

import numpy as np

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.objective.stress_mean_reversion_bb_rsi import run_mr_bb_rsi_fold_local_stress
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.mean_reversion_bb_rsi import (
    MeanReversionBBRSIStrategy,
    MeanReversionBBRSIStrategyConfig,
)
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=800):
    rng = np.random.default_rng(seed=99)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.4)
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


def test_stress_returns_one_score_per_scenario():
    candles = _make_candles()
    strategy_config = MeanReversionBBRSIStrategyConfig(
        bb_length=20, bbp_entry_threshold=0.5,
        rsi_length=14, rsi_entry_threshold=70.0,
        use_trend_filter=False,
        trend_ema_length=50,
        atr_length=14, max_atr_pct_for_entry=1.0,
        volume_filter_window=48, min_volume_quantile=0.0,
        max_trades_per_day=100,
    )
    engine_config = EngineConfig(total_amount_quote=100.0, executor_refresh_time=300.0)
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    scores = run_mr_bb_rsi_fold_local_stress(
        candles=candles,
        strategy_config=strategy_config,
        engine_config=engine_config,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        fold_test_start_idx=200,
        fold_test_end_idx=700,
    )
    assert len(scores) > 0
    # All finite (a numeric score, including REJECT_SCORE = -1000.0)
    for s in scores:
        assert np.isfinite(s)
