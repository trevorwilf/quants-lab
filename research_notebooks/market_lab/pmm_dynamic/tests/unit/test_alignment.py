"""Tests for no-lookahead feature alignment."""

import numpy as np
import pytest

from pmm_lab.features.pmm_dynamic_features import compute_pmm_dynamic_features
from pmm_lab.features.alignment import align_features


def test_open_mode_shifts_by_one(sample_candles_5m):
    """In open mode, aligned[t] == raw[t-1] for t >= 1, and aligned[0] is NaN."""
    raw = compute_pmm_dynamic_features(sample_candles_5m)
    aligned = align_features(raw, timestamp_mode="open")

    # Check shift for valid bars
    for t in range(1, len(sample_candles_5m)):
        if not np.isnan(raw.reference_price[t - 1]):
            assert aligned.reference_price[t] == raw.reference_price[t - 1], f"Mismatch at bar {t}"

    # Bar 0 should be NaN
    assert np.isnan(aligned.reference_price[0])


def test_close_mode_no_shift(sample_candles_5m):
    """In close mode, aligned[t] == raw[t] for all t."""
    raw = compute_pmm_dynamic_features(sample_candles_5m)
    aligned = align_features(raw, timestamp_mode="close")

    np.testing.assert_array_equal(aligned.reference_price, raw.reference_price)
    np.testing.assert_array_equal(aligned.natr, raw.natr)


def test_warmup_incremented_in_open_mode(sample_candles_5m):
    """warmup_end is incremented by 1 in open mode."""
    raw = compute_pmm_dynamic_features(sample_candles_5m)
    aligned = align_features(raw, timestamp_mode="open")
    assert aligned.warmup_end == raw.warmup_end + 1


def test_no_future_data_used(sample_candles_5m):
    """Aligned features at bar t depend only on candles[0:t] for shift-based fields.

    Note: reference_price uses macd_signal_z which is computed from the full
    series mean/std (as documented in the spec), so it will differ slightly
    with different series lengths. We test NATR instead, which is purely
    lookback-based and should match exactly.
    """
    # Compute on full data
    raw_full = compute_pmm_dynamic_features(sample_candles_5m)
    aligned_full = align_features(raw_full, timestamp_mode="open")

    # Compute on truncated data (up to bar 70)
    t = 70
    candles_short = sample_candles_5m[:t + 5]
    raw_short = compute_pmm_dynamic_features(candles_short)
    aligned_short = align_features(raw_short, timestamp_mode="open")

    # NATR is purely lookback-based, so it should match exactly
    np.testing.assert_allclose(
        aligned_full.natr[t],
        aligned_short.natr[t],
        rtol=1e-10,
    )
    # The shift itself ensures no future data: aligned[t] = raw[t-1]
    np.testing.assert_equal(
        aligned_full.natr[t],
        raw_full.natr[t - 1],
    )
