"""
TA utilities shim — verbatim port of hummingbot/strategy_v2/utils/ta_utils.py.

This module exists so pmm_lab can compute the exact same indicator values
as the live Hummingbot controllers (mean_reversion_bb_rsi_v1,
ema_regime_hold_v1) without taking a dependency on the `hummingbot` package.

Every function here must match the Hummingbot reference semantically.
Parity is validated by tests/unit/test_ta_utils_shim_parity.py.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def ema(series: pd.Series, length: int) -> pd.Series:
    """Exponential moving average, matching pandas ewm with span=length.

    NaN for the first `length - 1` bars (min_periods gate).
    """
    return series.ewm(span=length, adjust=False, min_periods=length).mean()


def rsi_wilder(close: pd.Series, length: int) -> pd.Series:
    """Wilder-smoothed RSI with correct edge-case handling.

    Classical RSI semantics:
      gain > 0 and loss == 0 -> RSI = 100  (all-gain window)
      gain == 0 and loss > 0 -> RSI = 0    (all-loss window)
      gain == 0 and loss == 0 -> RSI = 50  (flat window)

    The naive formula 100 - 100/(1 + gain/loss) produces NaN on all-gain
    and flat windows; this implementation handles those explicitly.
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()

    rs = avg_gain / avg_loss.where(avg_loss > 0.0)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    gain_only = (avg_gain > 0.0) & (avg_loss == 0.0)
    loss_only = (avg_gain == 0.0) & (avg_loss > 0.0)
    flat = (avg_gain == 0.0) & (avg_loss == 0.0)

    rsi = rsi.mask(gain_only, 100.0)
    rsi = rsi.mask(loss_only, 0.0)
    rsi = rsi.mask(flat, 50.0)

    warmup_mask = avg_gain.isna() | avg_loss.isna()
    rsi = rsi.where(~warmup_mask, other=np.nan)

    return rsi


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True range = max(high-low, |high-prev_close|, |low-prev_close|)."""
    prev_close = close.shift(1)
    return pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def atr_wilder(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """Average true range, Wilder-smoothed (EMA with alpha=1/length)."""
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def adx_wilder(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """Wilder's Average Directional Index."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0.0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0.0), down_move, 0.0)

    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    atr = atr_wilder(high, low, close, length)
    plus_di = 100.0 * (plus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr.replace(0.0, np.nan))
    minus_di = 100.0 * (minus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr.replace(0.0, np.nan))
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def bollinger_bands(close: pd.Series, length: int, std: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger bands: (upper, middle, lower). Uses population std (ddof=0)."""
    mid = close.rolling(window=length, min_periods=length).mean()
    sd = close.rolling(window=length, min_periods=length).std(ddof=0)
    upper = mid + std * sd
    lower = mid - std * sd
    return upper, mid, lower


def bollinger_percent_b(close: pd.Series, length: int, std: float) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Bollinger %B = (close - lower) / (upper - lower).

    Returns a 4-tuple: (bbp, upper, mid, lower). Matches the live controller's
    unpacking in update_processed_data.
    """
    upper, mid, lower = bollinger_bands(close, length, std)
    rng = (upper - lower).replace(0.0, np.nan)
    bbp = (close - lower) / rng
    return bbp, upper, mid, lower


def donchian_high(high: pd.Series, length: int) -> pd.Series:
    """Donchian channel high, shifted by 1 to avoid lookahead on the current bar."""
    return high.rolling(window=length, min_periods=length).max().shift(1)


def rolling_volume_quantile_ok(volume: pd.Series, window: int, q: float) -> pd.Series:
    """Return True where current volume >= q-th quantile of the prior `window` bars.

    Warmup bars (where quantile is NaN) return True — this matches the live
    controller's behavior. Do NOT "fix" this; the parity tests depend on it.
    """
    if window <= 0 or q <= 0:
        return pd.Series(True, index=volume.index)
    threshold = volume.rolling(window=window, min_periods=window).quantile(q).shift(1)
    return threshold.isna() | (volume >= threshold)
