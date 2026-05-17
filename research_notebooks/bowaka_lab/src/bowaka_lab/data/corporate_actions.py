"""Corporate-action helpers: splits, dividends, spin-offs, and raw-vs-split sanity."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

import pandas as pd


def detect_split_anomalies(daily_bars: pd.DataFrame, *, jump_threshold: float = 0.40) -> pd.DataFrame:
    """Flag suspicious overnight gaps that may indicate an unadjusted split.

    Returns a DataFrame with columns ``symbol``, ``session_date``, ``gap_pct``,
    ``flag_reason`` for rows where the open-to-prev-close gap exceeds
    ``jump_threshold`` (default ±40%) — well outside normal daily moves and a
    strong hint of a split.
    """
    if daily_bars.empty:
        return pd.DataFrame(columns=["symbol", "session_date", "gap_pct", "flag_reason"])
    df = daily_bars.sort_values(["symbol", "timestamp"]).copy()
    df["prev_close"] = df.groupby("symbol")["close"].shift(1)
    df["gap_pct"] = df["open"] / df["prev_close"] - 1.0
    flagged = df[df["gap_pct"].abs() >= jump_threshold].copy()
    flagged["flag_reason"] = "large_overnight_gap"
    flagged["session_date"] = flagged["timestamp"].dt.tz_convert("America/New_York").dt.date
    return flagged[["symbol", "session_date", "gap_pct", "flag_reason"]].reset_index(drop=True)


def compare_raw_vs_split(raw_bars: pd.DataFrame, split_bars: pd.DataFrame) -> pd.DataFrame:
    """Compute per-symbol ratio between raw and split-adjusted close.

    Used as a sanity check that the split-adjustment vendor agrees with our
    own split-derived adjustments. Returns one row per (symbol, session_date).
    """
    if raw_bars.empty or split_bars.empty:
        return pd.DataFrame(columns=["symbol", "session_date", "raw_close", "split_close", "ratio"])
    raw = raw_bars.rename(columns={"close": "raw_close"})[["symbol", "timestamp", "raw_close"]]
    split = split_bars.rename(columns={"close": "split_close"})[["symbol", "timestamp", "split_close"]]
    merged = raw.merge(split, on=["symbol", "timestamp"], how="inner")
    merged["ratio"] = merged["split_close"] / merged["raw_close"]
    merged["session_date"] = merged["timestamp"].dt.tz_convert("America/New_York").dt.date
    return merged[["symbol", "session_date", "raw_close", "split_close", "ratio"]]


def fetch_corporate_actions(
    fetcher: Callable[[str, date, date], list[dict[str, Any]]],
    *,
    symbols: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """Generic corporate-action fetcher.

    ``fetcher`` is a callable(symbol, start, end) returning a list of records like
    ``{"type": "split", "ex_date": "2026-03-01", "ratio": 0.1}``. The Alpaca SDK
    path lives in the caller; this module stays vendor-neutral so the
    counterfactual engine can plug in fixtures.
    """
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        for ev in fetcher(symbol, start, end):
            rows.append({"symbol": symbol, **ev})
    if not rows:
        return pd.DataFrame(columns=["symbol", "type", "ex_date", "ratio", "amount"])
    return pd.DataFrame(rows)
