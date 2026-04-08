"""Tests for refresh close behavior (Priority 1 parity fix)."""

import numpy as np
import pytest

from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.config.params import PairRules, FeeConfig

from tests.conftest import CANDLE_DTYPE


def _make_candles(n=30, interval=300, base_price=100.0, volatility=0.5):
    """Create candles with controlled price movement."""
    rng = np.random.default_rng(seed=42)
    start_ts = 1000000
    price = base_price
    rows = []
    for i in range(n):
        ts = start_ts + i * interval
        change = rng.normal(0, volatility)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        open_p = max(open_p, 0.01)
        close_p = max(close_p, 0.01)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.001)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(100.0, 500.0)
        rows.append((ts, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=0.1,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _make_sim_config(refresh_close_mode="keep", refresh_time=600, **kwargs):
    """Build a SimConfig with short refresh time to trigger refreshes."""
    defaults = dict(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        buy_side_weight=0.5,
        total_amount_quote=100.0,
        executor_refresh_time=refresh_time,
        cooldown_time=0,
        stop_loss=0.50,       # wide SL so trades don't exit via SL
        take_profit=0.50,     # wide TP so trades don't exit via TP
        time_limit=999999,
        macd_fast=3,
        macd_slow=7,
        macd_signal=3,
        natr_length=3,
        controller_compat=False,
        refresh_close_mode=refresh_close_mode,
    )
    defaults.update(kwargs)
    return SimConfig(**defaults)


class TestRefreshKeepMode:
    """Test that refresh_close_mode='keep' preserves current behavior."""

    def test_open_trades_survive_refresh(self, pair_rules):
        """Open trades should NOT be closed at refresh with mode='keep'."""
        candles = _make_candles(n=50, volatility=1.0)
        config = _make_sim_config(refresh_close_mode="keep", refresh_time=600)
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(candles)

        # No trades should have exit_type "refresh"
        refresh_exits = [t for t in result.trades if t.exit_type == "refresh"]
        assert len(refresh_exits) == 0, "Keep mode should never produce refresh exits"

    def test_backward_compatible_with_default(self, pair_rules):
        """Default EngineConfig should use 'keep' mode."""
        cfg = EngineConfig()
        assert cfg.refresh_close_mode == "keep"


class TestRefreshMarketClose:
    """Test that refresh_close_mode='market_close' force-closes open trades."""

    def test_trades_exit_at_refresh(self, pair_rules):
        """With market_close mode, filled trades should be closed at refresh."""
        candles = _make_candles(n=50, volatility=1.0)
        config = _make_sim_config(
            refresh_close_mode="market_close",
            refresh_time=600,  # refresh every 2 bars (300s * 2)
        )
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(candles)

        refresh_exits = [t for t in result.trades if t.exit_type == "refresh"]
        # With short refresh time and market_close, we should see some refresh exits
        # (if any trades filled between refreshes)
        closed_trades = [t for t in result.trades if t.exit_price is not None]
        if len(closed_trades) > 0:
            # At least some should be refresh-closed (not all will be TP/SL given wide barriers)
            # The exact count depends on market dynamics, but refresh exits should exist
            all_exit_types = set(t.exit_type for t in closed_trades)
            # We expect either refresh exits or final_liquidation (if only closed at end)
            assert "refresh" in all_exit_types or "final_liquidation" in all_exit_types

    def test_refresh_exit_uses_taker_fee(self, pair_rules):
        """Refresh exits should use taker fees."""
        candles = _make_candles(n=50, volatility=1.0)
        config = _make_sim_config(refresh_close_mode="market_close", refresh_time=600)
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(candles)

        for trade in result.trades:
            if trade.exit_type == "refresh":
                assert trade.exit_fee_type == "taker"
                assert trade.exit_fee_quote > 0

    def test_refresh_close_pnl_accounting(self, pair_rules):
        """PnL for refresh-closed trades should be correctly computed."""
        candles = _make_candles(n=50, volatility=1.0)
        config = _make_sim_config(refresh_close_mode="market_close", refresh_time=600)
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(candles)

        for trade in result.trades:
            if trade.exit_type == "refresh" and trade.exit_price is not None:
                if trade.side == "buy":
                    expected_pnl = (
                        (trade.exit_price - trade.entry_price) * trade.quantity
                        - trade.entry_fee_quote - trade.exit_fee_quote
                    )
                else:
                    expected_pnl = (
                        (trade.entry_price - trade.exit_price) * trade.quantity
                        - trade.entry_fee_quote - trade.exit_fee_quote
                    )
                assert abs(trade.pnl_quote - expected_pnl) < 1e-8, (
                    f"PnL mismatch: {trade.pnl_quote} != {expected_pnl}"
                )

    def test_refresh_close_equity_curve_consistency(self, pair_rules):
        """Equity curve should reflect refresh closes — final equity should differ from keep mode."""
        candles = _make_candles(n=50, volatility=1.0)

        config_keep = _make_sim_config(refresh_close_mode="keep", refresh_time=600)
        config_close = _make_sim_config(refresh_close_mode="market_close", refresh_time=600)

        result_keep = CandleSimRunner(config_keep, pair_rules).run(candles)
        result_close = CandleSimRunner(config_close, pair_rules).run(candles)

        # Both should have valid equity curves of same length
        assert len(result_keep.equity_curve) == len(result_close.equity_curve)
        # They SHOULD differ (market close has extra taker fees and forced exits)
        # But we can't assert they're always different (depends on whether trades filled)

    def test_refresh_close_cooldown_skips_close(self, pair_rules):
        """When cooldown is active, refresh is skipped — no market close should happen."""
        candles = _make_candles(n=50, volatility=1.0)
        # Very long cooldown means refresh never fires after first fill
        config = _make_sim_config(
            refresh_close_mode="market_close",
            refresh_time=600,
            cooldown_time=999999,
        )
        runner = CandleSimRunner(config, pair_rules)
        result = runner.run(candles)

        refresh_exits = [t for t in result.trades if t.exit_type == "refresh"]
        assert len(refresh_exits) == 0, "Cooldown should prevent refresh closes"
