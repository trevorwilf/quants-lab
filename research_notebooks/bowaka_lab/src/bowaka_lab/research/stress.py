"""Stress scenarios: high-volatility, low-liquidity, gap-event days."""

from __future__ import annotations

import pandas as pd


def high_vol_sessions(daily_bars: pd.DataFrame, *, quantile: float = 0.95) -> set[pd.Timestamp]:
    if daily_bars.empty:
        return set()
    df = daily_bars.copy()
    df["range_pct"] = (df["high"] - df["low"]) / df["close"].replace(0, pd.NA)
    threshold = df["range_pct"].quantile(quantile)
    return set(df.loc[df["range_pct"] >= threshold, "session_date"].unique().tolist())


def low_liquidity_sessions(daily_bars: pd.DataFrame, *, quantile: float = 0.05) -> set[pd.Timestamp]:
    if daily_bars.empty:
        return set()
    df = daily_bars.copy()
    df["dv"] = df["close"] * df["volume"]
    threshold = df["dv"].quantile(quantile)
    return set(df.loc[df["dv"] <= threshold, "session_date"].unique().tolist())


def gap_event_sessions(daily_bars: pd.DataFrame, *, threshold: float = 0.15) -> set[pd.Timestamp]:
    if daily_bars.empty:
        return set()
    df = daily_bars.sort_values(["symbol", "session_date"]).copy()
    df["prev_close"] = df.groupby("symbol")["close"].shift(1)
    df["gap_pct"] = df["open"] / df["prev_close"] - 1.0
    return set(df.loc[df["gap_pct"].abs() >= threshold, "session_date"].dropna().unique().tolist())


def slice_trades_to_sessions(trades: pd.DataFrame, *, sessions: set) -> pd.DataFrame:
    if trades.empty or not sessions:
        return trades.iloc[0:0]
    return trades[trades["trade_date"].isin(sessions)].copy()
