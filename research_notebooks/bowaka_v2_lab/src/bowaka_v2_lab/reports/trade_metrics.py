"""Per-trade win rate, hold duration, exit mix, MFE/MAE."""
from __future__ import annotations

import datetime as _dt
from typing import Iterable

import pandas as pd


def win_rate_summary(trades: list[dict]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n_trades": 0, "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0}
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    return {
        "n_trades": n,
        "win_rate": len(wins) / n,
        "avg_win": (sum(t["pnl"] for t in wins) / len(wins)) if wins else 0.0,
        "avg_loss": (sum(t["pnl"] for t in losses) / len(losses)) if losses else 0.0,
    }


def hold_duration_distribution(trades: list[dict]) -> pd.DataFrame:
    rows = []
    for t in trades:
        try:
            entry = _dt.date.fromisoformat(t["entry_date"])
            exit_d = _dt.date.fromisoformat(t["exit_date"])
            rows.append({"symbol": t["symbol"], "days_held": (exit_d - entry).days})
        except Exception:
            continue
    return pd.DataFrame(rows)


def exit_mix(trades: list[dict]) -> pd.DataFrame:
    rows = []
    for t in trades:
        rows.append({"exit_reason": t.get("exit_reason", "unknown"), "pnl": t.get("pnl", 0.0)})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame({"exit_reason": [], "count": [], "avg_pnl": []})
    out = df.groupby("exit_reason").agg(count=("pnl", "count"), avg_pnl=("pnl", "mean")).reset_index()
    return out
