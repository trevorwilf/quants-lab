"""Tests for simulation determinism."""

import hashlib
import numpy as np
import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig


def _make_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.6, 0.4],
        sell_amounts_pct=[0.6, 0.4],
        total_amount_quote=100.0,
        stop_loss=0.03,
        take_profit=0.015,
        time_limit=43200,
        fill_participation_rate=1.0,
        latency_bars=0,
        executor_refresh_time=300,
        cooldown_time=0,
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


def _make_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.00001,
        min_notional_quote=0.01,
        fees=FeeConfig(0.001, 0.002),
    )


def _trade_hash(trades):
    """Hash the trade log for comparison."""
    data = ""
    for t in trades:
        data += f"{t.trade_id},{t.side},{t.entry_price},{t.quantity},{t.entry_bar},"
        data += f"{t.exit_price},{t.exit_bar},{t.exit_type},{t.pnl_quote},{t.fee_quote}\n"
    return hashlib.sha256(data.encode()).hexdigest()


def test_same_input_same_output(sample_candles_5m):
    """Two identical runs produce identical results."""
    config = _make_config()
    rules = _make_rules()

    runner1 = CandleSimRunner(config, rules)
    result1 = runner1.run(sample_candles_5m)

    runner2 = CandleSimRunner(config, rules)
    result2 = runner2.run(sample_candles_5m)

    # Same number of trades
    assert len(result1.trades) == len(result2.trades)

    # Same trade details
    for t1, t2 in zip(result1.trades, result2.trades):
        assert t1.trade_id == t2.trade_id
        assert t1.side == t2.side
        assert t1.entry_price == t2.entry_price
        assert t1.quantity == t2.quantity
        assert t1.pnl_quote == t2.pnl_quote

    # Same equity curves
    np.testing.assert_array_equal(result1.equity_curve, result2.equity_curve)


def test_trade_log_hash_stable(sample_candles_5m):
    """Hash of trade log is identical across runs."""
    config = _make_config()
    rules = _make_rules()

    result1 = CandleSimRunner(config, rules).run(sample_candles_5m)
    result2 = CandleSimRunner(config, rules).run(sample_candles_5m)

    assert _trade_hash(result1.trades) == _trade_hash(result2.trades)


def test_different_config_different_output(sample_candles_5m):
    """Changing buy_spreads produces different results."""
    rules = _make_rules()

    config1 = _make_config(buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0])
    config2 = _make_config(buy_spreads=[0.1, 0.2], sell_spreads=[0.1, 0.2])

    result1 = CandleSimRunner(config1, rules).run(sample_candles_5m)
    result2 = CandleSimRunner(config2, rules).run(sample_candles_5m)

    # Different spreads should produce different equity curves
    different = not np.array_equal(result1.equity_curve, result2.equity_curve)
    assert different


def test_seed_everything_makes_simulation_reproducible(sample_candles_5m):
    """seed_everything produces identical sim results across calls."""
    from pmm_lab.utils.reproducibility import seed_everything

    config = _make_config()
    rules = _make_rules()

    seed_everything(42)
    result1 = CandleSimRunner(config, rules).run(sample_candles_5m)

    seed_everything(42)
    result2 = CandleSimRunner(config, rules).run(sample_candles_5m)

    np.testing.assert_array_equal(result1.equity_curve, result2.equity_curve)
    assert _trade_hash(result1.trades) == _trade_hash(result2.trades)
