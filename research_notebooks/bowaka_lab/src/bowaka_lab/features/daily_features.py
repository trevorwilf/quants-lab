"""Bowaka daily features ported from ``scripts/bowaka_prefilter.py``.

Parity contract (`[Report §11]`):

- Same column names as the legacy script: dollar_volume, avg_dollar_volume,
  avg_volume, rvol, prev_close, atr, atr_pct, gap_pct, range_expansion,
  close_location, ema, ema_distance, ema_lagged, ema_slope.
- Same math: rolling means use ``.shift(1).rolling(N).mean()`` to exclude
  the signal-date bar from its own baseline (no-lookahead invariant).
- EMA via ``ewm(span=N, adjust=False)``.
- range_expansion uses ATR as denominator, not range itself.
- close_location: (close-low)/(high-low), with 0.5 when range is zero.

# parity-note: this function deliberately filters to bars with session_date <=
# signal_date BEFORE computing rolling features. The legacy script trims by
# calendar-day lookback BEFORE compute_features so its rolling window only
# ever sees pre-signal-date bars; the bowaka_lab version makes the truncation
# explicit so callers cannot accidentally pass post-signal bars.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from bowaka_lab.config.models import PrefilterConfig

_EXPECTED_COLUMNS = ("symbol", "open", "high", "low", "close", "volume")


def _resolve_session_date(df: pd.DataFrame) -> pd.Series:
    if "session_date" in df.columns:
        return pd.to_datetime(df["session_date"]).dt.date
    ts = pd.to_datetime(df["timestamp"])
    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_convert("America/New_York")
    return ts.dt.date


def compute_daily_features(
    bars: pd.DataFrame,
    cfg: PrefilterConfig,
    *,
    signal_date: date | pd.Timestamp,
) -> pd.DataFrame:
    """Compute Bowaka daily features using bars with session_date <= signal_date.

    Returns one row per symbol for the latest bar at or before ``signal_date``.
    Output columns mirror the legacy script's, indexed by ``symbol``.
    """
    if bars.empty:
        return pd.DataFrame()

    for col in _EXPECTED_COLUMNS:
        if col not in bars.columns:
            raise ValueError(f"bars is missing required column {col!r}")

    sd = pd.Timestamp(signal_date).date()
    df = bars.copy()
    df["session_date"] = _resolve_session_date(df)
    df = df[df["session_date"] <= sd].copy()
    if df.empty:
        return pd.DataFrame()

    df = df.sort_values(["symbol", "session_date"]).reset_index(drop=True)
    g = df.groupby("symbol", sort=False)

    lookback = cfg.lookback_days
    atr_n = cfg.atr_days
    ema_n = cfg.ema_days
    slope_lb = cfg.ema_slope_lookback

    df["dollar_volume"] = df["close"] * df["volume"]
    df["avg_dollar_volume"] = g["dollar_volume"].transform(lambda s: s.shift(1).rolling(lookback).mean())
    df["avg_volume"] = g["volume"].transform(lambda s: s.shift(1).rolling(lookback).mean())
    df["rvol"] = df["volume"] / df["avg_volume"]

    df["prev_close"] = g["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - df["prev_close"]).abs(),
            (df["low"] - df["prev_close"]).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr"] = tr.groupby(df["symbol"]).transform(lambda s: s.rolling(atr_n).mean())
    df["atr_pct"] = df["atr"] / df["close"]

    df["gap_pct"] = df["open"] / df["prev_close"] - 1.0
    df["range_expansion"] = (df["high"] - df["low"]) / df["atr"]

    rng = (df["high"] - df["low"]).replace(0, np.nan)
    df["close_location"] = ((df["close"] - df["low"]) / rng).fillna(0.5)

    df["ema"] = g["close"].transform(lambda s: s.ewm(span=ema_n, adjust=False).mean())
    df["ema_distance"] = df["close"] / df["ema"] - 1.0
    df["ema_lagged"] = df.groupby("symbol")["ema"].shift(slope_lb)
    df["ema_slope"] = df["ema"] / df["ema_lagged"] - 1.0

    latest = df.groupby("symbol", sort=False).tail(1).set_index("symbol")
    latest = latest.copy()
    latest["latest_bar_date"] = latest["session_date"]
    assert (latest["latest_bar_date"] <= sd).all()  # no-lookahead invariant
    return latest


def compute_signal_strength(features: pd.DataFrame, cfg: PrefilterConfig) -> pd.Series:
    """Bowaka's signal-strength score (unbounded by default, bounded optional).

    Identical math to ``bowaka_prefilter.py::compute_signal_strength`` so the
    parity test can match exactly when ``cfg.score.bounded=False``.
    """
    score = cfg.score
    if not score.bounded:
        return (
            features["rvol"].fillna(0)
            + features["range_expansion"].fillna(0)
            + features["ema_distance"].fillna(0) * 10
            + features["ema_slope"].fillna(0) * 10
        )
    rvol_term = features["rvol"].fillna(0).clip(upper=score.rvol_score_cap)
    range_term = features["range_expansion"].fillna(0).clip(upper=score.range_score_cap)
    edist_term = features["ema_distance"].fillna(0).clip(upper=score.ema_distance_score_cap) * 10
    eslope_term = features["ema_slope"].fillna(0).clip(upper=score.ema_slope_score_cap) * 10
    s = rvol_term + range_term + edist_term + eslope_term
    if "gap_pct" in features.columns:
        excess = (features["gap_pct"].fillna(0) - score.gap_penalty_above).clip(lower=0)
        s = s - excess
    return s
