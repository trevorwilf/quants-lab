"""Tests for candle validation."""

import numpy as np
import pytest

from pmm_lab.data.candles import validate_candles


def test_clean_data_passes_strict(sample_candles_5m):
    """Clean data passes strict audit."""
    audit = validate_candles(sample_candles_5m, "5m", strict=True)
    assert audit.passed_strict is True
    assert audit.failure_reasons == []


def test_ohlc_violations_detected(sample_candles_with_violations):
    """OHLC violations are detected and counted."""
    audit = validate_candles(sample_candles_with_violations, "5m", strict=True)
    # Row 5: high < close, Row 10: low > open
    assert audit.ohlc_violations >= 2
    assert len(audit.ohlc_violation_details) > 0


def test_non_positive_price_fails_strict(sample_candles_with_violations):
    """Non-positive OHLC values cause strict failure."""
    audit = validate_candles(sample_candles_with_violations, "5m", strict=True)
    assert audit.passed_strict is False
    assert any("non-positive OHLC" in r for r in audit.failure_reasons)


def test_duplicate_timestamps_detected(sample_candles_with_duplicates):
    """Duplicate timestamps are counted."""
    audit = validate_candles(sample_candles_with_duplicates, "5m", strict=True)
    assert audit.duplicate_count == 1


def test_gap_histogram_correct(sample_candles_with_gaps):
    """Gap histogram includes the 1800-second gap."""
    audit = validate_candles(sample_candles_with_gaps, "5m", strict=True)
    assert 1800 + 300 in audit.gap_histogram  # gap of 7*300=2100 between rows 24 and 25


def test_expected_row_count_and_missing(sample_candles_with_gaps):
    """Expected rows > total_rows and missing_rows matches gap."""
    audit = validate_candles(sample_candles_with_gaps, "5m", strict=True)
    assert audit.expected_rows > audit.total_rows
    assert audit.missing_rows > 0


def test_volume_zero_count(sample_candles_with_violations):
    """Volume=0 candles are counted (row 18)."""
    audit = validate_candles(sample_candles_with_violations, "5m", strict=True)
    assert audit.volume_zero_count >= 1


def test_monotonicity_check():
    """Non-monotonic timestamps fail strict audit."""
    from tests.conftest import CANDLE_DTYPE
    rows = []
    for i in range(50):
        rows.append((1000 + i * 300, 100.0, 101.0, 99.0, 100.0, 1.0, False))
    # Swap two timestamps to break monotonicity
    candles = np.array(rows, dtype=CANDLE_DTYPE)
    candles["timestamp"][25] = candles["timestamp"][24]  # duplicate/non-increasing
    audit = validate_candles(candles, "5m", strict=True)
    assert audit.passed_strict is False
    assert any("monotonic" in r.lower() for r in audit.failure_reasons)


def test_longest_gap_detected(sample_candles_with_gaps):
    """Longest gap is detected correctly."""
    audit = validate_candles(sample_candles_with_gaps, "5m", strict=True)
    # The gap between rows 24 and 25 is (6+1)*300 = 2100s
    assert audit.longest_gap_seconds == 2100
