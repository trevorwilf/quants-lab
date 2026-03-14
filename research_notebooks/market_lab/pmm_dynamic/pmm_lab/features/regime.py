"""
Market regime classification.

Classifies candle windows into regime categories using:
1. Volatility level: NATR above/below median -> high_vol / low_vol
2. Trend strength: abs(total_return) / sum(abs(bar_returns)) -> trending / ranging

These are coarse classifications for fold-level analysis, not trading signals.

Usage:
    regime = classify_regime(candles)
    # regime.volatility = "high_vol" or "low_vol"
    # regime.trend = "trending" or "ranging"
    # regime.label = "high_vol_trending" etc.
"""

import numpy as np
from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeClassification:
    """Regime classification for a candle window."""
    volatility: str          # "high_vol" or "low_vol"
    trend: str               # "trending" or "ranging"
    label: str               # combined, e.g. "high_vol_trending"
    natr_mean: float         # mean NATR over the window
    natr_median: float       # global median NATR (the threshold used)
    efficiency_ratio: float  # |net_move| / sum(|bar_moves|), 0..1
    total_return_pct: float  # close[-1]/close[0] - 1 in percent


def classify_regime(
    candles: np.ndarray,
    natr_threshold: float = None,
    efficiency_threshold: float = 0.30,
    natr_window: int = 14,
) -> RegimeClassification:
    """Classify a candle window into a market regime.

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array for one window.
    natr_threshold : float, optional
        NATR threshold for vol classification. If None, uses window's own median.
    efficiency_threshold : float
        Efficiency ratio threshold. Above = trending, below = ranging.
        Default 0.30 (30% efficiency = trending).
    natr_window : int
        Rolling window for NATR calculation.

    Returns
    -------
    RegimeClassification
    """
    close = candles["close"].astype("float64")
    high = candles["high"].astype("float64")
    low = candles["low"].astype("float64")
    n = len(close)

    if n < natr_window + 1:
        return RegimeClassification(
            volatility="unknown", trend="unknown", label="unknown",
            natr_mean=0.0, natr_median=0.0,
            efficiency_ratio=0.0, total_return_pct=0.0,
        )

    # 1. Compute simple ATR / NATR
    # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close))
    )
    # Rolling mean ATR
    atr = np.convolve(tr, np.ones(natr_window) / natr_window, mode='valid')
    # NATR = ATR / close (as fraction)
    atr_close = close[natr_window - 1:]
    natr = atr / np.where(atr_close > 0, atr_close, 1.0)

    natr_mean = float(np.mean(natr))
    if natr_threshold is None:
        natr_median = float(np.median(natr))
    else:
        natr_median = natr_threshold

    volatility = "high_vol" if natr_mean >= natr_median else "low_vol"

    # 2. Efficiency ratio: |net move| / sum(|bar moves|)
    bar_returns = np.diff(close)
    net_move = abs(close[-1] - close[0])
    sum_abs_moves = np.sum(np.abs(bar_returns))
    efficiency_ratio = net_move / sum_abs_moves if sum_abs_moves > 0 else 0.0

    trend = "trending" if efficiency_ratio >= efficiency_threshold else "ranging"

    # Total return
    total_return_pct = (close[-1] / close[0] - 1.0) * 100.0 if close[0] > 0 else 0.0

    label = f"{volatility}_{trend}"

    return RegimeClassification(
        volatility=volatility,
        trend=trend,
        label=label,
        natr_mean=natr_mean,
        natr_median=natr_median,
        efficiency_ratio=efficiency_ratio,
        total_return_pct=total_return_pct,
    )
