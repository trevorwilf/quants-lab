"""
Feature parity checker.

Compares local pmm_lab feature computation against:
1. Frozen fixture values (always available)
2. Native Hummingbot controller output (when Hummingbot installed)
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
) -> ParityResult:
    """Compare local features against native Hummingbot controller.

    Only works when Hummingbot is installed.

    Raises ImportError if Hummingbot is not available.
    """
    from pmm_lab.parity import HAS_HUMMINGBOT
    if not HAS_HUMMINGBOT:
        raise ImportError(
            "Hummingbot is not installed. Cannot run native parity check. "
            "Use check_feature_parity_frozen() instead."
        )

    # Placeholder for when Hummingbot is in the environment.
    return ParityResult(
        passed=False,
        mode="native",
        mismatches=[{"bar": -1, "field": "native", "expected": "implemented",
                     "actual": "not_implemented", "diff": 0}],
        max_abs_diff=0.0,
        max_rel_diff=0.0,
    )
