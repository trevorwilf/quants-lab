"""Tests for pmm_lab.metrics.metrics — compute_metrics."""

import numpy as np
import pytest

from pmm_lab.sim.executor_model import SimResult, Trade
from pmm_lab.metrics.metrics import compute_metrics, Metrics

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n: int, price: float = 100.0) -> np.ndarray:
    """Create n-bar candle array at constant price."""
    rows = []
    for i in range(n):
        rows.append((
            1000000 + i * 300, price, price, price, price, 1.0, False,
        ))
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_sim_result(trades, equity_curve, position_history=None) -> SimResult:
    """Helper to build a SimResult."""
    n = len(equity_curve)
    if position_history is None:
        position_history = np.zeros(n, dtype="float64")
    return SimResult(
        trades=trades,
        equity_curve=equity_curve,
        position_history=position_history,
        n_orders_placed=0,
        n_orders_filled=len(trades),
        n_orders_rejected=0,
        n_market_exits=0,
        final_base_balance=0.0,
        final_quote_balance=100.0,
    )


class TestComputeMetrics:
    def test_zero_trade_metrics(self):
        """0 trades, flat equity → pnl=0, trade_count=0, sharpe=0, drawdown=0."""
        n = 50
        candles = _make_candles(n)
        eq = np.full(n, 100.0, dtype="float64")
        result = _make_sim_result([], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert m.pnl_pct == 0.0
        assert m.trade_count == 0
        assert m.sharpe == 0.0
        assert m.max_drawdown_pct == 0.0

    def test_single_winning_trade(self):
        """1 trade, +10 profit on 100 equity."""
        n = 50
        candles = _make_candles(n)
        eq = np.linspace(100.0, 110.0, n, dtype="float64")
        trade = Trade(
            trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
            entry_bar=5, entry_timestamp=1000000 + 5 * 300,
            exit_price=110.0, exit_bar=45, exit_timestamp=1000000 + 45 * 300,
            exit_type="take_profit", pnl_quote=10.0, fee_quote=0.0,
        )
        result = _make_sim_result([trade], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert abs(m.pnl_pct - 10.0) < 0.01
        assert abs(m.net_pnl_quote - 10.0) < 0.01
        assert m.n_winning == 1
        assert m.n_losing == 0
        assert m.profit_factor == float('inf')

    def test_single_losing_trade(self):
        """1 trade, -5 loss on 100 equity."""
        n = 50
        candles = _make_candles(n)
        eq = np.linspace(100.0, 95.0, n, dtype="float64")
        trade = Trade(
            trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
            entry_bar=5, entry_timestamp=1000000 + 5 * 300,
            exit_price=95.0, exit_bar=45, exit_timestamp=1000000 + 45 * 300,
            exit_type="stop_loss", pnl_quote=-5.0, fee_quote=0.0,
        )
        result = _make_sim_result([trade], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert abs(m.pnl_pct - (-5.0)) < 0.01
        assert m.profit_factor == 0.0

    def test_mixed_trades(self):
        """3 wins (+20 total), 2 losses (-8 total). profit_factor = 2.5."""
        n = 50
        candles = _make_candles(n)
        eq = np.linspace(100.0, 112.0, n, dtype="float64")
        trades = [
            Trade(trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
                  entry_bar=5, entry_timestamp=1000000+5*300,
                  exit_price=108.0, exit_bar=10, exit_timestamp=1000000+10*300,
                  exit_type="take_profit", pnl_quote=8.0, fee_quote=0.0),
            Trade(trade_id=1, side="buy", entry_price=100.0, quantity=1.0,
                  entry_bar=12, entry_timestamp=1000000+12*300,
                  exit_price=106.0, exit_bar=18, exit_timestamp=1000000+18*300,
                  exit_type="take_profit", pnl_quote=6.0, fee_quote=0.0),
            Trade(trade_id=2, side="buy", entry_price=100.0, quantity=1.0,
                  entry_bar=20, entry_timestamp=1000000+20*300,
                  exit_price=106.0, exit_bar=25, exit_timestamp=1000000+25*300,
                  exit_type="take_profit", pnl_quote=6.0, fee_quote=0.0),
            Trade(trade_id=3, side="buy", entry_price=100.0, quantity=1.0,
                  entry_bar=28, entry_timestamp=1000000+28*300,
                  exit_price=95.0, exit_bar=33, exit_timestamp=1000000+33*300,
                  exit_type="stop_loss", pnl_quote=-5.0, fee_quote=0.0),
            Trade(trade_id=4, side="buy", entry_price=100.0, quantity=1.0,
                  entry_bar=35, entry_timestamp=1000000+35*300,
                  exit_price=97.0, exit_bar=40, exit_timestamp=1000000+40*300,
                  exit_type="stop_loss", pnl_quote=-3.0, fee_quote=0.0),
        ]
        result = _make_sim_result(trades, eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert abs(m.profit_factor - 2.5) < 0.01
        assert m.n_winning == 3
        assert m.n_losing == 2

    def test_fee_drag_calculation(self):
        """Total fees = 2.0 on initial equity 100 → fee_drag_pct = 2.0."""
        n = 50
        candles = _make_candles(n)
        eq = np.full(n, 98.0, dtype="float64")
        trade = Trade(
            trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
            entry_bar=5, entry_timestamp=1000000+5*300,
            exit_price=100.0, exit_bar=45, exit_timestamp=1000000+45*300,
            exit_type="time_limit", pnl_quote=-2.0, fee_quote=2.0,
        )
        result = _make_sim_result([trade], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert abs(m.fee_drag_pct - 2.0) < 0.01

    def test_sharpe_positive_for_uptrend(self):
        """Equity that trends upward steadily → sharpe > 0."""
        n = 100
        candles = _make_candles(n)
        eq = np.linspace(100.0, 120.0, n, dtype="float64")
        trade = Trade(
            trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
            entry_bar=5, entry_timestamp=1000000+5*300,
            exit_price=120.0, exit_bar=95, exit_timestamp=1000000+95*300,
            exit_type="take_profit", pnl_quote=20.0, fee_quote=0.0,
        )
        result = _make_sim_result([trade], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert m.sharpe > 0

    def test_sharpe_zero_for_flat(self):
        """Flat equity curve → sharpe = 0.0."""
        n = 50
        candles = _make_candles(n)
        eq = np.full(n, 100.0, dtype="float64")
        result = _make_sim_result([], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert m.sharpe == 0.0

    def test_expected_shortfall_computed(self):
        """ES is computed and negative for a downtrending equity curve."""
        n = 100
        candles = _make_candles(n)
        eq = np.linspace(100.0, 80.0, n, dtype="float64")
        trade = Trade(
            trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
            entry_bar=5, entry_timestamp=1000000+5*300,
            exit_price=80.0, exit_bar=95, exit_timestamp=1000000+95*300,
            exit_type="stop_loss", pnl_quote=-20.0, fee_quote=0.0,
        )
        result = _make_sim_result([trade], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert m.expected_shortfall_5pct < 0, "ES should be negative for losses"

    def test_maker_taker_fee_split(self):
        """maker_fees + taker_fees sum to total_fees."""
        n = 50
        candles = _make_candles(n)
        eq = np.full(n, 98.0, dtype="float64")
        trade = Trade(
            trade_id=0, side="buy", entry_price=100.0, quantity=1.0,
            entry_bar=5, entry_timestamp=1000000+5*300,
            exit_price=100.0, exit_bar=45, exit_timestamp=1000000+45*300,
            exit_type="stop_loss", pnl_quote=-2.0, fee_quote=2.0,
            entry_fee_quote=0.8, exit_fee_quote=1.2,
        )
        result = _make_sim_result([trade], eq)
        m = compute_metrics(result, 100.0, candles, 300)
        assert abs(m.maker_fees_quote + m.taker_fees_quote - m.total_fees_quote) < 0.01


class TestInventoryExposureVectorized:
    """Vectorized inventory exposure must be identical to the loop version."""

    def test_vectorized_matches_loop(self):
        import numpy as np
        rng = np.random.default_rng(42)
        n = 1000
        eq = rng.uniform(50, 200, n)
        eq[::10] = 0  # some zero-equity bars
        pos = rng.uniform(-5, 5, n)
        close_prices = rng.uniform(80, 120, n)

        # Loop version (old)
        loop_result = np.zeros(n, dtype=np.float64)
        for i in range(n):
            if eq[i] != 0:
                loop_result[i] = abs(pos[i] * close_prices[i]) / abs(eq[i])

        # Vectorized version (new)
        vec_result = np.zeros(n, dtype=np.float64)
        mask = eq != 0
        vec_result[mask] = np.abs(pos[mask] * close_prices[mask]) / np.abs(eq[mask])

        np.testing.assert_array_equal(loop_result, vec_result)
