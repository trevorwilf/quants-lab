"""Numba-compiled port of MR BB+RSI controller-compat feature kernel.

Mirrors `_compute_controller_compat` in `mean_reversion_bb_rsi_features.py`:

    for t in range(n):
        start = max(0, t - max_records + 1)
        slice_high = highs[start:t+1]
        slice_low  = lows[start:t+1]
        slice_close = closes[start:t+1]
        slice_vol  = volumes[start:t+1]
        if len(slice_close) < min_len: continue
        bbp[t]     = bollinger_percent_b(slice_close, bb_length, bb_std).iloc[-1]
        rsi[t]     = rsi_wilder(slice_close, rsi_length).iloc[-1]
        atr[t]     = atr_wilder(slice_high, slice_low, slice_close, atr_length).iloc[-1]
        atr_pct[t] = atr[t] / slice_close[-1]
        ema_slope[t] = ema(slice_close, trend_ema_length).diff().iloc[-1]
        volume_ok[t] = rolling_volume_quantile_ok(...).iloc[-1]
        entry[t]   = (all gates pass)

The kernel calls back into the same Numba indicator primitives as used in
unit tests. The bounded slice semantics must match the pandas replay path
exactly.
"""

from __future__ import annotations

import math

import numpy as np

from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE
from pmm_lab.features._numba_indicators import (
    _atr_wilder_last,
    _bollinger_percent_b_last,
    _ema_diff_last,
    _rolling_volume_quantile_ok_last,
    _rsi_wilder_last,
)

if _NUMBA_AVAILABLE:
    from numba import njit  # type: ignore
else:
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        def _wrap(fn):
            return fn
        return _wrap


@njit(cache=True)
def _run_mr_kernel(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
    bb_length: int,
    bb_std: float,
    rsi_length: int,
    atr_length: int,
    trend_ema_length: int,
    bbp_entry_threshold: float,
    rsi_entry_threshold: float,
    max_atr_pct_for_entry: float,
    use_trend_filter: bool,
    min_trend_slope: float,
    volume_filter_window: int,
    min_volume_quantile: float,
):
    """Inner Numba-compiled loop.

    Returns (bbp, rsi, atr_pct, ema_slope, volume_ok, entry) — all length n.
    NaN for warmup bars (in floats). False for warmup bars (in bools).
    """
    n = highs.shape[0]

    # max_records from the pandas replay path
    max_records = bb_length
    if trend_ema_length > max_records:
        max_records = trend_ema_length
    if rsi_length > max_records:
        max_records = rsi_length
    if atr_length > max_records:
        max_records = atr_length
    max_records = max_records + 500

    # min_len — skip bars before the longest indicator has any output
    min_len = bb_length
    if trend_ema_length > min_len:
        min_len = trend_ema_length
    if rsi_length > min_len:
        min_len = rsi_length
    if atr_length > min_len:
        min_len = atr_length

    bbp_arr = np.full(n, np.nan, dtype=np.float64)
    rsi_arr = np.full(n, np.nan, dtype=np.float64)
    atrpct_arr = np.full(n, np.nan, dtype=np.float64)
    slope_arr = np.full(n, np.nan, dtype=np.float64)
    volok_arr = np.zeros(n, dtype=np.bool_)
    entry_arr = np.zeros(n, dtype=np.bool_)

    for t in range(n):
        start = t - max_records + 1
        if start < 0:
            start = 0
        slen = t + 1 - start
        if slen < min_len:
            continue

        h_slice = highs[start:t + 1]
        l_slice = lows[start:t + 1]
        c_slice = closes[start:t + 1]
        v_slice = volumes[start:t + 1]

        bbp_v = _bollinger_percent_b_last(c_slice, bb_length, bb_std)
        rsi_v = _rsi_wilder_last(c_slice, rsi_length)
        atr_v = _atr_wilder_last(h_slice, l_slice, c_slice, atr_length)

        # atr_pct: pandas code does `atr / close.replace(0.0, np.nan)`, which at
        # the last bar means `atr_v / c_slice[-1]` if c_slice[-1] != 0, else NaN.
        last_close = c_slice[slen - 1]
        if last_close == 0.0 or math.isnan(atr_v):
            atr_pct_v = math.nan
        else:
            atr_pct_v = atr_v / last_close

        slope_v = _ema_diff_last(c_slice, trend_ema_length)
        vok = _rolling_volume_quantile_ok_last(v_slice, volume_filter_window,
                                                min_volume_quantile)

        bbp_arr[t] = bbp_v
        rsi_arr[t] = rsi_v
        atrpct_arr[t] = atr_pct_v
        slope_arr[t] = slope_v
        volok_arr[t] = vok

        cond = (
            (not math.isnan(bbp_v)) and bbp_v <= bbp_entry_threshold
            and (not math.isnan(rsi_v)) and rsi_v <= rsi_entry_threshold
            and (not math.isnan(atr_pct_v)) and atr_pct_v <= max_atr_pct_for_entry
            and vok
        )
        if use_trend_filter:
            cond = cond and (not math.isnan(slope_v)) and slope_v >= min_trend_slope
        entry_arr[t] = cond

    return bbp_arr, rsi_arr, atrpct_arr, slope_arr, volok_arr, entry_arr


def compute_controller_compat_mr_numba(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
    bb_length: int,
    bb_std: float,
    rsi_length: int,
    atr_length: int,
    trend_ema_length: int,
    bbp_entry_threshold: float,
    rsi_entry_threshold: float,
    max_atr_pct_for_entry: float,
    use_trend_filter: bool,
    min_trend_slope: float,
    volume_filter_window: int,
    min_volume_quantile: float,
):
    """Public entrypoint. Returns the same 6-tuple as `_compute_controller_compat`."""
    # Ensure contiguous float64 arrays (Numba requires this)
    h = np.ascontiguousarray(highs, dtype=np.float64)
    l = np.ascontiguousarray(lows, dtype=np.float64)
    c = np.ascontiguousarray(closes, dtype=np.float64)
    v = np.ascontiguousarray(volumes, dtype=np.float64)
    return _run_mr_kernel(
        h, l, c, v,
        int(bb_length), float(bb_std),
        int(rsi_length), int(atr_length), int(trend_ema_length),
        float(bbp_entry_threshold), float(rsi_entry_threshold),
        float(max_atr_pct_for_entry),
        bool(use_trend_filter), float(min_trend_slope),
        int(volume_filter_window), float(min_volume_quantile),
    )
