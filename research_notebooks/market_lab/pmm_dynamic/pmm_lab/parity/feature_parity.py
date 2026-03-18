"""
Feature parity checker.

Compares local pmm_lab feature computation against:
1. Frozen fixture values (always available)
2. Native Hummingbot controller logic (replicated locally, no Hummingbot required)
"""

import numpy as np
import logging
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParityResult:
    """Result of a feature parity check."""
    passed: bool
    mode: str                    # "frozen" or "native"
    mismatches: List[Dict[str, Any]]  # list of {bar, field, expected, actual, diff}
    max_abs_diff: float
    max_rel_diff: float


def check_feature_parity_frozen(
    candles: np.ndarray,
    expected_features: Dict[str, Dict[str, float]],
    config_params: Dict[str, Any],
    abs_tol: float = 1e-8,
    rel_tol: float = 1e-6,
) -> ParityResult:
    """Compare local features against frozen fixture values.

    Parameters
    ----------
    candles : np.ndarray
        Candle data.
    expected_features : Dict
        {bar_idx_str: {field: expected_value}} from fixture.json.
    config_params : Dict
        Raw params for feature config.
    abs_tol : float
        Absolute tolerance.
    rel_tol : float
        Relative tolerance.

    Returns
    -------
    ParityResult
    """
    from pmm_lab.features.pmm_dynamic_features import compute_pmm_dynamic_features, PMMDynamicConfig

    feat_config = PMMDynamicConfig(
        macd_fast=config_params.get("macd_fast", 21),
        macd_slow=config_params.get("macd_slow", 42),
        macd_signal=config_params.get("macd_signal", 9),
        natr_length=config_params.get("natr_length", 14),
    )
    features = compute_pmm_dynamic_features(candles, feat_config)

    field_map = {
        "reference_price": features.reference_price,
        "spread_multiplier": features.spread_multiplier,
        "natr": features.natr,
        "macd_signal_z": features.macd_signal_z,
        "price_multiplier": features.price_multiplier,
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
                    "expected": exp_val, "actual": None,
                    "diff": float('inf'),
                })
                continue

            actual_val = float(arr[bar])

            if np.isnan(exp_val) and np.isnan(actual_val):
                continue  # both NaN = match

            abs_diff = abs(actual_val - exp_val)
            rel_diff = abs_diff / abs(exp_val) if abs(exp_val) > 1e-15 else abs_diff

            max_abs = max(max_abs, abs_diff)
            max_rel = max(max_rel, rel_diff)

            if abs_diff > abs_tol and rel_diff > rel_tol:
                mismatches.append({
                    "bar": bar, "field": field_name,
                    "expected": exp_val, "actual": actual_val,
                    "diff": abs_diff,
                })

    return ParityResult(
        passed=len(mismatches) == 0,
        mode="frozen",
        mismatches=mismatches,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
    )


def check_feature_parity_native(
    candles: np.ndarray,
    config_params: Dict[str, Any],
    abs_tol: float = 1e-8,
    rel_tol: float = 1e-6,
) -> ParityResult:
    """Compare local features against native Hummingbot controller logic.

    This replicates the exact computation from
    app/controllers/market_making/pmm_dynamic.py:update_processed_data()
    without requiring the full Hummingbot runtime, then compares against
    the pmm_lab feature engine.

    The live controller:
    1. Gets the last max_records candles
    2. Computes ta.natr(...) / 100
    3. Computes ta.macd(...)
    4. Z-scores MACD: -(macd - macd.mean()) / macd.std()
    5. Computes macdh sign: 1 if macdh > 0 else -1
    6. price_multiplier = (0.5 * macd_signal_z + 0.5 * macdh_sign) * natr / 2
    7. reference_price = close * (1 + price_multiplier)
    8. spread_multiplier = natr
    """
    import pandas as pd
    import pandas_ta as pta

    macd_fast = config_params.get("macd_fast", 21)
    macd_slow = config_params.get("macd_slow", 42)
    macd_signal = config_params.get("macd_signal", 9)
    natr_length = config_params.get("natr_length", 14)
    max_records = max(macd_fast, macd_slow, macd_signal, natr_length) + 100

    # Compute lab features
    from pmm_lab.features.pmm_dynamic_features import compute_pmm_dynamic_features, PMMDynamicConfig
    feat_config = PMMDynamicConfig(
        macd_fast=macd_fast, macd_slow=macd_slow,
        macd_signal=macd_signal, natr_length=natr_length,
        controller_compat=True,
    )
    lab_features = compute_pmm_dynamic_features(candles, feat_config)

    # Compute native controller features by replicating the controller logic
    n = len(candles)
    warmup_end = lab_features.warmup_end

    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    close_s = pd.Series(candles["close"].astype("float64"))
    close_arr = candles["close"].astype("float64")

    native_reference_price = np.full(n, np.nan, dtype="float64")
    native_spread_multiplier = np.full(n, np.nan, dtype="float64")

    for t in range(warmup_end, n):
        start = max(0, t - max_records + 1)
        w_high = high.iloc[start:t+1]
        w_low = low.iloc[start:t+1]
        w_close = close_s.iloc[start:t+1]

        # Exactly replicate controller: ta.natr / 100
        w_natr = pta.natr(w_high, w_low, w_close, length=natr_length) / 100.0

        # Exactly replicate controller: ta.macd
        w_macd_out = pta.macd(w_close, fast=macd_fast, slow=macd_slow, signal=macd_signal)
        macd_col = f"MACD_{macd_fast}_{macd_slow}_{macd_signal}"
        macdh_col = f"MACDh_{macd_fast}_{macd_slow}_{macd_signal}"
        w_macd = w_macd_out[macd_col]
        w_macdh = w_macd_out[macdh_col]

        # Controller: macd_signal = -(macd - macd.mean()) / macd.std()
        m_mean = w_macd.mean()
        m_std = w_macd.std()  # pandas default ddof=1
        if m_std > 0:
            macd_z = -(float(w_macd.iloc[-1]) - m_mean) / m_std
        else:
            macd_z = 0.0

        # Controller: macdh_signal = 1 if x > 0 else -1
        macdh_sign = 1.0 if float(w_macdh.iloc[-1]) > 0 else -1.0

        natr_val = float(w_natr.iloc[-1]) if not pd.isna(w_natr.iloc[-1]) else 0.0
        max_price_shift = natr_val / 2.0
        price_mult = (0.5 * macd_z + 0.5 * macdh_sign) * max_price_shift

        native_spread_multiplier[t] = natr_val
        native_reference_price[t] = close_arr[t] * (1.0 + price_mult)

    # Compare lab vs native
    mismatches = []
    max_abs = 0.0
    max_rel = 0.0

    for t in range(warmup_end, n):
        for field_name, lab_arr, native_arr in [
            ("reference_price", lab_features.reference_price, native_reference_price),
            ("spread_multiplier", lab_features.spread_multiplier, native_spread_multiplier),
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
                    "expected": native_val, "actual": lab_val,
                    "diff": abs_diff,
                })

    return ParityResult(
        passed=len(mismatches) == 0,
        mode="native",
        mismatches=mismatches,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
    )
