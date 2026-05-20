"""Per-trade win/loss + R-multiple metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def per_trade_metrics(trades: pd.DataFrame, *, stop_pct: float | None = None) -> pd.DataFrame:
    """Add ``pnl``, ``pnl_pct``, ``win``, ``r_multiple``, ``holding_minutes`` columns."""
    if trades.empty:
        return trades
    df = trades.copy()
    df["pnl"] = (df["exit_price"] - df["entry_price"]) * df["qty"]
    df["pnl_pct"] = df["exit_price"] / df["entry_price"] - 1.0
    df["win"] = df["pnl"] > 0
    if "entry_time" in df.columns and "exit_time" in df.columns:
        df["holding_minutes"] = (
            pd.to_datetime(df["exit_time"]) - pd.to_datetime(df["entry_time"])
        ).dt.total_seconds() / 60.0
    if stop_pct is not None and stop_pct > 0:
        df["r_multiple"] = df["pnl_pct"] / stop_pct
    return df


def summary_stats(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {
            "trade_count": 0,
            "win_count": 0,
            "win_rate": 0.0,
            "mean_pnl_pct": 0.0,
            "median_pnl_pct": 0.0,
            "total_pnl": 0.0,
        }
    pnl_pct = trades["pnl_pct"].dropna() if "pnl_pct" in trades.columns else pd.Series(dtype=float)
    win_count = int((trades["pnl"] > 0).sum()) if "pnl" in trades.columns else 0
    return {
        "trade_count": int(trades.shape[0]),
        "win_count": win_count,
        "win_rate": float(win_count / max(1, trades.shape[0])),
        "mean_pnl_pct": float(pnl_pct.mean()) if not pnl_pct.empty else 0.0,
        "median_pnl_pct": float(pnl_pct.median()) if not pnl_pct.empty else 0.0,
        "total_pnl": float(trades["pnl"].sum()) if "pnl" in trades.columns else 0.0,
    }
