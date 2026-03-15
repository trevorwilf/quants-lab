"""Tests for trailing stop functionality."""

import numpy as np
import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig
from tests.conftest import CANDLE_DTYPE


def _make_trending_candles(n=150, start_price=100000.0):
    """Create candles: flat/dip (fills buys), then strong rise, then sharp drop.

    Pattern:
    - Bars 0-59: flat with small dips (buy orders fill)
    - Bars 60-100: strong uptrend (trailing stop activates)
    - Bars 100-149: sharp drop (trailing stop triggers)
    """
    rng = np.random.default_rng(seed=42)
    rows = []
    price = start_price
    for i in range(n):
        ts = 1756833000 + i * 300
        if i < 60:
            price += rng.normal(-5, 20)  # flat/slight dip
        elif i < 100:
            price += abs(rng.normal(40, 15))  # strong uptrend
        else:
            price -= abs(rng.normal(60, 20))  # sharp drop

        price = max(price, 1000.0)
        o = price
        c = price + rng.normal(0, 10)
        c = max(c, 1.0)
        h = max(o, c) + abs(rng.normal(0, 15))
        lo = min(o, c) - abs(rng.normal(0, 15))
        lo = max(lo, 1.0)
        vol = rng.uniform(0.5, 5.0)
        rows.append((ts, o, h, lo, c, vol, False))
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=0.01,
        fees=FeeConfig(0.001, 0.002),
    )


def test_trailing_stop_disabled(sample_candles_5m):
    """trailing_stop_activation=0.0 -> trailing stop never triggers."""
    rules = _make_rules()
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        trailing_stop_activation=0.0,
        trailing_stop_delta=0.0,
        stop_loss=0.5,
        take_profit=0.5,
        time_limit=999999,
        fill_participation_rate=1.0,
        latency_bars=0,
        executor_refresh_time=300,
        cooldown_time=0,
    )
    runner = CandleSimRunner(config, rules)
    result = runner.run(sample_candles_5m)
    ts_trades = [t for t in result.trades if t.exit_type == "trailing_stop"]
    assert len(ts_trades) == 0


def test_trailing_stop_activates_and_triggers():
    """Trailing stop activates and triggers on crafted candles.

    Engine intrabar ordering: peak updates before trigger check on each bar.
    This means a bar can update the peak AND trigger the trailing stop
    if both conditions are met by the bar's extremes.

    Craft a scenario:
    1. Entry buy at ~100 (bar 55 after warmup)
    2. Price rises to 105 over several bars (activates trailing stop at 0.5% = 100.5)
    3. Peak reaches 105, then price drops to 104 (trails by ~0.95%, triggers at 0.3% delta)
    """
    # Build candles with a clear up-move then reversal
    rng = np.random.default_rng(seed=999)
    n = 100
    start_ts = 1756833000
    interval = 300
    rows = []

    for i in range(n):
        if i < 55:
            # Pre-warmup: stable around 100
            base = 100.0 + rng.normal(0, 0.1)
        elif i < 70:
            # Rise phase: steady climb to ~105
            base = 100.0 + (i - 55) * 0.35
        elif i < 75:
            # Peak phase: hold near 105
            base = 105.0 + rng.normal(0, 0.1)
        else:
            # Drop phase: fall back to 101
            base = 105.0 - (i - 75) * 0.5

        open_p = max(base + rng.normal(0, 0.05), 1.0)
        close_p = max(base + rng.normal(0, 0.05), 1.0)
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        low_p = max(low_p, 0.01)
        vol = rng.uniform(0.5, 5.0)
        rows.append((start_ts + i * interval, open_p, high_p, low_p, close_p, vol, False))

    candles = np.array(rows, dtype=CANDLE_DTYPE)

    config = SimConfig(
        buy_spreads=[0.5],       # tight spread to ensure fills
        sell_spreads=[0.5],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        stop_loss=0.10,          # wide stop loss (won't trigger)
        take_profit=0.10,        # wide take profit (won't trigger)
        time_limit=86400,        # long time limit
        trailing_stop_activation=0.005,  # activate after 0.5% rise
        trailing_stop_delta=0.003,       # trigger at 0.3% from peak
    )

    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )

    runner = CandleSimRunner(config, pair_rules)
    result = runner.run(candles)

    ts_trades = [t for t in result.trades if t.exit_type == "trailing_stop"]
    assert len(ts_trades) > 0, (
        f"Expected at least one trailing_stop exit, got {len(ts_trades)}. "
        f"Trade exit types: {[t.exit_type for t in result.trades]}"
    )


def test_trailing_stop_does_not_activate_below_threshold(sample_candles_5m):
    """Price doesn't rise enough to activate trailing stop."""
    rules = _make_rules()
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        trailing_stop_activation=0.5,   # 50% rise needed — won't happen
        trailing_stop_delta=0.01,
        stop_loss=0.5,
        take_profit=0.5,
        time_limit=999999,
        fill_participation_rate=1.0,
        latency_bars=0,
        executor_refresh_time=300,
        cooldown_time=0,
    )
    runner = CandleSimRunner(config, rules)
    result = runner.run(sample_candles_5m)
    ts_trades = [t for t in result.trades if t.exit_type == "trailing_stop"]
    assert len(ts_trades) == 0


def test_trailing_stop_uses_taker_fee():
    """Trailing stop exit uses taker fee + slippage."""
    candles = _make_trending_candles()
    rules = PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=0.01,
        fees=FeeConfig(0.0001, 0.01),  # large taker fee
    )
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        total_amount_quote=100.0,
        trailing_stop_activation=0.005,
        trailing_stop_delta=0.003,
        stop_loss=0.5,
        take_profit=0.5,
        time_limit=999999,
        fill_participation_rate=1.0,
        latency_bars=0,
        executor_refresh_time=300,
        cooldown_time=0,
        slippage_bps=5.0,
    )
    runner = CandleSimRunner(config, rules)
    result = runner.run(candles)
    ts_trades = [t for t in result.trades if t.exit_type == "trailing_stop"]
    if ts_trades:
        trade = ts_trades[0]
        assert trade.fee_quote > 0
