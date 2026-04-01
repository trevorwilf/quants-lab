"""Tests for MACD-BB walk-forward integration."""

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


@pytest.fixture
def candles():
    return _make_candles()


class TestMACDBBWalkForward:
    def test_generic_runner_produces_sim_result(self, candles):
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
        runner = GenericSimRunner(engine_config, strategy, pair_rules)
        result = runner.run(candles)
        assert isinstance(result, SimResult)
        assert len(result.equity_curve) == len(candles)

    def test_walk_forward_fold_simulation(self, candles):
        """Test that we can slice candles and run fold-style simulation."""
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

        # Pre-compute signals on full array
        full_signals = strategy.compute_signals(candles)

        # Simulate a fold: train 0-300, test 300-400
        test_start = 300
        test_end = 400
        candle_slice = candles[:test_end]

        engine = SimEngine(engine_config, pair_rules)
        sim_result = engine.run_with_signals(
            candle_slice, strategy, full_signals, sim_start_idx=test_start,
        )
        assert isinstance(sim_result, SimResult)
        assert len(sim_result.equity_curve) == test_end

        # Compute metrics on test window
        test_eq = sim_result.equity_curve[test_start:test_end]
        test_candles = candles[test_start:test_end]
        test_trades = [t for t in sim_result.trades if t.entry_bar >= test_start]
        test_sim = SimResult(
            trades=test_trades,
            equity_curve=test_eq,
            position_history=sim_result.position_history[test_start:test_end],
            n_orders_placed=sim_result.n_orders_placed,
            n_orders_filled=sim_result.n_orders_filled,
            n_orders_rejected=sim_result.n_orders_rejected,
            n_market_exits=sim_result.n_market_exits,
            final_base_balance=sim_result.final_base_balance,
            final_quote_balance=sim_result.final_quote_balance,
        )
        metrics = compute_metrics(test_sim, 100.0, test_candles, 300)
        assert metrics is not None

    def test_windowed_fold_simulation_matches_full_slice(self, candles):
        """Windowed fold evaluation should preserve SimEngine outputs exactly."""
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
        full_signals = strategy.compute_signals(candles)

        test_start = 300
        test_end = 400

        # OLD path: simulate full prefix, slice results
        engine = SimEngine(engine_config, pair_rules)
        full_slice_result = engine.run_with_signals(
            candles[:test_end], strategy, full_signals, sim_start_idx=test_start,
        )

        # NEW path: simulate only the test window with bar_index_offset
        engine2 = SimEngine(engine_config, pair_rules)
        windowed_result = engine2.run_with_signals(
            candles[test_start:test_end],
            strategy,
            full_signals.slice(test_start, test_end),
            sim_start_idx=0,
            bar_index_offset=test_start,
        )

        # Equity curves must match
        assert np.allclose(
            full_slice_result.equity_curve[test_start:test_end],
            windowed_result.equity_curve,
            atol=1e-12,
            rtol=0.0,
        )

        # Position history must match
        assert np.allclose(
            full_slice_result.position_history[test_start:test_end],
            windowed_result.position_history,
            atol=1e-12,
            rtol=0.0,
        )

        # Order/fill counts must match
        assert full_slice_result.n_orders_placed == windowed_result.n_orders_placed
        assert full_slice_result.n_orders_filled == windowed_result.n_orders_filled
        assert full_slice_result.n_orders_rejected == windowed_result.n_orders_rejected
        assert full_slice_result.n_market_exits == windowed_result.n_market_exits

        # Trade-level parity
        full_trades = [t for t in full_slice_result.trades if t.entry_bar >= test_start]
        assert len(full_trades) == len(windowed_result.trades)
        for lhs, rhs in zip(full_trades, windowed_result.trades):
            assert lhs.entry_bar == rhs.entry_bar
            assert lhs.exit_bar == rhs.exit_bar
            assert lhs.side == rhs.side
            assert lhs.quantity == pytest.approx(rhs.quantity, abs=1e-12)
            assert lhs.entry_price == pytest.approx(rhs.entry_price, abs=1e-12)
            assert lhs.exit_price == pytest.approx(rhs.exit_price, abs=1e-12)
            assert lhs.pnl_quote == pytest.approx(rhs.pnl_quote, abs=1e-12)
