"""
Feature alignment for no-lookahead enforcement.

In "open" timestamp mode, the candle timestamp represents the bar's open time.
Signals computed from candle t use data that isn't known until candle t closes.
Therefore, signals must be SHIFTED by 1 bar: orders active during bar t use
features computed from bar t-1.
"""

import numpy as np
from pmm_lab.features.pmm_dynamic_features import PMMDynamicFeatures


def _shift_array(arr: np.ndarray) -> np.ndarray:
    """Shift array forward by 1, inserting NaN at index 0."""
    shifted = np.roll(arr, 1)
    shifted[0] = np.nan
    return shifted


def align_features(
    features: PMMDynamicFeatures,
    timestamp_mode: str = "open",
) -> PMMDynamicFeatures:
    """Align features to prevent lookahead bias.

    Parameters
    ----------
    features : PMMDynamicFeatures
        Raw features where features[t] was computed using candle[t].
    timestamp_mode : str
        "open" (default, conservative) — shift all feature arrays forward by 1 bar.
            features_aligned[t] = features_raw[t-1]. Bar 0 gets NaN.
        "close" — no shift needed (features from bar t are available after bar t closes).

    Returns
    -------
    PMMDynamicFeatures
        Aligned features. warmup_end is incremented by 1 in "open" mode.
    """
    if timestamp_mode == "close":
        return PMMDynamicFeatures(
            reference_price=features.reference_price.copy(),
            spread_multiplier=features.spread_multiplier.copy(),
            natr=features.natr.copy(),
            macd_raw=features.macd_raw.copy(),
            macd_signal_z=features.macd_signal_z.copy(),
            macdh=features.macdh.copy(),
            macdh_sign=features.macdh_sign.copy(),
            price_multiplier=features.price_multiplier.copy(),
            warmup_end=features.warmup_end,
        )

    # "open" mode: shift all arrays forward by 1
    return PMMDynamicFeatures(
        reference_price=_shift_array(features.reference_price),
        spread_multiplier=_shift_array(features.spread_multiplier),
        natr=_shift_array(features.natr),
        macd_raw=_shift_array(features.macd_raw),
        macd_signal_z=_shift_array(features.macd_signal_z),
        macdh=_shift_array(features.macdh),
        macdh_sign=_shift_array(features.macdh_sign),
        price_multiplier=_shift_array(features.price_multiplier),
        warmup_end=features.warmup_end + 1,
    )
