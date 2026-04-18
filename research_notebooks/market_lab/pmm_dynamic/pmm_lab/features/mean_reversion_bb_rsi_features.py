"""
Mean-reversion BB+RSI feature computation.

Must match Hummingbot's `mean_reversion_bb_rsi_v1` controller
`update_processed_data()` signal semantics exactly.

Reference:
  hummingbot/controllers/directional_trading/mean_reversion_bb_rsi_v1.py

Vectorized path (controller_compat=False) is canonical for production.
Sliding-window path (controller_compat=True) exists only to produce
parity fixtures against the live controller's max_records-bounded recompute.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pmm_lab.features.ta_utils_shim import (
    atr_wilder,
    bollinger_percent_b,
    ema,
    rolling_volume_quantile_ok,
    rsi_wilder,
)
from pmm_lab.sim.strategy import SignalOutput


@dataclass(frozen=True)
class MRBBRSIFeatureConfig:
    """MR BB+RSI indicator parameters.

    Defaults match the live controller's Pydantic model defaults.
    `timestamp_mode='open'` (D1) means signals at bar t are computed from
    close[0..t-1] after the shift, which prevents using a close the bot
    cannot yet have observed.
    """

    bb_length: int = 80
    bb_std: float = 2.0
    bbp_entry_threshold: float = 0.20
    rsi_length: int = 14
    rsi_entry_threshold: float = 40.0
    use_trend_filter: bool = True
    trend_ema_length: int = 200
    min_trend_slope: float = 0.0  # fixed at 0.0 per D17
    atr_length: int = 14
    max_atr_pct_for_entry: float = 0.10
    volume_filter_window: int = 288
    min_volume_quantile: float = 0.30
    timestamp_mode: str = "open"
    controller_compat: bool = False  # D9: vectorized by default
    use_numba_kernel: bool = False  # opt-in Numba compiled controller-compat path


def _compute_raw(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    config: MRBBRSIFeatureConfig,
):
    """Compute indicator arrays using the shim TA functions.

    Returns numpy arrays plus a boolean `entry` mask. Callers apply the
    timestamp shift and warmup detection.
    """
    bbp, bb_upper, bb_mid, bb_lower = bollinger_percent_b(close, config.bb_length, config.bb_std)
    rsi = rsi_wilder(close, config.rsi_length)
    atr = atr_wilder(high, low, close, config.atr_length)
    # Controller line 182: df["atr_pct"] = df["atr"] / df["close"].replace(0, np.nan)
    atr_pct = atr / close.replace(0.0, np.nan)
    ema_trend = ema(close, config.trend_ema_length)
    ema_slope = ema_trend.diff()
    volume_ok = rolling_volume_quantile_ok(
        volume, config.volume_filter_window, config.min_volume_quantile
    )

    entry = (
        (bbp <= config.bbp_entry_threshold)
        & (rsi <= config.rsi_entry_threshold)
        & (atr_pct <= config.max_atr_pct_for_entry)
        & volume_ok
    )
    if config.use_trend_filter:
        entry = entry & (ema_slope >= config.min_trend_slope)

    # bbp, rsi, atr_pct are Series with NaN during warmup. ema_slope likewise.
    # Non-finite comparisons in pandas return False, so `entry` is already
    # False during warmup bars for each indicator.

    return (
        bbp.to_numpy(dtype="float64"),
        rsi.to_numpy(dtype="float64"),
        atr_pct.to_numpy(dtype="float64"),
        ema_slope.to_numpy(dtype="float64"),
        volume_ok.to_numpy(dtype="bool"),
        entry.to_numpy(dtype="bool"),
    )


def _compute_vectorized(candles: np.ndarray, config: MRBBRSIFeatureConfig):
    """Full-history vectorized path. Used during search."""
    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    close = pd.Series(candles["close"].astype("float64"))
    volume = pd.Series(candles["volume"].astype("float64"))
    return _compute_raw(high, low, close, volume, config)


def _compute_controller_compat(candles: np.ndarray, config: MRBBRSIFeatureConfig):
    """Sliding-window replay path (for parity fixture generation only).

    At each bar t, recomputes indicators on the max_records-sized window
    ending at t. Replicates the controller's `required_records`-bounded
    buffer behavior.
    """
    # Opt-in Numba compiled path — same bounded-slice semantics, 20-50x faster
    if getattr(config, "use_numba_kernel", False):
        from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE
        if _NUMBA_AVAILABLE:
            from pmm_lab.features._numba_mr_bb_rsi import compute_controller_compat_mr_numba
            return compute_controller_compat_mr_numba(
                highs=candles["high"].astype("float64"),
                lows=candles["low"].astype("float64"),
                closes=candles["close"].astype("float64"),
                volumes=candles["volume"].astype("float64"),
                bb_length=int(config.bb_length),
                bb_std=float(config.bb_std),
                rsi_length=int(config.rsi_length),
                atr_length=int(config.atr_length),
                trend_ema_length=int(config.trend_ema_length),
                bbp_entry_threshold=float(config.bbp_entry_threshold),
                rsi_entry_threshold=float(config.rsi_entry_threshold),
                max_atr_pct_for_entry=float(config.max_atr_pct_for_entry),
                use_trend_filter=bool(config.use_trend_filter),
                min_trend_slope=float(config.min_trend_slope),
                volume_filter_window=int(config.volume_filter_window),
                min_volume_quantile=float(config.min_volume_quantile),
            )
        # Fallback to pandas path if Numba is not installed
    n = len(candles)
    max_records = max(config.bb_length, config.trend_ema_length, config.rsi_length, config.atr_length) + 500

    high_full = pd.Series(candles["high"].astype("float64"))
    low_full = pd.Series(candles["low"].astype("float64"))
    close_full = pd.Series(candles["close"].astype("float64"))
    vol_full = pd.Series(candles["volume"].astype("float64"))

    bbp_arr = np.full(n, np.nan, dtype="float64")
    rsi_arr = np.full(n, np.nan, dtype="float64")
    atrpct_arr = np.full(n, np.nan, dtype="float64")
    slope_arr = np.full(n, np.nan, dtype="float64")
    volok_arr = np.zeros(n, dtype="bool")
    entry_arr = np.zeros(n, dtype="bool")

    # We need enough history for the longest indicator to warm up
    min_len = max(config.bb_length, config.trend_ema_length, config.rsi_length, config.atr_length)

    for t in range(n):
        start = max(0, t - max_records + 1)
        h = high_full.iloc[start:t + 1].reset_index(drop=True)
        l = low_full.iloc[start:t + 1].reset_index(drop=True)
        c = close_full.iloc[start:t + 1].reset_index(drop=True)
        v = vol_full.iloc[start:t + 1].reset_index(drop=True)

        if len(c) < min_len:
            continue

        bbp, _, _, _ = bollinger_percent_b(c, config.bb_length, config.bb_std)
        rsi = rsi_wilder(c, config.rsi_length)
        atr = atr_wilder(h, l, c, config.atr_length)
        atr_pct = atr / c.replace(0.0, np.nan)
        ema_trend = ema(c, config.trend_ema_length)
        ema_slope = ema_trend.diff()
        volume_ok = rolling_volume_quantile_ok(
            v, config.volume_filter_window, config.min_volume_quantile
        )

        bbp_v = float(bbp.iloc[-1]) if not pd.isna(bbp.iloc[-1]) else np.nan
        rsi_v = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else np.nan
        atr_pct_v = float(atr_pct.iloc[-1]) if not pd.isna(atr_pct.iloc[-1]) else np.nan
        slope_v = float(ema_slope.iloc[-1]) if not pd.isna(ema_slope.iloc[-1]) else np.nan
        volok_v = bool(volume_ok.iloc[-1])

        bbp_arr[t] = bbp_v
        rsi_arr[t] = rsi_v
        atrpct_arr[t] = atr_pct_v
        slope_arr[t] = slope_v
        volok_arr[t] = volok_v

        # Entry logic mirrors the controller
        cond = (
            (not np.isnan(bbp_v)) and bbp_v <= config.bbp_entry_threshold
            and (not np.isnan(rsi_v)) and rsi_v <= config.rsi_entry_threshold
            and (not np.isnan(atr_pct_v)) and atr_pct_v <= config.max_atr_pct_for_entry
            and volok_v
        )
        if config.use_trend_filter:
            cond = cond and (not np.isnan(slope_v)) and slope_v >= config.min_trend_slope
        entry_arr[t] = cond

    return bbp_arr, rsi_arr, atrpct_arr, slope_arr, volok_arr, entry_arr


def _shift_array(arr: np.ndarray) -> np.ndarray:
    """Shift numeric array forward by 1, inserting NaN at index 0."""
    shifted = np.roll(arr, 1)
    shifted[0] = np.nan
    return shifted


def _shift_bool(arr: np.ndarray) -> np.ndarray:
    shifted = np.roll(arr, 1)
    shifted[0] = False
    return shifted


def _shift_signal(arr: np.ndarray) -> np.ndarray:
    """Shift signal array forward by 1, inserting 0.0 at index 0."""
    shifted = np.roll(arr, 1)
    shifted[0] = 0.0
    return shifted


def compute_mr_bb_rsi_features(
    candles: np.ndarray,
    config: MRBBRSIFeatureConfig = MRBBRSIFeatureConfig(),
) -> SignalOutput:
    """Compute MR BB+RSI signals from a canonical candle array.

    Parameters
    ----------
    candles : np.ndarray
        Structured candle array (CANDLE_DTYPE).
    config : MRBBRSIFeatureConfig
        Indicator parameters.

    Returns
    -------
    SignalOutput
        data keys: signal, bbp, rsi, atr_pct, ema_slope, volume_ok, close_price, timestamp.
        signal values in {0.0, 1.0}; no -1.0 since the controller is long-only.
    """
    n = len(candles)
    close_price = candles["close"].astype("float64").copy()
    timestamps = candles["timestamp"].astype("int64").copy()

    if config.controller_compat:
        bbp, rsi, atr_pct, ema_slope, volume_ok, entry = _compute_controller_compat(candles, config)
    else:
        bbp, rsi, atr_pct, ema_slope, volume_ok, entry = _compute_vectorized(candles, config)

    signal = entry.astype("float64")

    # Warmup: first bar where all required indicators are finite.
    required_arrays = [bbp, rsi, atr_pct]
    if config.use_trend_filter:
        required_arrays.append(ema_slope)
    warmup_end = n
    for i in range(n):
        if all(not np.isnan(arr[i]) for arr in required_arrays):
            warmup_end = i
            break

    # Zero signal in warmup region (defensive — NaN comparisons should already be False)
    signal[:warmup_end] = 0.0

    # Timestamp alignment — 'open' mode shifts forward by 1 so signal at bar t
    # is computed from close[0..t-1]
    if config.timestamp_mode == "open":
        bbp = _shift_array(bbp)
        rsi = _shift_array(rsi)
        atr_pct = _shift_array(atr_pct)
        ema_slope = _shift_array(ema_slope)
        volume_ok = _shift_bool(volume_ok)
        signal = _shift_signal(signal)
        close_price = _shift_array(close_price)
        # timestamps we leave unshifted — they remain the candle's bar-open time
        warmup_end = warmup_end + 1

    return SignalOutput(
        warmup_end=warmup_end,
        data={
            "signal": signal,
            "bbp": bbp,
            "rsi": rsi,
            "atr_pct": atr_pct,
            "ema_slope": ema_slope,
            "volume_ok": volume_ok.astype("float64"),
            "close_price": close_price,
            "timestamp": timestamps.astype("float64"),
        },
    )
