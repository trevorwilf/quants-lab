"""Daily PnL, equity curve, drawdown, gross exposure."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd


def daily_pnl(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["trade_date", "pnl"])
    df = trades.copy()
    if "trade_date" not in df.columns and "exit_time" in df.columns:
        df["trade_date"] = pd.to_datetime(df["exit_time"]).dt.date
    grouped = df.groupby("trade_date")["pnl"].sum().reset_index()
    return grouped


def equity_curve(daily: pd.DataFrame, *, starting_capital: float = 100_000.0) -> pd.DataFrame:
    if daily.empty:
        return pd.DataFrame(columns=["trade_date", "equity", "cumulative_pnl"])
    df = daily.sort_values("trade_date").copy()
    df["cumulative_pnl"] = df["pnl"].cumsum()
    df["equity"] = starting_capital + df["cumulative_pnl"]
    return df


def drawdown_stats(equity_df: pd.DataFrame) -> dict:
    if equity_df.empty:
        return {"max_drawdown_pct": 0.0, "max_drawdown_dollars": 0.0}
    eq = equity_df["equity"].astype(float)
    running_max = eq.cummax()
    dd_dollars = (eq - running_max).min()
    dd_pct = ((eq / running_max) - 1.0).min()
    return {
        "max_drawdown_pct": float(dd_pct),
        "max_drawdown_dollars": float(dd_dollars),
    }


def exposure_summary(positions: pd.DataFrame) -> dict:
    if positions.empty:
        return {"max_open_positions": 0, "max_gross_notional": 0.0}
    if "open_count" in positions.columns:
        return {
            "max_open_positions": int(positions["open_count"].max()),
            "max_gross_notional": float(positions.get("gross_notional", pd.Series([0.0])).max()),
        }
    return {"max_open_positions": int(positions.shape[0]), "max_gross_notional": float(positions.get("notional", pd.Series([0.0])).sum())}
