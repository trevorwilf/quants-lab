"""Tests for MR BB+RSI feature computation."""

import numpy as np
import pytest

from pmm_lab.features.mean_reversion_bb_rsi_features import (
    MRBBRSIFeatureConfig,
    compute_mr_bb_rsi_features,
)
from pmm_lab.sim.strategy import SignalOutput
from tests.conftest import CANDLE_DTYPE


def _make_candles(n: int = 1500, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.8)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.3))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.3))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.05, 3.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def candles():
    return _make_candles()


@pytest.fixture
def config():
    return MRBBRSIFeatureConfig(
        bb_length=20,
        bb_std=2.0,
        bbp_entry_threshold=0.5,  # relaxed to produce some entries in synthetic data
        rsi_length=14,
        rsi_entry_threshold=60.0,
        use_trend_filter=False,
        trend_ema_length=50,
        atr_length=14,
        max_atr_pct_for_entry=0.5,  # relaxed
        volume_filter_window=48,
        min_volume_quantile=0.0,
        controller_compat=False,
    )


class TestContract:
    def test_returns_signal_output(self, candles, config):
        result = compute_mr_bb_rsi_features(candles, config)
        assert isinstance(result, SignalOutput)

    def test_required_keys_present(self, candles, config):
        result = compute_mr_bb_rsi_features(candles, config)
        for key in ("signal", "bbp", "rsi", "atr_pct", "ema_slope", "volume_ok", "close_price", "timestamp"):
            assert key in result.data, f"missing key: {key}"

    def test_array_lengths_match(self, candles, config):
        result = compute_mr_bb_rsi_features(candles, config)
        for key, arr in result.data.items():
            assert len(arr) == len(candles), f"{key} length mismatch"


class TestSignalValues:
    def test_signal_only_zero_or_one_or_nan(self, candles, config):
        result = compute_mr_bb_rsi_features(candles, config)
        sig = result.data["signal"]
        # Allowed: 0.0, 1.0. We don't produce NaN here but we allow it.
        allowed_mask = (sig == 0.0) | (sig == 1.0) | np.isnan(sig)
        assert allowed_mask.all()

    def test_warmup_has_no_positive_signal(self, candles, config):
        result = compute_mr_bb_rsi_features(candles, config)
        warmup_region = result.data["signal"][:result.warmup_end]
        # Either 0 or nan in warmup
        assert np.all((warmup_region == 0.0) | np.isnan(warmup_region))


class TestDeterminism:
    def test_repeat_same_output(self, candles, config):
        r1 = compute_mr_bb_rsi_features(candles, config)
        r2 = compute_mr_bb_rsi_features(candles, config)
        for key in r1.data:
            a = r1.data[key]
            b = r2.data[key]
            if a.dtype.kind in ("f",):
                # NaN-safe comparison
                both_nan = np.isnan(a) & np.isnan(b)
                eq = (a == b) | both_nan
                assert eq.all(), f"{key} diverges between runs"
            else:
                assert (a == b).all()


class TestNoLookahead:
    def test_flip_future_close_does_not_alter_current_signal(self, candles, config):
        """If we mutate the close at bar t, the signal at bars <= t must not change.

        Because timestamp_mode='open' shifts signals forward by 1, mutating close[t]
        should affect signal[t+1] onwards but NOT signal[0..t].
        """
        result1 = compute_mr_bb_rsi_features(candles, config)

        # Choose a bar past warmup with a reasonable amount of history
        mutate_idx = len(candles) - 10
        assert mutate_idx > result1.warmup_end + 10

        mutated = candles.copy()
        mutated["close"][mutate_idx] = mutated["close"][mutate_idx] * 1.5  # big shock

        result2 = compute_mr_bb_rsi_features(mutated, config)

        sig1 = result1.data["signal"]
        sig2 = result2.data["signal"]
        # Under 'open' shift, mutating close[mutate_idx] affects indicators that
        # would have been produced for bar mutate_idx; after the shift those land
        # at bar mutate_idx+1. So signals at indices <= mutate_idx must be identical.
        # We use 'mutate_idx' as the cutoff.
        for i in range(mutate_idx + 1):
            if np.isnan(sig1[i]) and np.isnan(sig2[i]):
                continue
            assert sig1[i] == sig2[i], f"signal[{i}] changed after mutating close[{mutate_idx}]"
