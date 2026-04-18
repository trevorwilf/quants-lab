"""
EMA regime-hold feature computation — multi-timeframe.

Must match Hummingbot's `ema_regime_hold_v1` controller `update_processed_data()`:
  1. Compute EMA_fast/EMA_slow/ADX on the regime (slow) candles.
  2. Project `trend_on = (ema_fast >= ema_slow) & (adx >= threshold)` onto the
     signal (fast) timeframe via `pd.merge_asof(direction='backward')`.
  3. Combine with `volume_ok` (fast timeframe) to produce `eligible`.
  4. `signal = eligible.astype(int)` (long-only).

Per D20: controller_compat=True (replay/sliding-window) is the authoritative
path until vectorized parity is proven to atol=1e-10.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pmm_lab.features.ta_utils_shim import adx_wilder, ema, rolling_volume_quantile_ok
from pmm_lab.sim.strategy import SignalOutput


@dataclass(frozen=True)
class EMARegimeHoldFeatureConfig:
    """EMA regime-hold indicator parameters."""

    regime_ema_fast: int = 50
    regime_ema_slow: int = 200
    regime_adx_length: int = 14
    regime_adx_threshold: float = 20.0
    volume_filter_window: int = 288
    min_volume_quantile: float = 0.30
    hold_mode: str = "reentry"  # D4 — 'hold' rejected at canonicalize time
    timestamp_mode: str = "open"
    controller_compat: bool = False
    use_numba_kernel: bool = False  # opt-in Numba compiled controller-compat path


def _compute_regime_trend(regime_candles: np.ndarray, config: EMARegimeHoldFeatureConfig):
    """Compute trend_on series on regime candles (slow timeframe).

    Returns a pandas DataFrame with columns ['timestamp', 'trend_on'] and
    NaN rows dropped (matching the controller's `df_slow.dropna(inplace=True)`
    at line 147).
    """
    close = pd.Series(regime_candles["close"].astype("float64"))
    high = pd.Series(regime_candles["high"].astype("float64"))
    low = pd.Series(regime_candles["low"].astype("float64"))
    ts = pd.Series(regime_candles["timestamp"].astype("int64"))

    df_slow = pd.DataFrame({"timestamp": ts, "close": close, "high": high, "low": low})
    df_slow["ema_fast"] = ema(close, config.regime_ema_fast)
    df_slow["ema_slow"] = ema(close, config.regime_ema_slow)
    df_slow["adx"] = adx_wilder(high, low, close, config.regime_adx_length)
    df_slow.dropna(inplace=True)
    df_slow["trend_on"] = (
        (df_slow["ema_fast"] >= df_slow["ema_slow"])
        & (df_slow["adx"] >= config.regime_adx_threshold)
    )
    return df_slow[["timestamp", "trend_on"]].copy()


def _merge_asof_backward(
    signal_ts: np.ndarray, slow_ind: pd.DataFrame
) -> np.ndarray:
    """Project trend_on from slow timeframe onto signal timeframe.

    Uses merge_asof with direction='backward' — signal bar at time t sees
    only regime bars with timestamp <= t. This is the no-lookahead contract.

    Returns a numpy bool array of length len(signal_ts). Bars before the
    first regime bar get False (no regime yet).
    """
    fast = pd.DataFrame({"timestamp": signal_ts.astype("int64")})
    # Ensure both sides are sorted (merge_asof requires sorted keys).
    slow_sorted = slow_ind.sort_values("timestamp").reset_index(drop=True)
    merged = pd.merge_asof(
        fast.sort_values("timestamp").reset_index(drop=True),
        slow_sorted,
        on="timestamp",
        direction="backward",
    )
    return merged["trend_on"].fillna(False).astype("bool").to_numpy()


def _compute_vectorized(signal_candles, regime_candles, config):
    """Full-history vectorized path: compute regime on all slow candles,
    project once, compute vol_ok on all fast candles.
    """
    slow_ind = _compute_regime_trend(regime_candles, config)
    signal_ts = signal_candles["timestamp"].astype("int64")
    trend_on = _merge_asof_backward(signal_ts, slow_ind)

    vol_series = pd.Series(signal_candles["volume"].astype("float64"))
    vol_ok = rolling_volume_quantile_ok(
        vol_series, config.volume_filter_window, config.min_volume_quantile
    ).to_numpy(dtype="bool")

    return trend_on, vol_ok


def _compute_controller_compat(signal_candles, regime_candles, config):
    """Sliding-window replay matching the controller's per-tick behavior.

    At each fast bar t:
      - slice regime candles to the most recent 3000 bars (controller's max_records)
      - recompute ema_fast/ema_slow/adx/trend_on
      - slice fast candles to most recent 6000 bars
      - recompute vol_ok
      - project via merge_asof backward
    """
    # Opt-in Numba compiled path — same bounded-slice semantics, much faster
    if getattr(config, "use_numba_kernel", False):
        from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE
        if _NUMBA_AVAILABLE:
            from pmm_lab.features._numba_ema_regime_hold import compute_controller_compat_ema_numba
            return compute_controller_compat_ema_numba(
                fast_timestamps=signal_candles["timestamp"].astype("int64"),
                fast_volumes=signal_candles["volume"].astype("float64"),
                regime_timestamps=regime_candles["timestamp"].astype("int64"),
                regime_highs=regime_candles["high"].astype("float64"),
                regime_lows=regime_candles["low"].astype("float64"),
                regime_closes=regime_candles["close"].astype("float64"),
                regime_ema_fast=int(config.regime_ema_fast),
                regime_ema_slow=int(config.regime_ema_slow),
                regime_adx_length=int(config.regime_adx_length),
                regime_adx_threshold=float(config.regime_adx_threshold),
                volume_filter_window=int(config.volume_filter_window),
                min_volume_quantile=float(config.min_volume_quantile),
            )
        # Fallback to pandas path if Numba is not installed
    SLOW_MAX_RECORDS = 3000
    FAST_MAX_RECORDS = 6000

    n_fast = len(signal_candles)
    trend_arr = np.zeros(n_fast, dtype="bool")
    volok_arr = np.zeros(n_fast, dtype="bool")

    signal_ts = signal_candles["timestamp"].astype("int64")
    regime_ts = regime_candles["timestamp"].astype("int64")

    for t in range(n_fast):
        t_now = int(signal_ts[t])

        # Slice regime candles to those with timestamp <= t_now, bounded by SLOW_MAX_RECORDS
        regime_mask = regime_ts <= t_now
        regime_subset_idx = np.where(regime_mask)[0]
        if len(regime_subset_idx) == 0:
            continue
        last_slow_idx = int(regime_subset_idx[-1])
        slow_start = max(0, last_slow_idx - SLOW_MAX_RECORDS + 1)
        slow_sub = regime_candles[slow_start:last_slow_idx + 1]

        # Slice fast candles (latest FAST_MAX_RECORDS ending at t)
        fast_start = max(0, t - FAST_MAX_RECORDS + 1)
        fast_sub = signal_candles[fast_start:t + 1]

        # Compute regime trend on slice
        slow_ind = _compute_regime_trend(slow_sub, config)
        if slow_ind.empty:
            continue

        # Vol-ok on fast slice (we only need the final value)
        vol_series = pd.Series(fast_sub["volume"].astype("float64"))
        vok_series = rolling_volume_quantile_ok(
            vol_series, config.volume_filter_window, config.min_volume_quantile
        )
        volok_arr[t] = bool(vok_series.iloc[-1])

        # Backward-asof projection: most recent slow bar with timestamp <= t_now
        slow_recent = slow_ind[slow_ind["timestamp"] <= t_now]
        if not slow_recent.empty:
            trend_arr[t] = bool(slow_recent["trend_on"].iloc[-1])
        else:
            trend_arr[t] = False

    return trend_arr, volok_arr


def _shift_array(arr: np.ndarray) -> np.ndarray:
    shifted = np.roll(arr, 1)
    if shifted.dtype.kind in ("f",):
        shifted[0] = np.nan
    else:
        shifted[0] = 0
    return shifted


def _shift_bool(arr: np.ndarray) -> np.ndarray:
    shifted = np.roll(arr, 1)
    shifted[0] = False
    return shifted


def _shift_signal(arr: np.ndarray) -> np.ndarray:
    shifted = np.roll(arr, 1)
    shifted[0] = 0.0
    return shifted


def compute_ema_regime_hold_features(
    signal_candles: np.ndarray,
    regime_candles: np.ndarray,
    config: EMARegimeHoldFeatureConfig = EMARegimeHoldFeatureConfig(),
) -> SignalOutput:
    """Compute EMA regime-hold signals.

    Parameters
    ----------
    signal_candles : np.ndarray
        Fast-timeframe candles (typically 5m).
    regime_candles : np.ndarray
        Slow-timeframe candles (typically 4h).
    config : EMARegimeHoldFeatureConfig
        Indicator parameters.

    Returns
    -------
    SignalOutput
        data keys: signal, trend_on, vol_ok, close_price, timestamp.
        signal values in {0.0, 1.0}; long-only.
    """
    n = len(signal_candles)
    close_price = signal_candles["close"].astype("float64").copy()
    timestamps = signal_candles["timestamp"].astype("int64").copy()

    if config.controller_compat:
        trend_on, vol_ok = _compute_controller_compat(signal_candles, regime_candles, config)
    else:
        trend_on, vol_ok = _compute_vectorized(signal_candles, regime_candles, config)

    eligible = trend_on & vol_ok
    signal = eligible.astype("float64")

    # Warmup: first bar where trend_on has been defined (a regime bar exists with ts <= now).
    # In controller_compat, trend_arr stays False during warmup; in vectorized, same.
    # We define warmup_end as the first bar where either trend_on or vol_ok has a
    # non-default value — practically, the first bar where a regime value exists.
    # Find first bar with a regime projection available:
    warmup_end = n
    if len(regime_candles) > 0:
        # Earliest candidate: first signal bar whose timestamp >= first regime_trend bar
        slow_ind = _compute_regime_trend(regime_candles, config)
        if not slow_ind.empty:
            first_trend_ts = int(slow_ind["timestamp"].iloc[0])
            idx = np.searchsorted(
                signal_candles["timestamp"].astype("int64"), first_trend_ts, side="left"
            )
            warmup_end = int(idx)
    # Zero signal in warmup region
    signal[:warmup_end] = 0.0

    if config.timestamp_mode == "open":
        trend_on = _shift_bool(trend_on)
        vol_ok = _shift_bool(vol_ok)
        signal = _shift_signal(signal)
        close_price = _shift_array(close_price.astype("float64"))
        warmup_end = warmup_end + 1

    return SignalOutput(
        warmup_end=warmup_end,
        data={
            "signal": signal,
            "trend_on": trend_on.astype("float64"),
            "vol_ok": vol_ok.astype("float64"),
            "close_price": close_price,
            "timestamp": timestamps.astype("float64"),
        },
    )
