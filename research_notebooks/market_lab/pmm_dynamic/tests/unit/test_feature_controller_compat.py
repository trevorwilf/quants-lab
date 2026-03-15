"""Tests for controller_compat mode in feature engine."""

import numpy as np
import pandas as pd
import pandas_ta as ta
import pytest

from tests.conftest import _make_sample_candles_500, _make_sample_candles_5m
from pmm_lab.features.pmm_dynamic_features import (
    compute_pmm_dynamic_features, PMMDynamicConfig, PMMDynamicFeatures,
)


class TestControllerCompatModeDefault:
    def test_controller_compat_mode_default(self):
        """PMMDynamicConfig().controller_compat is True by default."""
        config = PMMDynamicConfig()
        assert config.controller_compat is True


class TestControllerCompatShortHistoryMatchesFull:
    def test_controller_compat_short_history_matches_full(self):
        """For candles shorter than max_records, both modes produce identical results (within 1e-6)."""
        candles = _make_sample_candles_5m()  # 100 bars
        config_compat = PMMDynamicConfig(controller_compat=True)
        config_full = PMMDynamicConfig(controller_compat=False)

        feat_compat = compute_pmm_dynamic_features(candles, config_compat)
        feat_full = compute_pmm_dynamic_features(candles, config_full)

        warmup = feat_compat.warmup_end

        # For short history (< max_records=142), both modes should produce very close results
        for t in range(warmup, len(candles)):
            if np.isnan(feat_compat.reference_price[t]) or np.isnan(feat_full.reference_price[t]):
                continue
            assert abs(feat_compat.reference_price[t] - feat_full.reference_price[t]) < 1e-6, (
                f"Diverged at bar {t}: compat={feat_compat.reference_price[t]}, full={feat_full.reference_price[t]}"
            )


class TestControllerCompatLongHistoryDivergesFromFull:
    def test_controller_compat_long_history_diverges_from_full(self):
        """For 500 bars, controller_compat and full-history modes produce DIFFERENT results after max_records."""
        candles = _make_sample_candles_500()  # 500 bars
        config_compat = PMMDynamicConfig(controller_compat=True)
        config_full = PMMDynamicConfig(controller_compat=False)

        feat_compat = compute_pmm_dynamic_features(candles, config_compat)
        feat_full = compute_pmm_dynamic_features(candles, config_full)

        max_records = max(config_compat.macd_fast, config_compat.macd_slow,
                         config_compat.macd_signal, config_compat.natr_length) + 100

        # After max_records, the modes should diverge
        diffs_after = []
        for t in range(max_records, len(candles)):
            if np.isnan(feat_compat.reference_price[t]) or np.isnan(feat_full.reference_price[t]):
                continue
            d = abs(feat_compat.reference_price[t] - feat_full.reference_price[t])
            diffs_after.append(d)

        assert len(diffs_after) > 0, "No valid bars after max_records to compare"
        assert max(diffs_after) > 0.01, (
            f"Modes should diverge after max_records but max diff was only {max(diffs_after):.8f}"
        )


class TestControllerCompatMatchesManualSlidingWindow:
    def test_controller_compat_matches_manual_sliding_window(self):
        """Verify reference_price matches a manual controller emulation at every bar within 1e-8."""
        candles = _make_sample_candles_500()
        config = PMMDynamicConfig(controller_compat=True)

        feat = compute_pmm_dynamic_features(candles, config)
        manual_ref = _compute_controller_reference(candles, config)

        warmup = feat.warmup_end
        matches = 0
        for t in range(warmup, len(candles)):
            if np.isnan(feat.reference_price[t]) and np.isnan(manual_ref[t]):
                continue
            if np.isnan(feat.reference_price[t]) or np.isnan(manual_ref[t]):
                pytest.fail(f"NaN mismatch at bar {t}: feat={feat.reference_price[t]}, manual={manual_ref[t]}")
            assert abs(feat.reference_price[t] - manual_ref[t]) < 1e-8, (
                f"Mismatch at bar {t}: feat={feat.reference_price[t]}, manual={manual_ref[t]}"
            )
            matches += 1

        assert matches > 100, f"Only {matches} bars compared — expected more"


class TestControllerCompatNatrMatches:
    def test_controller_compat_natr_matches(self):
        """Verify NATR values match between sliding window and controller compat mode."""
        candles = _make_sample_candles_500()
        config = PMMDynamicConfig(controller_compat=True)

        feat = compute_pmm_dynamic_features(candles, config)

        max_records = max(config.macd_fast, config.macd_slow, config.macd_signal, config.natr_length) + 100
        warmup = feat.warmup_end

        high = pd.Series(candles["high"].astype("float64"))
        low = pd.Series(candles["low"].astype("float64"))
        close = pd.Series(candles["close"].astype("float64"))

        for t in range(warmup, len(candles)):
            start = max(0, t - max_records + 1)
            w_h = high.iloc[start:t+1]
            w_l = low.iloc[start:t+1]
            w_c = close.iloc[start:t+1]

            w_natr = ta.natr(w_h, w_l, w_c, length=config.natr_length) / 100.0
            expected_natr = float(w_natr.iloc[-1]) if not pd.isna(w_natr.iloc[-1]) else np.nan

            if np.isnan(feat.natr[t]) and np.isnan(expected_natr):
                continue
            assert abs(feat.natr[t] - expected_natr) < 1e-10, (
                f"NATR mismatch at bar {t}: feat={feat.natr[t]}, expected={expected_natr}"
            )


class TestControllerCompatDeterministic:
    def test_controller_compat_deterministic(self):
        """Two runs produce identical arrays."""
        candles = _make_sample_candles_500()
        config = PMMDynamicConfig(controller_compat=True)

        feat1 = compute_pmm_dynamic_features(candles, config)
        feat2 = compute_pmm_dynamic_features(candles, config)

        np.testing.assert_array_equal(feat1.reference_price, feat2.reference_price)
        np.testing.assert_array_equal(feat1.spread_multiplier, feat2.spread_multiplier)
        np.testing.assert_array_equal(feat1.natr, feat2.natr)
        np.testing.assert_array_equal(feat1.macd_raw, feat2.macd_raw)
        np.testing.assert_array_equal(feat1.macd_signal_z, feat2.macd_signal_z)
        np.testing.assert_array_equal(feat1.macdh, feat2.macdh)
        np.testing.assert_array_equal(feat1.macdh_sign, feat2.macdh_sign)
        np.testing.assert_array_equal(feat1.price_multiplier, feat2.price_multiplier)
        assert feat1.warmup_end == feat2.warmup_end


def _compute_controller_reference(candles, config):
    """Emulate controller logic: slide max_records window, recompute per bar."""
    max_records = max(config.macd_fast, config.macd_slow, config.macd_signal, config.natr_length) + 100
    n = len(candles)
    ref_prices = np.full(n, np.nan)

    high = pd.Series(candles["high"].astype("float64"))
    low = pd.Series(candles["low"].astype("float64"))
    close = pd.Series(candles["close"].astype("float64"))

    for t in range(n):
        start = max(0, t - max_records + 1)
        w_h = high.iloc[start:t+1]
        w_l = low.iloc[start:t+1]
        w_c = close.iloc[start:t+1]

        if len(w_c) < max(config.macd_slow, config.natr_length) + config.macd_signal + 1:
            continue

        natr = ta.natr(w_h, w_l, w_c, length=config.natr_length) / 100.0
        macd_out = ta.macd(w_c, fast=config.macd_fast, slow=config.macd_slow, signal=config.macd_signal)
        macd = macd_out[f"MACD_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"]
        macdh = macd_out[f"MACDh_{config.macd_fast}_{config.macd_slow}_{config.macd_signal}"]

        macd_mean = macd.mean()
        macd_std = macd.std(ddof=1)
        macd_z = -(macd.iloc[-1] - macd_mean) / macd_std if macd_std > 0 else 0.0
        macdh_sign = 1.0 if macdh.iloc[-1] > 0 else -1.0

        max_shift = natr.iloc[-1] / 2.0 if not pd.isna(natr.iloc[-1]) else 0.0
        price_mult = (0.5 * macd_z + 0.5 * macdh_sign) * max_shift
        ref_prices[t] = float(w_c.iloc[-1]) * (1.0 + price_mult)

    return ref_prices
