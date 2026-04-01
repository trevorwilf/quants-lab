"""Tests for MACD-BB holdout validation integration."""

import numpy as np
import pytest

from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.generic_runner import GenericSimRunner
from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.sim.executor_model import SimResult
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


class TestMACDBBHoldout:
    def test_holdout_window_simulation(self):
        """Test that MACD-BB can run on a holdout window."""
        candles = _make_candles(500, seed=77)
        strategy_config = MACDBBStrategyConfig(
            bb_length=20, bb_std=2.0,
            bb_long_threshold=0.2, bb_short_threshold=0.8,
            macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False,
        )
        engine_config = EngineConfig(total_amount_quote=100.0, stop_loss=0.05, take_profit=0.03)
        pair_rules = PairRules(
            price_tick=0.01, amount_step=0.00001,
            min_notional_quote=1.0,
            fees=FeeConfig(0.001, 0.002),
        )
        strategy = MACDBBStrategy(strategy_config)

        # Simulate holdout: use last 100 bars
        holdout_start = 400
        holdout_end = 500

        full_signals = strategy.compute_signals(candles)
        engine = SimEngine(engine_config, pair_rules)
        sim_result = engine.run_with_signals(
            candles, strategy, full_signals, sim_start_idx=holdout_start,
        )

        assert isinstance(sim_result, SimResult)
        holdout_eq = sim_result.equity_curve[holdout_start:holdout_end]
        assert len(holdout_eq) == 100

        holdout_candles = candles[holdout_start:holdout_end]
        holdout_trades = [t for t in sim_result.trades if t.entry_bar >= holdout_start]
        holdout_sim = SimResult(
            trades=holdout_trades,
            equity_curve=holdout_eq,
            position_history=sim_result.position_history[holdout_start:holdout_end],
            n_orders_placed=sim_result.n_orders_placed,
            n_orders_filled=sim_result.n_orders_filled,
            n_orders_rejected=sim_result.n_orders_rejected,
            n_market_exits=sim_result.n_market_exits,
            final_base_balance=sim_result.final_base_balance,
            final_quote_balance=sim_result.final_quote_balance,
        )
        metrics = compute_metrics(holdout_sim, 100.0, holdout_candles, 300)
        assert metrics is not None
        assert not np.isnan(metrics.pnl_pct)
