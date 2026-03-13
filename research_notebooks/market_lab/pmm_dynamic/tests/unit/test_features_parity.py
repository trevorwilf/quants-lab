"""Tests for PMM Dynamic feature computation."""

import numpy as np
import pytest

from pmm_lab.features.pmm_dynamic_features import (
    compute_pmm_dynamic_features,
    PMMDynamicConfig,
)


def test_feature_output_shapes(sample_candles_5m):
    """All output arrays have length 100 and warmup_end is reasonable."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    assert len(features.reference_price) == 100
    assert len(features.spread_multiplier) == 100
    assert len(features.natr) == 100
    assert len(features.macd_raw) == 100
    assert len(features.macd_signal_z) == 100
    assert len(features.macdh) == 100
    assert len(features.macdh_sign) == 100
    assert len(features.price_multiplier) == 100
    # warmup_end should be around 51 for default params (max(42,14)+9=51)
    assert 45 <= features.warmup_end <= 55


def test_natr_positive_after_warmup(sample_candles_5m):
    """NATR is positive and finite after warmup."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    natr_valid = features.natr[features.warmup_end:]
    assert np.all(natr_valid > 0)
    assert np.all(np.isfinite(natr_valid))


def test_spread_multiplier_equals_natr(sample_candles_5m):
    """spread_multiplier == natr after warmup."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    w = features.warmup_end
    np.testing.assert_array_equal(
        features.spread_multiplier[w:], features.natr[w:]
    )


def test_reference_price_near_close(sample_candles_5m):
    """reference_price is within ±5% of close after warmup."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    w = features.warmup_end
    close = sample_candles_5m["close"][w:]
    ref = features.reference_price[w:]
    ratio = ref / close
    assert np.all(ratio > 0.95)
    assert np.all(ratio < 1.05)


def test_macdh_sign_is_plus_minus_one(sample_candles_5m):
    """macdh_sign contains only +1.0 and -1.0 after warmup."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    w = features.warmup_end
    signs = features.macdh_sign[w:]
    unique_vals = set(signs)
    assert unique_vals <= {1.0, -1.0}


def test_warmup_bars_are_nan(sample_candles_5m):
    """All feature arrays contain NaN for bars 0 through warmup_end - 1."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    w = features.warmup_end
    for arr in (features.reference_price, features.spread_multiplier,
                features.natr, features.macd_raw, features.macd_signal_z,
                features.macdh, features.macdh_sign, features.price_multiplier):
        assert np.all(np.isnan(arr[:w])), f"Expected all NaN before warmup_end={w}"


def test_golden_values_bar60(sample_candles_5m):
    """Golden values at bar 60 match frozen reference."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    np.testing.assert_allclose(features.reference_price[60], 99613.79598938077, rtol=1e-10)
    np.testing.assert_allclose(features.spread_multiplier[60], 0.0007348990530329418, rtol=1e-10)
    np.testing.assert_allclose(features.natr[60], 0.0007348990530329418, rtol=1e-10)
    np.testing.assert_allclose(features.price_multiplier[60], 0.0003716192872574744, rtol=1e-10)


def test_golden_values_bar80(sample_candles_5m):
    """Golden values at bar 80 match frozen reference."""
    features = compute_pmm_dynamic_features(sample_candles_5m)
    np.testing.assert_allclose(features.reference_price[80], 99680.50967958754, rtol=1e-10)
    np.testing.assert_allclose(features.spread_multiplier[80], 0.0007282213859069458, rtol=1e-10)
    np.testing.assert_allclose(features.natr[80], 0.0007282213859069458, rtol=1e-10)
    np.testing.assert_allclose(features.price_multiplier[80], -0.0003652900500905005, rtol=1e-10)


def test_no_lookahead_macd_z(sample_candles_5m):
    """macd_signal_z at bar 99 is identical whether computed on 100 or 200 bars."""
    candles_100 = sample_candles_5m[:100]
    candles_200 = np.concatenate([sample_candles_5m, sample_candles_5m[:100]])
    f100 = compute_pmm_dynamic_features(candles_100)
    f200 = compute_pmm_dynamic_features(candles_200)
    assert abs(f100.macd_signal_z[99] - f200.macd_signal_z[99]) < 1e-10, (
        f"Look-ahead detected: {f100.macd_signal_z[99]} vs {f200.macd_signal_z[99]}"
    )


def test_too_short_raises():
    """Array too short for warmup raises ValueError."""
    from tests.conftest import CANDLE_DTYPE
    rng = np.random.default_rng(seed=1)
    n = 30
    rows = []
    for i in range(n):
        rows.append((1000 + i * 300, 100.0, 101.0, 99.0, 100.5, 1.0, False))
    candles = np.array(rows, dtype=CANDLE_DTYPE)
    with pytest.raises(ValueError, match="at least"):
        compute_pmm_dynamic_features(candles)


def test_custom_config(sample_candles_5m):
    """Custom config changes warmup_end."""
    config = PMMDynamicConfig(macd_fast=12, macd_slow=26, macd_signal=9, natr_length=20)
    features = compute_pmm_dynamic_features(sample_candles_5m, config=config)
    # warmup_end = max(26, 20) + 9 + 1 = 36
    assert features.warmup_end == 36
