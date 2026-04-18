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


# ────────────────────────────────────────────────────────────────────────────
# Directional parity (ML-DIR-009) — MR BB+RSI and EMA regime-hold variants.
# ────────────────────────────────────────────────────────────────────────────


def _compare_fields(
    field_map: Dict[str, Any],
    expected_features: Dict[str, Dict[str, float]],
    abs_tol: float,
    rel_tol: float,
    *,
    mode: str,
) -> ParityResult:
    """Shared comparison helper for MR and EMA parity checks.

    For each expected bar/field, look up the actual value in field_map and
    record any mismatch that exceeds both abs_tol and rel_tol.
    """
    mismatches = []
    max_abs = 0.0
    max_rel = 0.0
    for bar_str, expected in expected_features.items():
        bar = int(bar_str)
        for field_name, exp_val in expected.items():
            if field_name not in field_map or field_map[field_name] is None:
                continue
            arr = field_map[field_name]
            if hasattr(arr, "__len__") and bar >= len(arr):
                continue
            actual = float(arr[bar]) if hasattr(arr, "__len__") else float(arr)
            exp_f = float(exp_val) if not isinstance(exp_val, bool) else float(bool(exp_val))
            if np.isnan(exp_f) and np.isnan(actual):
                continue
            diff = abs(actual - exp_f)
            rel = diff / max(abs(exp_f), 1e-12)
            max_abs = max(max_abs, diff)
            max_rel = max(max_rel, rel)
            if diff > abs_tol and rel > rel_tol:
                mismatches.append({
                    "bar": bar, "field": field_name,
                    "expected": exp_f, "actual": actual, "diff": diff,
                })
    return ParityResult(
        passed=(len(mismatches) == 0),
        mode=mode,
        mismatches=mismatches,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
    )


def check_feature_parity_frozen_mr(
    candles: np.ndarray,
    expected_features: Dict[str, Dict[str, float]],
    config_params: Dict[str, Any],
    abs_tol: float = 1e-8,
    rel_tol: float = 1e-6,
) -> ParityResult:
    """Compare local MR BB+RSI features against frozen fixture values."""
    from pmm_lab.features.mean_reversion_bb_rsi_features import (
        compute_mr_bb_rsi_features, MRBBRSIFeatureConfig,
    )
    feat_cfg = MRBBRSIFeatureConfig(
        bb_length=int(config_params.get("bb_length", 20)),
        bb_std=float(config_params.get("bb_std", 2.0)),
        bbp_entry_threshold=float(config_params.get("bbp_entry_threshold", 0.15)),
        rsi_length=int(config_params.get("rsi_length", 14)),
        rsi_entry_threshold=float(config_params.get("rsi_entry_threshold", 35.0)),
        use_trend_filter=bool(config_params.get("use_trend_filter", True)),
        trend_ema_length=int(config_params.get("trend_ema_length", 100)),
        min_trend_slope=float(config_params.get("min_trend_slope", 0.0)),
        atr_length=int(config_params.get("atr_length", 14)),
        max_atr_pct_for_entry=float(config_params.get("max_atr_pct_for_entry", 0.05)),
        volume_filter_window=int(config_params.get("volume_filter_window", 288)),
        min_volume_quantile=float(config_params.get("min_volume_quantile", 0.3)),
        timestamp_mode=str(config_params.get("timestamp_mode", "open")),
        controller_compat=bool(config_params.get("controller_compat", True)),
    )
    features = compute_mr_bb_rsi_features(candles, feat_cfg)

    # SignalOutput.data keys from compute_mr_bb_rsi_features:
    # signal, bbp, rsi, atr_pct, ema_slope, volume_ok, close_price, timestamp
    field_map = {
        "signal": features.data.get("signal"),
        "bbp": features.data.get("bbp"),
        "rsi": features.data.get("rsi"),
        "atr_pct": features.data.get("atr_pct"),
        "ema_slope": features.data.get("ema_slope"),
        "volume_ok": features.data.get("volume_ok"),
    }
    return _compare_fields(field_map, expected_features, abs_tol, rel_tol, mode="frozen_mr")


def check_feature_parity_frozen_ema(
    candles: np.ndarray,
    regime_candles: np.ndarray,
    expected_features: Dict[str, Dict[str, float]],
    config_params: Dict[str, Any],
    abs_tol: float = 1e-8,
    rel_tol: float = 1e-6,
) -> ParityResult:
    """Compare local EMA regime-hold features against frozen fixture values."""
    from pmm_lab.features.ema_regime_hold_features import (
        compute_ema_regime_hold_features, EMARegimeHoldFeatureConfig,
    )
    feat_cfg = EMARegimeHoldFeatureConfig(
        regime_ema_fast=int(config_params.get("regime_ema_fast", 10)),
        regime_ema_slow=int(config_params.get("regime_ema_slow", 30)),
        regime_adx_length=int(config_params.get("regime_adx_length", 14)),
        regime_adx_threshold=float(config_params.get("regime_adx_threshold", 20.0)),
        volume_filter_window=int(config_params.get("volume_filter_window", 288)),
        min_volume_quantile=float(config_params.get("min_volume_quantile", 0.3)),
        hold_mode=str(config_params.get("hold_mode", "reentry")),
        timestamp_mode=str(config_params.get("timestamp_mode", "open")),
        controller_compat=bool(config_params.get("controller_compat", True)),
    )
    features = compute_ema_regime_hold_features(candles, regime_candles, feat_cfg)

    # SignalOutput.data keys from compute_ema_regime_hold_features:
    # signal, trend_on, vol_ok, close_price, timestamp
    field_map = {
        "signal": features.data.get("signal"),
        "trend_on": features.data.get("trend_on"),
        "vol_ok": features.data.get("vol_ok"),
    }
    return _compare_fields(field_map, expected_features, abs_tol, rel_tol, mode="frozen_ema")
