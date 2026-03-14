"""
Parity tests — proves SimEngine + PMMDynamicStrategy produces
byte-identical results to the CandleSimRunner wrapper path.
"""

import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner, _sim_config_to_engine_config
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy
from pmm_lab.config.params import PairRules, FeeConfig


@pytest.fixture
def default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _run_both_paths(config, pair_rules, candles, sim_start_idx=None):
    """Run both CandleSimRunner (wrapper) and direct SimEngine paths."""
    # Path 1: CandleSimRunner wrapper
    result_wrapper = CandleSimRunner(config, pair_rules).run(candles, sim_start_idx=sim_start_idx)

    # Path 2: Direct SimEngine + PMMDynamicStrategy
    engine_config = _sim_config_to_engine_config(config)
    strategy = PMMDynamicStrategy.from_sim_config(config)
    engine = SimEngine(engine_config, pair_rules)
    result_direct = engine.run(candles, strategy, sim_start_idx=sim_start_idx)

    return result_wrapper, result_direct


def _default_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )


class TestParityEquityCurve:
    def test_parity_equity_curve(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)


class TestParityPositionHistory:
    def test_parity_position_history(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        np.testing.assert_array_equal(r1.position_history, r2.position_history)


class TestParityTradeCount:
    def test_parity_trade_count(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        assert len(r1.trades) == len(r2.trades)


class TestParityTradeDetails:
    def test_parity_trade_details(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        assert len(r1.trades) == len(r2.trades)
        for i, (t1, t2) in enumerate(zip(r1.trades, r2.trades)):
            assert abs(t1.entry_price - t2.entry_price) < 1e-12, f"Trade {i} entry_price differs"
            assert abs(t1.quantity - t2.quantity) < 1e-12, f"Trade {i} quantity differs"
            if t1.exit_price is not None:
                assert t2.exit_price is not None, f"Trade {i} exit_price: one is None"
                assert abs(t1.exit_price - t2.exit_price) < 1e-12, f"Trade {i} exit_price differs"
            assert t1.exit_type == t2.exit_type, f"Trade {i} exit_type differs"
            if t1.pnl_quote is not None and t2.pnl_quote is not None:
                assert abs(t1.pnl_quote - t2.pnl_quote) < 1e-12, f"Trade {i} pnl_quote differs"


class TestParityOrderCounts:
    def test_parity_order_counts(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        assert r1.n_orders_placed == r2.n_orders_placed
        assert r1.n_orders_filled == r2.n_orders_filled
        assert r1.n_orders_rejected == r2.n_orders_rejected
        assert r1.n_market_exits == r2.n_market_exits


class TestParityFinalBalances:
    def test_parity_final_balances(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        assert abs(r1.final_base_balance - r2.final_base_balance) < 1e-12
        assert abs(r1.final_quote_balance - r2.final_quote_balance) < 1e-12


class TestParityWithSimStartIdx:
    def test_parity_with_sim_start_idx(self, sample_candles_5m, default_pair_rules):
        config = _default_config()
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m, sim_start_idx=70)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)
        np.testing.assert_array_equal(r1.position_history, r2.position_history)
        assert len(r1.trades) == len(r2.trades)
        assert r1.n_orders_placed == r2.n_orders_placed
        assert r1.n_orders_filled == r2.n_orders_filled


class TestParityWithTrailingStop:
    def test_parity_with_trailing_stop(self, sample_candles_5m, default_pair_rules):
        config = SimConfig(
            buy_spreads=[1.0, 2.0],
            sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5],
            sell_amounts_pct=[0.5, 0.5],
            total_amount_quote=100.0,
            trailing_stop_activation=0.005,
            trailing_stop_delta=0.003,
        )
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_5m)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)
        np.testing.assert_array_equal(r1.position_history, r2.position_history)
        assert len(r1.trades) == len(r2.trades)
        assert r1.n_orders_placed == r2.n_orders_placed
        assert abs(r1.final_base_balance - r2.final_base_balance) < 1e-12
        assert abs(r1.final_quote_balance - r2.final_quote_balance) < 1e-12


class TestParitySampleCandles500:
    def test_parity_sample_candles_500(self, sample_candles_500, default_pair_rules):
        config = SimConfig(
            buy_spreads=[1.0, 2.0, 4.0],
            sell_spreads=[1.0, 2.0, 4.0],
            buy_amounts_pct=[0.33, 0.34, 0.33],
            sell_amounts_pct=[0.33, 0.34, 0.33],
            total_amount_quote=100.0,
        )
        r1, r2 = _run_both_paths(config, default_pair_rules, sample_candles_500)
        np.testing.assert_array_equal(r1.equity_curve, r2.equity_curve)
        np.testing.assert_array_equal(r1.position_history, r2.position_history)
        assert len(r1.trades) == len(r2.trades)
        assert r1.n_orders_placed == r2.n_orders_placed
        assert r1.n_orders_filled == r2.n_orders_filled
        assert r1.n_orders_rejected == r2.n_orders_rejected
        assert r1.n_market_exits == r2.n_market_exits
        assert abs(r1.final_base_balance - r2.final_base_balance) < 1e-12
        assert abs(r1.final_quote_balance - r2.final_quote_balance) < 1e-12

        for i, (t1, t2) in enumerate(zip(r1.trades, r2.trades)):
            assert abs(t1.entry_price - t2.entry_price) < 1e-12, f"Trade {i} entry_price"
            assert abs(t1.quantity - t2.quantity) < 1e-12, f"Trade {i} quantity"
            assert t1.exit_type == t2.exit_type, f"Trade {i} exit_type"
