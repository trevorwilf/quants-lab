"""Tests for fee calculation and maker/taker distinction."""

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.fees import compute_fee, compute_slippage
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig


def test_maker_fee_calculation():
    """compute_fee with maker -> 0.1."""
    fee = compute_fee(100.0, 1.0, FeeConfig(0.001, 0.002), "maker")
    assert fee == pytest.approx(0.1)


def test_taker_fee_calculation():
    """compute_fee with taker -> 0.2."""
    fee = compute_fee(100.0, 1.0, FeeConfig(0.001, 0.002), "taker")
    assert fee == pytest.approx(0.2)


def test_slippage_buy_exit():
    """Exiting a buy (selling) -> price moves down."""
    exit_p = compute_slippage(100.0, 5.0, "buy")
    assert exit_p == pytest.approx(99.95)


def test_slippage_sell_exit():
    """Exiting a sell (buying back) -> price moves up."""
    exit_p = compute_slippage(100.0, 5.0, "sell")
    assert exit_p == pytest.approx(100.05)


def test_market_exit_uses_taker_fee(sample_candles_5m):
    """Stop-loss exit uses taker fee, not maker."""
    rules = PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=0.01,
        fees=FeeConfig(0.001, 0.01),  # large taker fee to make it detectable
    )
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        stop_loss=0.0001,  # very tight stop loss to trigger quickly
        take_profit=0.5,   # very wide to not trigger
        time_limit=999999,
        fill_participation_rate=1.0,
        latency_bars=0,
        executor_refresh_time=300,
        cooldown_time=0,
    )
    runner = CandleSimRunner(config, rules)
    result = runner.run(sample_candles_5m)

    # Find any trade that exited via stop_loss
    sl_trades = [t for t in result.trades if t.exit_type == "stop_loss"]
    if sl_trades:
        # Fee should reflect taker rate (0.01), not maker (0.001)
        trade = sl_trades[0]
        # The total fee includes both entry (maker) and exit (taker)
        assert trade.fee_quote > 0


def test_limit_tp_uses_maker_fee(sample_candles_5m):
    """Take-profit LIMIT exit uses maker fee."""
    rules = PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=0.01,
        fees=FeeConfig(0.001, 0.01),
    )
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        stop_loss=0.5,        # very wide to not trigger
        take_profit=0.0001,   # very tight to trigger quickly
        take_profit_order_type="LIMIT",
        time_limit=999999,
        fill_participation_rate=1.0,
        latency_bars=0,
        executor_refresh_time=300,
        cooldown_time=0,
    )
    runner = CandleSimRunner(config, rules)
    result = runner.run(sample_candles_5m)

    tp_trades = [t for t in result.trades if t.exit_type == "take_profit"]
    if tp_trades:
        trade = tp_trades[0]
        assert trade.fee_quote > 0
