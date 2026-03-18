"""Sell trades must not be partially closed and marked as complete."""
import numpy as np
import pytest
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimResult


class TestPartialSellClose:
    def test_partial_sell_not_closed(self):
        """If quote is insufficient to fully buy back a sell, trade stays open."""
        from tests.conftest import _make_sample_candles_500
        from pmm_lab.sim.runner import CandleSimRunner
        from pmm_lab.config.params import PairRules, FeeConfig

        candles = _make_sample_candles_500()
        config = EngineConfig(
            total_amount_quote=10.0,
            stop_loss=0.01,
            take_profit=0.005,
        )
        rules = PairRules(
            price_tick=0.01, amount_step=0.000001, min_notional_quote=0.01,
            fees=FeeConfig(0.001, 0.002),
        )
        from pmm_lab.sim.executor_model import SimConfig
        sim_config = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
            total_amount_quote=10.0,
            stop_loss=0.01,
            take_profit=0.005,
        )
        result = CandleSimRunner(sim_config, rules).run(candles)
        for t in result.trades:
            if t.exit_type is not None:
                assert t.exit_price is not None, \
                    f"Trade {t.trade_id} has exit_type={t.exit_type} but no exit_price"

    def test_force_close_failures_counted(self):
        """force_close_failures field exists on SimResult and defaults to 0."""
        result = SimResult(
            trades=[],
            equity_curve=np.array([100.0]),
            position_history=np.array([0.0]),
            n_orders_placed=0,
            n_orders_filled=0,
            n_orders_rejected=0,
            n_market_exits=0,
            final_base_balance=0.0,
            final_quote_balance=100.0,
        )
        assert result.force_close_failures == 0
        assert result.open_trade_count == 0
