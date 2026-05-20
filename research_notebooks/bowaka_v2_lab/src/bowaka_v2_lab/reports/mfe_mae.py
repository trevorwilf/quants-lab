"""MFE / MAE surfaces per-trade."""
from __future__ import annotations

import pandas as pd


def mfe_mae_per_trade(trades: list[dict], daily_bars_by_symbol: dict) -> pd.DataFrame:
    """For each trade, compute the maximum favourable / adverse excursion across
    its holding window using the daily-bar frame for ``trades[i]["symbol"]``.
    """
    rows = []
    for t in trades:
        sym = t["symbol"]
        df = daily_bars_by_symbol.get(sym)
        if df is None or df.empty:
            continue
        df = df.copy()
        df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
        entry = pd.to_datetime(t["entry_date"]).date()
        exit_d = pd.to_datetime(t["exit_date"]).date()
        window = df[(df["session_date"] >= entry) & (df["session_date"] <= exit_d)]
        if window.empty:
            continue
        entry_price = float(t["entry_price"])
        if entry_price <= 0:
            continue
        mfe = (window["high"].max() - entry_price) / entry_price
        mae = (window["low"].min() - entry_price) / entry_price
        rows.append({"symbol": sym, "mfe_pct": mfe, "mae_pct": mae,
                      "pnl": t["pnl"], "exit_reason": t["exit_reason"]})
    return pd.DataFrame(rows)
