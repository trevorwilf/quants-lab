"""Tests for MACD-BB feature parity."""

import numpy as np
import pytest

from pmm_lab.parity.macd_bb_parity import (
    check_macd_bb_parity_frozen,
    check_macd_bb_parity_native,
)
from pmm_lab.features.macd_bb_features import compute_macd_bb_features, MACDBBFeatureConfig
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=300, seed=42):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1756833000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 100)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 40))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 40))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.1, 3.0)
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def candles():
    return _make_candles(300, seed=42)


@pytest.fixture
def config_params():
    return {
        "bb_length": 20,
        "bb_std": 2.0,
        "bb_long_threshold": 0.2,
        "bb_short_threshold": 0.8,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
    }


class TestFrozenParity:
    def test_frozen_parity_with_self(self, candles, config_params):
        """Generate features, use them as 'expected', verify parity."""
        feat_config = MACDBBFeatureConfig(
            bb_length=config_params["bb_length"],
            bb_std=config_params["bb_std"],
            bb_long_threshold=config_params["bb_long_threshold"],
            bb_short_threshold=config_params["bb_short_threshold"],
            macd_fast=config_params["macd_fast"],
            macd_slow=config_params["macd_slow"],
            macd_signal=config_params["macd_signal"],
            controller_compat=True,
            timestamp_mode="close",
        )
        result = compute_macd_bb_features(candles, feat_config)

        # Build frozen fixture from actual values at sample bars
        sample_bars = [result.warmup_end, result.warmup_end + 10,
                       result.warmup_end + 50, len(candles) - 1]
        expected = {}
        for bar in sample_bars:
            if bar < len(candles):
                expected[str(bar)] = {
                    "bbp": float(result.data["bbp"][bar]),
                    "macd": float(result.data["macd"][bar]),
                    "macdh": float(result.data["macdh"][bar]),
                    "signal": float(result.data["signal"][bar]),
                }

        parity = check_macd_bb_parity_frozen(candles, expected, config_params)
        assert parity.passed, f"Mismatches: {parity.mismatches}"
        assert parity.max_abs_diff < 1e-8


class TestNativeParity:
    def test_native_parity_passes(self, candles, config_params):
        """Controller-equivalent path should match lab features exactly."""
        parity = check_macd_bb_parity_native(candles, config_params)
        assert parity.passed, (
            f"Native parity failed with {len(parity.mismatches)} mismatches. "
            f"First 3: {parity.mismatches[:3]}"
        )

    def test_native_parity_with_default_params(self, candles):
        """Test with default controller parameters."""
        config = {
            "bb_length": 100,
            "bb_std": 2.0,
            "bb_long_threshold": 0.0,
            "bb_short_threshold": 1.0,
            "macd_fast": 21,
            "macd_slow": 42,
            "macd_signal": 9,
        }
        parity = check_macd_bb_parity_native(candles, config)
        assert parity.passed, (
            f"Native parity failed: {len(parity.mismatches)} mismatches, "
            f"max_abs={parity.max_abs_diff}"
        )


class TestCrossParamParity:
    def test_parity_with_various_params(self, candles):
        """Test parity across different parameter combinations."""
        param_sets = [
            {"bb_length": 20, "bb_std": 1.5, "bb_long_threshold": 0.1,
             "bb_short_threshold": 0.9, "macd_fast": 10, "macd_slow": 30, "macd_signal": 7},
            {"bb_length": 50, "bb_std": 2.5, "bb_long_threshold": -0.1,
             "bb_short_threshold": 1.1, "macd_fast": 15, "macd_slow": 40, "macd_signal": 12},
        ]
        for params in param_sets:
            parity = check_macd_bb_parity_native(candles, params)
            assert parity.passed, (
                f"Parity failed for {params}: {len(parity.mismatches)} mismatches"
            )
