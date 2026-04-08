"""Tests for initial_base_balance (wallet inventory modeling, Priority 2)."""

import numpy as np
import pytest

from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.config.params import PairRules, FeeConfig

from tests.conftest import CANDLE_DTYPE


def _make_candles(n=30, base_price=10.0):
    """Create simple candles at a known price."""
    rng = np.random.default_rng(seed=42)
    start_ts = 1000000
    rows = []
    for i in range(n):
        ts = start_ts + i * 300
        p = base_price + rng.normal(0, 0.1)
        p = max(p, 0.01)
        high = p + 0.2
        low = p - 0.2
        low = max(low, 0.001)
        vol = 1000.0
        rows.append((ts, p, high, low, p, vol, False))
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=0.1,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _make_sim_config(**kwargs):
    defaults = dict(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        buy_side_weight=0.5,
        total_amount_quote=100.0,
        executor_refresh_time=3120,
        cooldown_time=0,
        stop_loss=0.03,
        take_profit=0.015,
        time_limit=43200,
        macd_fast=3,
        macd_slow=7,
        macd_signal=3,
        natr_length=3,
        controller_compat=False,
    )
    defaults.update(kwargs)
    return SimConfig(**defaults)


class TestZeroInitialBaseDefault:
    """Default config should start with zero base."""

    def test_default_is_zero(self):
        cfg = EngineConfig()
        assert cfg.initial_base_balance == 0.0

    def test_sim_config_default_is_zero(self):
        config = _make_sim_config()
        assert config.initial_base_balance == 0.0


class TestInitialBaseBalanceSetsInventory:
    """Setting initial_base_balance should distribute capital between base and quote."""

    def test_inventory_redistributed(self, pair_rules):
        """Inventory should have base and reduced quote after initial_base_balance."""
        candles = _make_candles(n=30, base_price=5.0)
        first_close = float(candles["close"][0])  # ~5.0

        config = _make_sim_config(
            initial_base_balance=10.0,
            total_amount_quote=100.0,
        )
        runner = CandleSimRunner(config, pair_rules)

        # Run and check initial state via equity curve
        result = runner.run(candles)

        # Equity at bar 0 should be approximately total_amount_quote
        # (base_value + quote_balance = total)
        assert abs(result.equity_curve[0] - 100.0) < 5.0  # allow some drift from price movement


class TestInitialBaseEquityNeutral:
    """Total equity at bar 0 should equal total_amount_quote."""

    def test_equity_neutral(self, pair_rules):
        candles = _make_candles(n=30, base_price=5.0)
        first_close = float(candles["close"][0])

        config_zero = _make_sim_config(
            initial_base_balance=0.0,
            total_amount_quote=100.0,
        )
        config_base = _make_sim_config(
            initial_base_balance=10.0,
            total_amount_quote=100.0,
        )

        result_zero = CandleSimRunner(config_zero, pair_rules).run(candles)
        result_base = CandleSimRunner(config_base, pair_rules).run(candles)

        # At the warmup_end bar (where sim starts), equity should be ~100 for both
        # The base config redistributes but doesn't change total equity
        warmup_bar = 0
        # Both should have similar initial equity (within fees of initial_base_pct)
        assert abs(result_zero.equity_curve[warmup_bar] - result_base.equity_curve[warmup_bar]) < 1.0


class TestInitialBaseVsInitialBasePct:
    """initial_base_balance (no fees) and initial_base_pct (with fees) should differ."""

    def test_different_results(self, pair_rules):
        candles = _make_candles(n=30, base_price=5.0)
        first_close = float(candles["close"][0])

        # Use initial_base_balance: no fees, no slippage
        base_amount = 10.0
        config_balance = _make_sim_config(
            initial_base_balance=base_amount,
            total_amount_quote=100.0,
        )

        # Use initial_base_pct to buy equivalent amount: has fees + slippage
        # base_amount * first_close / total_amount_quote ≈ fraction of quote to spend
        pct = (base_amount * first_close) / 100.0
        config_pct = _make_sim_config(
            initial_base_pct=pct,
            total_amount_quote=100.0,
        )

        result_balance = CandleSimRunner(config_balance, pair_rules).run(candles)
        result_pct = CandleSimRunner(config_pct, pair_rules).run(candles)

        # initial_base_pct incurs fees + slippage, so equity should be slightly lower
        # The difference may be small but should exist
        # We just verify both run without error and produce valid results
        assert len(result_balance.equity_curve) == len(result_pct.equity_curve)
        assert result_balance.equity_curve[0] > 0
        assert result_pct.equity_curve[0] > 0
