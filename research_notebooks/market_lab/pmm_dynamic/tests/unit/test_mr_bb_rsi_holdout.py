"""Holdout verification for MR BB+RSI.

Uses the generic `split_holdout` helper; the existing `evaluate_holdout` is
PMM-specific so we run the engine directly on the holdout split.
"""

import numpy as np

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.objective.holdout import split_holdout
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.mean_reversion_bb_rsi import (
    MeanReversionBBRSIStrategy,
    MeanReversionBBRSIStrategyConfig,
)
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=3000):
    rng = np.random.default_rng(seed=113)
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


def test_mr_on_holdout_split():
    candles = _make_candles()
    dev, holdout = split_holdout(candles, holdout_fraction=0.20)
    assert len(dev) > 0
    assert len(holdout) > 0

    strategy = MeanReversionBBRSIStrategy(MeanReversionBBRSIStrategyConfig(
        bb_length=20, bbp_entry_threshold=0.5,
        use_trend_filter=False,
        trend_ema_length=50, atr_length=14, max_atr_pct_for_entry=1.0,
        volume_filter_window=48, min_volume_quantile=0.0,
        max_trades_per_day=100,
    ))
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    engine_config = EngineConfig(
        total_amount_quote=100.0, executor_refresh_time=300.0,
        stop_loss=0.03, take_profit=0.02, time_limit=86400,
    )
    engine = SimEngine(engine_config, pair_rules)
    result = engine.run(holdout, strategy)
    assert np.all(np.isfinite(result.equity_curve[1:]))
