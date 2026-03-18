"""Tests for correct trade accounting when trades fail to close."""
import numpy as np
import pytest
from pmm_lab.metrics.metrics import compute_metrics, Metrics
from pmm_lab.sim.executor_model import SimResult, Trade


def _make_trade(trade_id, side="buy", entry_price=100.0, quantity=0.01,
                exit_price=None, pnl_quote=None, entry_bar=0, entry_timestamp=0,
                exit_bar=None, exit_timestamp=None, exit_type=None,
                fee_quote=0.001, entry_fee_quote=0.001, exit_fee_quote=0.0):
    return Trade(
        trade_id=trade_id, side=side, entry_price=entry_price,
        quantity=quantity, entry_bar=entry_bar, entry_timestamp=entry_timestamp,
        exit_price=exit_price, exit_bar=exit_bar, exit_timestamp=exit_timestamp,
        exit_type=exit_type, pnl_quote=pnl_quote, fee_quote=fee_quote,
        entry_fee_quote=entry_fee_quote, exit_fee_quote=exit_fee_quote,
    )


def _make_sim_result(trades, n_bars=100):
    return SimResult(
        trades=trades,
        equity_curve=np.full(n_bars, 100.0),
        position_history=np.zeros(n_bars),
        n_orders_placed=len(trades),
        n_orders_filled=len(trades),
        n_orders_rejected=0,
        n_market_exits=0,
        final_base_balance=0.0,
        final_quote_balance=100.0,
    )


def _make_candles(n, interval_s=300):
    """Create minimal synthetic candles for metrics computation."""
    ts_start = 1000000
    timestamps = np.arange(ts_start, ts_start + n * interval_s, interval_s, dtype="int64")
    close = np.full(n, 100.0)
    close[n // 2:] = 101.0  # small price move to get non-zero returns
    return np.array(
        [(timestamps[i], close[i], close[i] + 0.5, close[i] - 0.5, close[i],
          1000.0 + i, False) for i in range(n)],
        dtype=[("timestamp", "int64"), ("open", "float64"), ("high", "float64"),
               ("low", "float64"), ("close", "float64"), ("volume", "float64"),
               ("is_forward_fill", "bool")],
    )


class TestTradeAccountingClosedOnly:
    """trade_count and fill_count must only count closed round trips."""

    def test_unclosed_trades_not_counted(self):
        """Trades with exit_price=None must not be counted in trade_count."""
        closed = _make_trade(0, exit_price=101.0, pnl_quote=0.01,
                             exit_bar=10, exit_timestamp=600, exit_type="take_profit")
        unclosed = _make_trade(1)  # exit_price=None, pnl_quote=None
        result = _make_sim_result([closed, unclosed])
        metrics = compute_metrics(result, initial_equity=100.0,
                                  candles=_make_candles(100), bar_interval_seconds=300)
        assert metrics.trade_count == 1, f"Expected 1 closed trade, got {metrics.trade_count}"
        assert metrics.fill_count == 2, f"Expected 2 fills, got {metrics.fill_count}"

    def test_all_unclosed_gives_zero_trades(self):
        """If no trades close, trade_count must be 0."""
        t1 = _make_trade(0)
        t2 = _make_trade(1)
        result = _make_sim_result([t1, t2])
        metrics = compute_metrics(result, initial_equity=100.0,
                                  candles=_make_candles(100), bar_interval_seconds=300)
        assert metrics.trade_count == 0
        assert metrics.fill_count == 0

    def test_open_trade_count_field(self):
        """Metrics should report the number of unclosed trades."""
        closed = _make_trade(0, exit_price=101.0, pnl_quote=0.01,
                             exit_bar=5, exit_timestamp=300, exit_type="take_profit")
        unclosed1 = _make_trade(1)
        unclosed2 = _make_trade(2)
        result = _make_sim_result([closed, unclosed1, unclosed2])
        metrics = compute_metrics(result, initial_equity=100.0,
                                  candles=_make_candles(100), bar_interval_seconds=300)
        assert metrics.open_trade_count == 2

    def test_win_loss_stats_exclude_unclosed(self):
        """Win/loss statistics must only consider closed trades."""
        winner = _make_trade(0, exit_price=105.0, pnl_quote=0.05,
                             exit_bar=5, exit_timestamp=300, exit_type="take_profit")
        loser = _make_trade(1, exit_price=98.0, pnl_quote=-0.02,
                            exit_bar=10, exit_timestamp=600, exit_type="stop_loss")
        unclosed = _make_trade(2)  # should NOT affect win/loss
        result = _make_sim_result([winner, loser, unclosed])
        metrics = compute_metrics(result, initial_equity=100.0,
                                  candles=_make_candles(100), bar_interval_seconds=300)
        assert metrics.trade_count == 2  # only closed
        assert metrics.n_winning == 1
        assert metrics.n_losing == 1
