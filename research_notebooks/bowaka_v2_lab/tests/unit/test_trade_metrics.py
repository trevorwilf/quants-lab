"""Win rate / hold / exit-mix on a tiny fixture."""
from __future__ import annotations

from bowaka_v2_lab.reports.trade_metrics import exit_mix, hold_duration_distribution, win_rate_summary


_TRADES = [
    {"symbol": "A", "pnl": 100, "entry_date": "2024-09-04", "exit_date": "2024-09-06", "exit_reason": "take_profit"},
    {"symbol": "B", "pnl": -50, "entry_date": "2024-09-04", "exit_date": "2024-09-05", "exit_reason": "stop_loss"},
    {"symbol": "C", "pnl": 25, "entry_date": "2024-09-04", "exit_date": "2024-09-09", "exit_reason": "time_stop"},
]


def test_win_rate() -> None:
    s = win_rate_summary(_TRADES)
    assert s["n_trades"] == 3
    assert abs(s["win_rate"] - (2 / 3)) < 1e-9


def test_hold_duration() -> None:
    df = hold_duration_distribution(_TRADES)
    assert set(df["days_held"]) == {2, 1, 5}


def test_exit_mix() -> None:
    df = exit_mix(_TRADES)
    assert set(df["exit_reason"]) == {"take_profit", "stop_loss", "time_stop"}
