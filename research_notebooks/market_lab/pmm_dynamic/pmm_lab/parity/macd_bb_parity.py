"""
MACD-BB feature parity checker.

Compares local pmm_lab feature computation against:
1. Frozen fixture values (always available)
2. Controller-equivalent path (pandas_ta directly, no Hummingbot required)
"""

import numpy as np
import pandas as pd
import pandas_ta as pta
import logging
from typing import Dict, List, Any
from dataclasses import dataclass

from pmm_lab.parity.feature_parity import ParityResult

logger = logging.getLogger(__name__)


def check_macd_bb_parity_frozen(
    candles: np.ndarray,
    expected_features: Dict[str, Dict[str, float]],
    config_params: Dict[str, Any],
    abs_tol: float = 1e-8,
    rel_tol: float = 1e-6,
) -> ParityResult:
    """Compare local MACD-BB features against frozen fixture values.

    Parameters
    ----------
    candles : np.ndarray
        Candle data.
    expected_features : dict
        {bar_idx_str: {field: expected_value}} from fixture.
    config_params : dict
        Raw params for feature config.
    abs_tol, rel_tol : float
        Tolerances.

    Returns
    -------
    ParityResult
    """
    from pmm_lab.features.macd_bb_features import compute_macd_bb_features, MACDBBFeatureConfig

    feat_config = MACDBBFeatureConfig(
        bb_length=config_params.get("bb_length", 100),
        bb_std=config_params.get("bb_std", 2.0),
        bb_long_threshold=config_params.get("bb_long_threshold", 0.0),
        bb_short_threshold=config_params.get("bb_short_threshold", 1.0),
        macd_fast=config_params.get("macd_fast", 21),
        macd_slow=config_params.get("macd_slow", 42),
        macd_signal=config_params.get("macd_signal", 9),
        controller_compat=True,
        timestamp_mode="close",  # no shift for raw parity comparison
    )
    result = compute_macd_bb_features(candles, feat_config)

    field_map = {
        "bbp": result.data["bbp"],
        "macd": result.data["macd"],
        "macdh": result.data["macdh"],
        "signal": result.data["signal"],
    }

    mismatches = []
    max_abs = 0.0
    max_rel = 0.0

    for bar_str, expected in expected_features.items():
        bar = int(bar_str)
        for field_name, exp_val in expected.items():
            if field_name not in field_map:
                continue
            arr = field_map[field_name]
            if bar >= len(arr):
                mismatches.append({
                    "bar": bar, "field": field_name,
                    "expected": exp_val, "actual": None, "diff": float('inf'),
                })
                continue

            actual_val = float(arr[bar])

            if np.isnan(exp_val) and np.isnan(actual_val):
                continue

            abs_diff = abs(actual_val - exp_val)
            rel_diff = abs_diff / abs(exp_val) if abs(exp_val) > 1e-15 else abs_diff

            max_abs = max(max_abs, abs_diff)
            max_rel = max(max_rel, rel_diff)

            if abs_diff > abs_tol and rel_diff > rel_tol:
                mismatches.append({
                    "bar": bar, "field": field_name,
                    "expected": exp_val, "actual": actual_val, "diff": abs_diff,
                })

    return ParityResult(
        passed=len(mismatches) == 0,
        mode="frozen",
        mismatches=mismatches,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
    )


def check_macd_bb_parity_native(
    candles: np.ndarray,
    config_params: Dict[str, Any],
    abs_tol: float = 1e-8,
    rel_tol: float = 1e-6,
) -> ParityResult:
    """Compare local features against controller-equivalent computation.

    Replicates the exact logic from macd_bb_v1.update_processed_data()
    using pandas_ta directly, then compares against the pmm_lab feature engine.
    """
    from pmm_lab.features.macd_bb_features import (
        compute_macd_bb_features, MACDBBFeatureConfig, _find_bbp_col,
    )

    bb_length = config_params.get("bb_length", 100)
    bb_std = config_params.get("bb_std", 2.0)
    bb_long_threshold = config_params.get("bb_long_threshold", 0.0)
    bb_short_threshold = config_params.get("bb_short_threshold", 1.0)
    macd_fast = config_params.get("macd_fast", 21)
    macd_slow = config_params.get("macd_slow", 42)
    macd_signal = config_params.get("macd_signal", 9)
    max_records = max(macd_slow, macd_fast, macd_signal, bb_length) + 20

    # Compute lab features (controller_compat=True, close mode)
    feat_config = MACDBBFeatureConfig(
        bb_length=bb_length, bb_std=bb_std,
        bb_long_threshold=bb_long_threshold,
        bb_short_threshold=bb_short_threshold,
        macd_fast=macd_fast, macd_slow=macd_slow, macd_signal=macd_signal,
        controller_compat=True,
        timestamp_mode="close",
    )
    lab_result = compute_macd_bb_features(candles, feat_config)
    lab_signal = lab_result.data["signal"]
    lab_bbp = lab_result.data["bbp"]
    lab_macd = lab_result.data["macd"]
    lab_macdh = lab_result.data["macdh"]

    # Compute native controller features
    n = len(candles)
    close = pd.Series(candles["close"].astype("float64"))

    native_signal = np.zeros(n, dtype="float64")
    native_bbp = np.full(n, np.nan, dtype="float64")
    native_macd = np.full(n, np.nan, dtype="float64")
    native_macdh = np.full(n, np.nan, dtype="float64")

    warmup = lab_result.warmup_end

    for t in range(warmup, n):
        start = max(0, t - max_records + 1)
        w_close = close.iloc[start:t + 1]

        # Exactly replicate controller: df.ta.bbands + df.ta.macd
        bb_out = pta.bbands(w_close, length=bb_length, std=bb_std)
        if bb_out is None:
            continue
        try:
            bbp_col = _find_bbp_col(bb_out.columns, bb_length, bb_std)
        except KeyError:
            continue
        bbp_val = bb_out[bbp_col].iloc[-1]

        macd_out = pta.macd(w_close, fast=macd_fast, slow=macd_slow, signal=macd_signal)
        if macd_out is None:
            continue
        macd_col = f"MACD_{macd_fast}_{macd_slow}_{macd_signal}"
        macdh_col = f"MACDh_{macd_fast}_{macd_slow}_{macd_signal}"
        if macd_col not in macd_out.columns:
            continue
        macd_val = macd_out[macd_col].iloc[-1]
        macdh_val = macd_out[macdh_col].iloc[-1]

        if pd.isna(bbp_val) or pd.isna(macd_val) or pd.isna(macdh_val):
            continue

        native_bbp[t] = float(bbp_val)
        native_macd[t] = float(macd_val)
        native_macdh[t] = float(macdh_val)

        # Signal logic
        if (native_bbp[t] < bb_long_threshold and
                native_macdh[t] > 0 and native_macd[t] < 0):
            native_signal[t] = 1.0
        elif (native_bbp[t] > bb_short_threshold and
              native_macdh[t] < 0 and native_macd[t] > 0):
            native_signal[t] = -1.0

    # Compare
    mismatches = []
    max_abs = 0.0
    max_rel = 0.0

    for t in range(warmup, n):
        for field_name, lab_arr, native_arr in [
            ("bbp", lab_bbp, native_bbp),
            ("macd", lab_macd, native_macd),
            ("macdh", lab_macdh, native_macdh),
            ("signal", lab_signal, native_signal),
        ]:
            lab_val = float(lab_arr[t])
            native_val = float(native_arr[t])

            if np.isnan(lab_val) and np.isnan(native_val):
                continue

            abs_diff = abs(lab_val - native_val)
            denom = abs(native_val) if abs(native_val) > 1e-15 else 1.0
            rel_diff = abs_diff / denom

            max_abs = max(max_abs, abs_diff)
            max_rel = max(max_rel, rel_diff)

            if abs_diff > abs_tol and rel_diff > rel_tol:
                mismatches.append({
                    "bar": t, "field": field_name,
                    "expected": native_val, "actual": lab_val, "diff": abs_diff,
                })

    return ParityResult(
        passed=len(mismatches) == 0,
        mode="native",
        mismatches=mismatches,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
    )
