"""Intraday-feature computation for signal-fade scoring."""

from __future__ import annotations

import pandas as pd


def vwap(bars: pd.DataFrame) -> pd.Series:
    """Per-symbol cumulative VWAP across the session.

    Expected columns: symbol, timestamp, high, low, close, volume.
    Returns one VWAP value per row (running through the bar).
    """
    if bars.empty:
        return pd.Series(dtype=float)
    typical = (bars["high"] + bars["low"] + bars["close"]) / 3.0
    pv = typical * bars["volume"]
    if "symbol" in bars.columns:
        cum_pv = pv.groupby(bars["symbol"]).cumsum()
        cum_v = bars["volume"].groupby(bars["symbol"]).cumsum()
    else:
        cum_pv = pv.cumsum()
        cum_v = bars["volume"].cumsum()
    return cum_pv / cum_v.replace(0, pd.NA)


def rolling_rvol(bars: pd.DataFrame, window_minutes: int = 30, baseline_volume: pd.Series | None = None) -> pd.Series:
    """Last-window rolling RVOL.

    If ``baseline_volume`` is provided (e.g. avg same-time-of-day intraday volume
    for the symbol), the result is ``window_volume / baseline_volume_window``.
    Otherwise it's ``window_volume / mean_volume_so_far`` so callers can compare
    late-day to morning-baseline volumes.
    """
    if bars.empty:
        return pd.Series(dtype=float)
    if "symbol" in bars.columns:
        window_vol = bars.groupby("symbol")["volume"].transform(lambda s: s.rolling(window_minutes, min_periods=1).sum())
        cum_vol = bars.groupby("symbol")["volume"].transform("cumsum")
        cum_count = bars.groupby("symbol").cumcount() + 1
        baseline_vol = cum_vol / cum_count * window_minutes
    else:
        window_vol = bars["volume"].rolling(window_minutes, min_periods=1).sum()
        cum_vol = bars["volume"].cumsum()
        baseline_vol = cum_vol / (pd.Series(range(1, len(bars) + 1), index=bars.index)) * window_minutes
    if baseline_volume is not None:
        baseline_vol = baseline_volume.reindex(bars.index).fillna(baseline_vol)
    return window_vol / baseline_vol.replace(0, pd.NA)


def short_ema_distance(bars: pd.DataFrame, span: int = 20) -> pd.Series:
    """Distance of close from a short intraday EMA (close / ema - 1)."""
    if bars.empty:
        return pd.Series(dtype=float)
    if "symbol" in bars.columns:
        ema = bars.groupby("symbol")["close"].transform(lambda s: s.ewm(span=span, adjust=False).mean())
    else:
        ema = bars["close"].ewm(span=span, adjust=False).mean()
    return bars["close"] / ema - 1.0


def session_extrema(bars: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol running session high/low up to and including each bar."""
    if bars.empty:
        return pd.DataFrame()
    if "symbol" in bars.columns:
        running_high = bars.groupby("symbol")["high"].transform("cummax")
        running_low = bars.groupby("symbol")["low"].transform("cummin")
    else:
        running_high = bars["high"].cummax()
        running_low = bars["low"].cummin()
    return pd.DataFrame({"running_high": running_high, "running_low": running_low})
