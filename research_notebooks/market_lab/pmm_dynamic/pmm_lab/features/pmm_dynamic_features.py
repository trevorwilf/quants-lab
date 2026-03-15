"""
PMM Dynamic feature computation — must match Hummingbot's pmm_dynamic controller.

Reference: https://github.com/hummingbot/hummingbot/blob/master/controllers/market_making/pmm_dynamic.py
"""

import numpy as np
import pandas as pd
import pandas_ta as ta
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PMMDynamicConfig:
    """PMM Dynamic indicator parameters."""
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9
    natr_length: int = 14
    controller_compat: bool = True  # Default to controller-equivalent mode


@dataclass
class PMMDynamicFeatures:
    """Output of PMM Dynamic feature computation for each bar."""
    reference_price: np.ndarray      # float64, length N
    spread_multiplier: np.ndarray    # float64, length N
    natr: np.ndarray                 # float64, length N
    macd_raw: np.ndarray             # float64, length N
    macd_signal_z: np.ndarray        # float64, length N (z-scored, sign-flipped)
    macdh: np.ndarray                # float64, length N
    macdh_sign: np.ndarray           # float64, length N (+1 or -1)
    price_multiplier: np.ndarray     # float64, length N
    warmup_end: int                  # index of first valid bar (all bars before this are NaN)


def compute_pmm_dynamic_features(
    candles: np.ndarray,
    config: PMMDynamicConfig = PMMDynamicConfig(),
) -> PMMDynamicFeatures:
    """Compute PMM Dynamic features from canonical candle data.

    This reproduces Hummingbot's PMM Dynamic controller logic:

    1. natr = ta.natr(high, low, close, length=natr_length) / 100
    2. macd_output = ta.macd(close, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    3. macd = macd_output["MACD_{fast}_{slow}_{signal}"]
    4. macd_signal_z = -(macd - macd.mean()) / macd.std()
    5. macdh = macd_output["MACDh_{fast}_{slow}_{signal}"]
    6. macdh_sign = where(macdh > 0, 1, -1)
    7. max_price_shift = natr / 2
    8. price_multiplier = (0.5 * macd_signal_z + 0.5 * macdh_sign) * max_price_shift
    9. spread_multiplier = natr
    10. reference_price = close * (1 + price_multiplier)

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array with fields: timestamp, open, high, low, close, volume, is_forward_fill
    config : PMMDynamicConfig
        Indicator parameters.

    Returns
    -------
    PMMDynamicFeatures
        Feature arrays aligned to the candle array (same length). Bars before warmup_end contain NaN.

    Raises
    ------
    ValueError
        If candle array is too short for the given config.
    """
    warmup_end = max(config.macd_slow, config.natr_length) + config.macd_signal + 1
    n = len(candles)

    if n < warmup_end + 1:
        raise ValueError(
            f"Candle array has {n} bars but needs at least {warmup_end + 1} "
            f"for config (macd_slow={config.macd_slow}, natr_length={config.natr_length}, "
            f"macd_signal={config.macd_signal})"
        )

    # Convert to pandas for pandas_ta
    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    close = pd.Series(candles["close"].astype("float64"))

    # --- CONTROLLER-COMPAT SLIDING WINDOW MODE ---
    # The live controller (app/controllers/market_making/pmm_dynamic.py)
    # recomputes MACD on the last max_records candles at each bar.
    # Since MACD uses EMAs, this produces different values than computing
    # MACD once on the full history. This mode replicates that behavior.

    max_records = max(config.macd_fast, config.macd_slow, config.macd_signal, config.natr_length) + 100

    if config.controller_compat:
        # Sliding-window mode: recompute MACD + NATR on last max_records bars per bar
        natr_arr = np.full(n, np.nan, dtype="float64")
        macd_arr = np.full(n, np.nan, dtype="float64")
        macd_signal_z_arr = np.full(n, np.nan, dtype="float64")
        macdh_arr = np.full(n, np.nan, dtype="float64")
        macdh_sign_arr = np.full(n, np.nan, dtype="float64")

        warmup_end_calc = max(config.macd_slow, config.natr_length) + config.macd_signal + 1

        for t in range(warmup_end_calc, n):
            start = max(0, t - max_records + 1)
            window_high = high.iloc[start:t+1]
            window_low = low.iloc[start:t+1]
            window_close = close.iloc[start:t+1]

            # Recompute NATR on window
            w_natr = ta.natr(window_high, window_low, window_close, length=config.natr_length) / 100.0
            natr_arr[t] = float(w_natr.iloc[-1]) if not pd.isna(w_natr.iloc[-1]) else np.nan

            # Recompute MACD on window
            w_macd_out = ta.macd(window_close, fast=config.macd_fast, slow=config.macd_slow, signal=config.macd_signal)
            w_macd = w_macd_out[f"MACD_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"]
            w_macdh = w_macd_out[f"MACDh_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"]

            macd_arr[t] = float(w_macd.iloc[-1]) if not pd.isna(w_macd.iloc[-1]) else np.nan
            macdh_arr[t] = float(w_macdh.iloc[-1]) if not pd.isna(w_macdh.iloc[-1]) else np.nan

            # Z-score: controller uses plain mean/std of the entire MACD buffer
            macd_mean = float(w_macd.mean())
            macd_std = float(w_macd.std(ddof=1))  # pandas default ddof=1
            if macd_std > 0:
                macd_signal_z_arr[t] = -(float(w_macd.iloc[-1]) - macd_mean) / macd_std
            else:
                macd_signal_z_arr[t] = 0.0

            macdh_sign_arr[t] = 1.0 if float(w_macdh.iloc[-1]) > 0 else -1.0

    else:
        # Full-history mode (original — faster, but NOT controller-equivalent for long histories)
        natr_series = ta.natr(high, low, close, length=config.natr_length) / 100.0
        macd_output = ta.macd(close, fast=config.macd_fast, slow=config.macd_slow, signal=config.macd_signal)
        macd_col = f"MACD_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"
        macdh_col = f"MACDh_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"

        macd_series = macd_output[macd_col]
        macdh_series = macd_output[macdh_col]

        macd_rolling_mean = macd_series.rolling(window=max_records, min_periods=2).mean()
        macd_rolling_std = macd_series.rolling(window=max_records, min_periods=2).std(ddof=1)
        macd_rolling_std_safe = macd_rolling_std.where(macd_rolling_std > 0, other=np.nan)
        macd_signal_z_series = -(macd_series - macd_rolling_mean) / macd_rolling_std_safe
        macd_signal_z_series = macd_signal_z_series.fillna(0.0)
        macdh_sign_series = pd.Series(np.where(macdh_series > 0, 1.0, -1.0), dtype="float64")

        natr_arr = np.array(natr_series, dtype="float64")
        macd_arr = np.array(macd_series, dtype="float64")
        macd_signal_z_arr = np.array(macd_signal_z_series, dtype="float64")
        macdh_arr = np.array(macdh_series, dtype="float64")
        macdh_sign_arr = np.array(macdh_sign_series, dtype="float64")
    close_arr = np.array(candles["close"], dtype="float64")

    # 5. Derived features
    max_price_shift = natr_arr / 2.0
    price_multiplier_arr = (0.5 * macd_signal_z_arr + 0.5 * macdh_sign_arr) * max_price_shift
    spread_multiplier_arr = natr_arr.copy()
    reference_price_arr = close_arr * (1.0 + price_multiplier_arr)

    # Ensure warmup bars are NaN
    for arr in (natr_arr, macd_arr, macd_signal_z_arr, macdh_arr,
                macdh_sign_arr, price_multiplier_arr, spread_multiplier_arr,
                reference_price_arr):
        arr[:warmup_end] = np.nan

    return PMMDynamicFeatures(
        reference_price=reference_price_arr,
        spread_multiplier=spread_multiplier_arr,
        natr=natr_arr,
        macd_raw=macd_arr,
        macd_signal_z=macd_signal_z_arr,
        macdh=macdh_arr,
        macdh_sign=macdh_sign_arr,
        price_multiplier=price_multiplier_arr,
        warmup_end=warmup_end,
    )
