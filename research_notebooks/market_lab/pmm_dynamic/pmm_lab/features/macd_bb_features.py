"""
MACD+BB feature computation — must match Hummingbot's macd_bb_v1 controller.

Reference: app/controllers/directional_trading/macd_bb_v1.py
"""

import numpy as np
import pandas as pd
import pandas_ta as ta
from dataclasses import dataclass
from typing import Optional

from pmm_lab.sim.strategy import SignalOutput


@dataclass(frozen=True)
class MACDBBFeatureConfig:
    """MACD+BB indicator parameters."""
    bb_length: int = 100
    bb_std: float = 2.0
    bb_long_threshold: float = 0.0
    bb_short_threshold: float = 1.0
    macd_fast: int = 21
    macd_slow: int = 42
    macd_signal: int = 9
    timestamp_mode: str = "open"
    controller_compat: bool = True


def _find_bbp_col(columns, bb_length, bb_std):
    """Find the BBP column name — pandas_ta naming varies by version."""
    # Try common patterns
    for pattern in [
        f"BBP_{bb_length}_{bb_std}",
        f"BBP_{bb_length}_{bb_std}_{bb_std}",
    ]:
        if pattern in columns:
            return pattern
    # Fallback: search for any column starting with BBP_
    for col in columns:
        if col.startswith("BBP_"):
            return col
    raise KeyError(f"No BBP column found in {list(columns)}")


def _compute_vectorized(candles: np.ndarray, config: MACDBBFeatureConfig):
    """Full-history vectorized computation (fast, for search phase)."""
    n = len(candles)
    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    close = pd.Series(candles["close"].astype("float64"))

    # BBands
    bb_out = ta.bbands(close, length=config.bb_length, std=config.bb_std)
    # pandas_ta names columns as BBP_{length}_{std}_{std} in newer versions
    bbp_col = _find_bbp_col(bb_out.columns, config.bb_length, config.bb_std)
    bbp = bb_out[bbp_col].to_numpy(dtype="float64")

    # MACD
    macd_out = ta.macd(close, fast=config.macd_fast, slow=config.macd_slow,
                       signal=config.macd_signal)
    macd_col = f"MACD_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"
    macdh_col = f"MACDh_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"
    macd_arr = macd_out[macd_col].to_numpy(dtype="float64")
    macdh_arr = macd_out[macdh_col].to_numpy(dtype="float64")

    # Signal logic — matches controller exactly
    signal = np.zeros(n, dtype="float64")
    long_cond = (bbp < config.bb_long_threshold) & (macdh_arr > 0) & (macd_arr < 0)
    short_cond = (bbp > config.bb_short_threshold) & (macdh_arr < 0) & (macd_arr > 0)
    signal[long_cond] = 1.0
    signal[short_cond] = -1.0

    # Warmup: need both BBands and MACD to be valid
    # BBands warmup = bb_length, MACD warmup = macd_slow + macd_signal - 1
    warmup_end = max(config.bb_length, config.macd_slow + config.macd_signal - 1)
    # Safety: find first bar where all indicators are non-NaN
    for i in range(warmup_end, n):
        if not (np.isnan(bbp[i]) or np.isnan(macd_arr[i]) or np.isnan(macdh_arr[i])):
            warmup_end = i
            break

    # Zero out signals in warmup region
    signal[:warmup_end] = 0.0

    return bbp, macd_arr, macdh_arr, signal, warmup_end


def _compute_controller_compat(candles: np.ndarray, config: MACDBBFeatureConfig):
    """Sliding-window computation matching the live controller."""
    n = len(candles)
    max_records = max(config.macd_slow, config.macd_fast, config.macd_signal,
                      config.bb_length) + 20

    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    close = pd.Series(candles["close"].astype("float64"))

    bbp_arr = np.full(n, np.nan, dtype="float64")
    macd_arr = np.full(n, np.nan, dtype="float64")
    macdh_arr = np.full(n, np.nan, dtype="float64")
    signal = np.zeros(n, dtype="float64")

    # Determine warmup from vectorized to find first valid bar
    warmup_end = max(config.bb_length, config.macd_slow + config.macd_signal - 1)

    # Find actual warmup by checking where indicators produce values
    found_warmup = False
    for t in range(warmup_end, n):
        start = max(0, t - max_records + 1)
        w_close = close.iloc[start:t + 1]

        # BBands
        bb_out = ta.bbands(w_close, length=config.bb_length, std=config.bb_std)
        if bb_out is None:
            continue
        try:
            bbp_col = _find_bbp_col(bb_out.columns, config.bb_length, config.bb_std)
        except KeyError:
            continue
        bbp_val = bb_out[bbp_col].iloc[-1]

        # MACD
        macd_out = ta.macd(w_close, fast=config.macd_fast, slow=config.macd_slow,
                           signal=config.macd_signal)
        if macd_out is None:
            continue
        macd_col = f"MACD_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"
        macdh_col = f"MACDh_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"
        if macd_col not in macd_out.columns:
            continue
        macd_val = macd_out[macd_col].iloc[-1]
        macdh_val = macd_out[macdh_col].iloc[-1]

        if pd.isna(bbp_val) or pd.isna(macd_val) or pd.isna(macdh_val):
            continue

        if not found_warmup:
            warmup_end = t
            found_warmup = True

        bbp_arr[t] = float(bbp_val)
        macd_arr[t] = float(macd_val)
        macdh_arr[t] = float(macdh_val)

        # Signal logic
        if (bbp_arr[t] < config.bb_long_threshold and
                macdh_arr[t] > 0 and macd_arr[t] < 0):
            signal[t] = 1.0
        elif (bbp_arr[t] > config.bb_short_threshold and
              macdh_arr[t] < 0 and macd_arr[t] > 0):
            signal[t] = -1.0

    return bbp_arr, macd_arr, macdh_arr, signal, warmup_end


def compute_macd_bb_features(
    candles: np.ndarray,
    config: MACDBBFeatureConfig = MACDBBFeatureConfig(),
) -> SignalOutput:
    """Compute MACD+BB features from canonical candle data.

    Produces signals matching the Hummingbot macd_bb_v1 controller:
    - long:  bbp < bb_long_threshold AND macdh > 0 AND macd < 0
    - short: bbp > bb_short_threshold AND macdh < 0 AND macd > 0

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array.
    config : MACDBBFeatureConfig
        Indicator parameters.

    Returns
    -------
    SignalOutput
        Contains bbp, macd, macdh, signal arrays and warmup_end.
    """
    if config.controller_compat:
        bbp, macd, macdh, signal, warmup_end = _compute_controller_compat(candles, config)
    else:
        bbp, macd, macdh, signal, warmup_end = _compute_vectorized(candles, config)

    # Close prices for order placement
    close_price = candles["close"].astype("float64").copy()

    # Apply timestamp alignment
    if config.timestamp_mode == "open":
        bbp = _shift_array(bbp)
        macd = _shift_array(macd)
        macdh = _shift_array(macdh)
        signal = _shift_signal(signal)
        close_price = _shift_array(close_price)
        warmup_end = warmup_end + 1

    return SignalOutput(
        warmup_end=warmup_end,
        data={
            "bbp": bbp,
            "macd": macd,
            "macdh": macdh,
            "signal": signal,
            "close_price": close_price,
        },
    )


def _shift_array(arr: np.ndarray) -> np.ndarray:
    """Shift array forward by 1, inserting NaN at index 0."""
    shifted = np.roll(arr, 1)
    shifted[0] = np.nan
    return shifted


def _shift_signal(arr: np.ndarray) -> np.ndarray:
    """Shift signal array forward by 1, inserting 0 at index 0."""
    shifted = np.roll(arr, 1)
    shifted[0] = 0.0
    return shifted
