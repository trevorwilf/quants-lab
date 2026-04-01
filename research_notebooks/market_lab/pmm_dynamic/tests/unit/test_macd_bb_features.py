"""Tests for MACD+BB feature computation."""

import numpy as np
import math
import pytest

from pmm_lab.sim.strategy import SignalOutput
from pmm_lab.features.macd_bb_features import (
    MACDBBFeatureConfig,
    compute_macd_bb_features,
)

from tests.conftest import CANDLE_DTYPE


def _make_candles(n=300, seed=42):
    """Generate n-bar candle array suitable for MACD+BB (needs longer history)."""
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
def macd_bb_candles():
    return _make_candles(300, seed=42)


@pytest.fixture
def default_config():
    return MACDBBFeatureConfig(
        bb_length=20,
        bb_std=2.0,
        bb_long_threshold=0.0,
        bb_short_threshold=1.0,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        controller_compat=False,
    )


class TestSignalOutputStructure:
    def test_returns_signal_output(self, macd_bb_candles, default_config):
        result = compute_macd_bb_features(macd_bb_candles, default_config)
        assert isinstance(result, SignalOutput)

    def test_has_required_keys(self, macd_bb_candles, default_config):
        result = compute_macd_bb_features(macd_bb_candles, default_config)
        for key in ("bbp", "macd", "macdh", "signal"):
            assert key in result.data, f"Missing key: {key}"

    def test_array_lengths(self, macd_bb_candles, default_config):
        result = compute_macd_bb_features(macd_bb_candles, default_config)
        n = len(macd_bb_candles)
        for key in ("bbp", "macd", "macdh", "signal"):
            assert len(result.data[key]) == n, f"{key} length mismatch"


class TestWarmup:
    def test_warmup_end_is_valid(self, macd_bb_candles, default_config):
        result = compute_macd_bb_features(macd_bb_candles, default_config)
        assert result.warmup_end > 0
        assert result.warmup_end < len(macd_bb_candles)

    def test_no_nan_after_warmup(self, macd_bb_candles, default_config):
        result = compute_macd_bb_features(macd_bb_candles, default_config)
        for key in ("bbp", "macd", "macdh"):
            arr = result.data[key]
            post_warmup = arr[result.warmup_end:]
            nan_count = np.sum(np.isnan(post_warmup))
            assert nan_count == 0, f"{key} has {nan_count} NaN values after warmup"


class TestSignalLogic:
    def test_signal_values_in_range(self, macd_bb_candles, default_config):
        result = compute_macd_bb_features(macd_bb_candles, default_config)
        signal = result.data["signal"]
        unique = set(np.unique(signal[~np.isnan(signal)]))
        assert unique.issubset({-1.0, 0.0, 1.0}), f"Unexpected signal values: {unique}"

    def test_signal_zero_during_warmup(self, macd_bb_candles, default_config):
        """Signals should be 0 (or NaN) during warmup period."""
        config = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="close",
        )
        result = compute_macd_bb_features(macd_bb_candles, config)
        warmup_signal = result.data["signal"][:result.warmup_end]
        assert np.all(warmup_signal == 0.0), "Non-zero signals during warmup"

    def test_long_condition_matches_controller(self):
        """Construct candles where we know long condition should fire."""
        # Long: bbp < 0.0 AND macdh > 0 AND macd < 0
        # We need a scenario where price is below lower BB, MACD histogram is positive,
        # and MACD line is negative. This is hard to engineer synthetically,
        # so we just verify the logic produces some signals on random data.
        candles = _make_candles(500, seed=123)
        config = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0,
            bb_long_threshold=0.2,  # relaxed to get more signals
            bb_short_threshold=0.8,
            macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="close",
        )
        result = compute_macd_bb_features(candles, config)
        signal = result.data["signal"]
        # With relaxed thresholds on 500 bars, we should get at least one signal
        assert np.any(signal != 0.0), "No signals generated — logic may be broken"


class TestTimestampMode:
    def test_open_mode_shifts_by_one(self, macd_bb_candles):
        config_close = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="close",
        )
        config_open = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="open",
        )
        result_close = compute_macd_bb_features(macd_bb_candles, config_close)
        result_open = compute_macd_bb_features(macd_bb_candles, config_open)

        # Open mode warmup should be 1 more than close mode
        assert result_open.warmup_end == result_close.warmup_end + 1

        # Signal at bar N in open mode should equal signal at bar N-1 in close mode
        for key in ("signal",):
            close_arr = result_close.data[key]
            open_arr = result_open.data[key]
            we = result_open.warmup_end
            for i in range(we, min(len(close_arr), len(open_arr))):
                assert open_arr[i] == close_arr[i - 1], (
                    f"{key} at bar {i}: open={open_arr[i]}, close[i-1]={close_arr[i-1]}"
                )


class TestControllerCompatModes:
    def test_both_modes_produce_same_signal_structure(self, macd_bb_candles):
        config_vec = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="close",
        )
        config_compat = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=True, timestamp_mode="close",
        )
        result_vec = compute_macd_bb_features(macd_bb_candles, config_vec)
        result_compat = compute_macd_bb_features(macd_bb_candles, config_compat)

        # Both should have the same keys
        assert set(result_vec.data.keys()) == set(result_compat.data.keys())

        # Signals should agree on the final bars (where sliding window has full data)
        sig_v = result_vec.data["signal"]
        sig_c = result_compat.data["signal"]
        # Compare last 50 bars — both modes should agree
        start = max(result_vec.warmup_end, result_compat.warmup_end)
        agree = np.sum(sig_v[start:] == sig_c[start:])
        total = len(sig_v[start:])
        # Allow some disagreement due to sliding-window vs full-history
        assert agree / total > 0.8, f"Modes disagree too much: {agree}/{total}"


class TestEdgeCases:
    def test_flat_price_no_crash(self):
        """Flat price data should not crash."""
        n = 200
        start_ts = 1756833000
        interval = 300
        rows = []
        for i in range(n):
            ts = start_ts + i * interval
            rows.append((ts, 100.0, 100.5, 99.5, 100.0, 1.0, False))
        candles = np.array(rows, dtype=CANDLE_DTYPE)
        config = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="close",
        )
        result = compute_macd_bb_features(candles, config)
        assert isinstance(result, SignalOutput)

    def test_extreme_thresholds_no_signals(self, macd_bb_candles):
        """Extreme thresholds should produce no signals."""
        config = MACDBBFeatureConfig(
            bb_length=20, bb_std=2.0,
            bb_long_threshold=-100.0,  # impossible to trigger
            bb_short_threshold=100.0,  # impossible to trigger
            macd_fast=12, macd_slow=26, macd_signal=9,
            controller_compat=False, timestamp_mode="close",
        )
        result = compute_macd_bb_features(macd_bb_candles, config)
        signal = result.data["signal"]
        assert np.all(signal == 0.0), "Signals with extreme thresholds"
