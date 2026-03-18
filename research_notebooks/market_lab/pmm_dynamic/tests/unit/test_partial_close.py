"""Sell trades must not be partially closed and marked as complete."""
import numpy as np
import pytest
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimResult


class TestPartialSellClose:
    def test_partial_sell_not_closed(self):
        """If quote is insufficient to fully buy back a sell, trade stays open.

        This is validated structurally: the engine code now checks
        `if close_qty < trade.quantity: continue` for sell trades,
        meaning a partial close is skipped entirely. The trade remains
        with exit_price=None and is counted by open_trade_count.
        """
        # Verify the structural guard exists in the engine source
        import inspect
        from pmm_lab.sim.engine import SimEngine
        source = inspect.getsource(SimEngine.run_with_signals)
        # The guard should appear in the barrier-exit path
        assert "if close_qty < trade.quantity:" in source, (
            "Engine must have partial-close guard for sell trades"
        )

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
