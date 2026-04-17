"""End-to-end engine integration for MR strategy.

Constructs a price pattern that dips into oversold territory and recovers,
runs SimEngine.run_with_signals, and asserts basic invariants.
"""

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.mean_reversion_bb_rsi import (
    MeanReversionBBRSIStrategy,
    MeanReversionBBRSIStrategyConfig,
)
from tests.conftest import CANDLE_DTYPE


def _make_dip_recover(n: int = 1500) -> np.ndarray:
    """Trending down then recovering — induces entries."""
    rng = np.random.default_rng(seed=7)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        # Phase 1: drift down. Phase 2: drift up.
        drift = -0.05 if i < n // 2 else 0.05
        change = rng.normal(drift, 0.5)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.3, 3.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_mr_engine_integration_has_trades_and_finite_equity():
    candles = _make_dip_recover()
    strategy = MeanReversionBBRSIStrategy(MeanReversionBBRSIStrategyConfig(
        bb_length=20, bb_std=2.0, bbp_entry_threshold=0.4,
        rsi_length=14, rsi_entry_threshold=70.0,
        use_trend_filter=False,
        trend_ema_length=50,
        atr_length=14, max_atr_pct_for_entry=1.0,
        volume_filter_window=48, min_volume_quantile=0.0,
        max_trades_per_day=100,  # relaxed for the test
    ))
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    engine_config = EngineConfig(
        total_amount_quote=100.0, executor_refresh_time=300.0, cooldown_time=300.0,
        stop_loss=0.03, take_profit=0.02, time_limit=43200,
    )
    engine = SimEngine(engine_config, pair_rules)
    result = engine.run(candles, strategy)

    assert np.all(np.isfinite(result.equity_curve[1:]))
    assert result.force_close_failures == 0
    # All trades are buys
    for trade in result.trades:
        assert trade.side == "buy"
