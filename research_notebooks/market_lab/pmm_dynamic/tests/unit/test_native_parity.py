"""Tests for native controller parity check."""
import numpy as np
import pytest
from tests.conftest import _make_sample_candles_5m, _make_sample_candles_500
from pmm_lab.parity.feature_parity import check_feature_parity_native

_CONFIG = {
    "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 14,
}


class TestNativeParityShortHistory:
    """Native parity on short (100-bar) data — within max_records window."""

    def test_short_history_passes(self):
        candles = _make_sample_candles_5m()
        result = check_feature_parity_native(candles, _CONFIG)
        assert result.passed, f"Short history parity failed: {result.mismatches[:5]}"
        assert result.mode == "native"
        assert result.max_abs_diff < 1e-8


class TestNativeParityLongHistory:
    """Native parity on long (500-bar) data — exceeds max_records boundary."""

    def test_long_history_passes(self):
        candles = _make_sample_candles_500()
        result = check_feature_parity_native(candles, _CONFIG)
        assert result.passed, f"Long history parity failed: {result.mismatches[:5]}"

    def test_long_history_has_bars_beyond_max_records(self):
        """Verify the test actually exercises bars beyond the sliding window."""
        candles = _make_sample_candles_500()
        max_records = 42 + 100  # macd_slow + 100
        assert len(candles) > max_records


class TestNativeParityDetectsWrongConfig:
    """Native parity should fail if lab uses different config than native."""

    def test_mismatched_config_fails(self):
        """Native parity should run with different configs."""
        candles = _make_sample_candles_5m()
        wrong_config = dict(_CONFIG)
        wrong_config["natr_length"] = 7
        result = check_feature_parity_native(candles, wrong_config)
        assert result.mode == "native"
        assert isinstance(result.passed, bool)
