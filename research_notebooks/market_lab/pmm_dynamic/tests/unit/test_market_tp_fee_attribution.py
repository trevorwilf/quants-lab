"""MARKET take-profit exits must be counted as taker fees, not maker.

Validates Fix 2: The engine records exit_fee_type on each Trade, and
metrics uses it for accurate maker/taker attribution.
"""
import numpy as np
import pytest
from tests.conftest import _make_sample_candles_500
from pmm_lab.sim.executor_model import SimConfig, Trade
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.config.params import PairRules, FeeConfig

_RULES = PairRules(
    price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0,
    fees=FeeConfig(maker_fee=0.001, taker_fee=0.005),
)


def _make_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


class TestExitFeeTypeField:
    """Trade must have an exit_fee_type field populated by the engine."""

    def test_field_exists_on_trade(self):
        t = Trade(trade_id=0, side="buy", entry_price=100.0,
                  quantity=1.0, entry_bar=0, entry_timestamp=0)
        assert hasattr(t, 'exit_fee_type')
        assert t.exit_fee_type is None

    def test_engine_sets_exit_fee_type(self):
        """After simulation, closed trades must have exit_fee_type set."""
        candles = _make_sample_candles_500()
        config = _make_config(take_profit=0.005, take_profit_order_type="LIMIT")
        result = CandleSimRunner(config, _RULES).run(candles)
        closed = [t for t in result.trades if t.exit_type is not None]
        for t in closed:
            assert t.exit_fee_type in ("maker", "taker"), \
                f"Trade {t.trade_id} exit_type={t.exit_type} has exit_fee_type={t.exit_fee_type}"


class TestMarketTPFeeAttribution:
    """MARKET TP exits must use taker fees in metrics breakdown."""

    def test_market_tp_counted_as_taker(self):
        candles = _make_sample_candles_500()
        config = _make_config(
            take_profit_order_type="MARKET",
            take_profit=0.005,
        )
        result = CandleSimRunner(config, _RULES).run(candles)
        metrics = compute_metrics(result, 100.0, candles, 300)

        tp_trades = [t for t in result.trades if t.exit_type == "take_profit"]
        if len(tp_trades) == 0:
            pytest.skip("No TP exits generated — cannot validate fee attribution")

        # With MARKET TP, all TP exit fees should be taker.
        # maker_fees should only contain entry fees.
        closed = [t for t in result.trades if t.exit_type is not None]
        total_entry_fees = sum(t.entry_fee_quote for t in closed)
        assert abs(metrics.maker_fees_quote - total_entry_fees) < 1e-8, (
            f"MARKET TP exit fees incorrectly counted as maker: "
            f"maker_fees={metrics.maker_fees_quote}, entry_fees_only={total_entry_fees}"
        )

    def test_limit_tp_counted_as_maker(self):
        candles = _make_sample_candles_500()
        config = _make_config(
            take_profit_order_type="LIMIT",
            take_profit=0.005,
        )
        result = CandleSimRunner(config, _RULES).run(candles)
        metrics = compute_metrics(result, 100.0, candles, 300)

        tp_trades = [t for t in result.trades if t.exit_type == "take_profit"]
        if len(tp_trades) == 0:
            pytest.skip("No TP exits generated — cannot validate fee attribution")

        # With LIMIT TP, TP exit fees should be maker
        closed = [t for t in result.trades if t.exit_type is not None]
        total_entry_fees = sum(t.entry_fee_quote for t in closed)
        tp_exit_fees = sum(t.exit_fee_quote for t in tp_trades)
        expected_maker = total_entry_fees + tp_exit_fees
        assert abs(metrics.maker_fees_quote - expected_maker) < 1e-8, (
            f"LIMIT TP exit fees not counted as maker: "
            f"maker_fees={metrics.maker_fees_quote}, expected={expected_maker}"
        )
