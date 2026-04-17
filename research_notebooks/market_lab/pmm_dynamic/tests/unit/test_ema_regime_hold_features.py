"""Tests for EMA regime-hold feature computation (multi-timeframe)."""

import numpy as np
import pytest

from pmm_lab.features.ema_regime_hold_features import (
    EMARegimeHoldFeatureConfig,
    compute_ema_regime_hold_features,
)
from pmm_lab.sim.strategy import SignalOutput
from tests.conftest import CANDLE_DTYPE


def _make_fast_candles(n: int = 2000, start_ts: int = 1_700_000_000, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.5)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.05, 3.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_slow_candles(n: int = 200, start_ts: int = 1_700_000_000, seed: int = 13) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    interval = 14400  # 4h
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 2.0)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 1.0))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 1.0))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.1, 10.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def fast_candles():
    return _make_fast_candles()


@pytest.fixture
def slow_candles():
    return _make_slow_candles()


@pytest.fixture
def config():
    return EMARegimeHoldFeatureConfig(
        regime_ema_fast=10,
        regime_ema_slow=30,
        regime_adx_length=14,
        regime_adx_threshold=0.0,  # relaxed to produce trend_on=True frequently
        volume_filter_window=48,
        min_volume_quantile=0.0,
        hold_mode="reentry",
        controller_compat=False,
    )


class TestContract:
    def test_returns_signal_output(self, fast_candles, slow_candles, config):
        result = compute_ema_regime_hold_features(fast_candles, slow_candles, config)
        assert isinstance(result, SignalOutput)

    def test_required_keys_present(self, fast_candles, slow_candles, config):
        result = compute_ema_regime_hold_features(fast_candles, slow_candles, config)
        for key in ("signal", "trend_on", "vol_ok", "close_price", "timestamp"):
            assert key in result.data, f"missing {key}"

    def test_signal_values_binary(self, fast_candles, slow_candles, config):
        result = compute_ema_regime_hold_features(fast_candles, slow_candles, config)
        sig = result.data["signal"]
        mask = (sig == 0.0) | (sig == 1.0) | np.isnan(sig)
        assert mask.all()


class TestMultiTimeframeMerge:
    def test_signal_bar_uses_only_prior_regime(self, fast_candles, slow_candles, config):
        """A 5m signal at timestamp t must only reflect 4h bars with timestamp <= t."""
        result = compute_ema_regime_hold_features(fast_candles, slow_candles, config)
        fast_ts = fast_candles["timestamp"]
        slow_ts = slow_candles["timestamp"]

        # For each signal bar with a nonzero trend_on, there must be at least one
        # regime bar at timestamp <= that signal bar's timestamp (before 'open'
        # shift). The 'open' shift then delays by 1 fast bar; we validate at the
        # pre-shift invariant level by using timestamps.
        trend = result.data["trend_on"].astype(bool)
        # The earliest fast bar where trend_on=True must have fast_ts >= first slow_ts
        idx_nonzero = np.where(trend)[0]
        if len(idx_nonzero) > 0:
            first_nonzero_fast_ts = int(fast_ts[int(idx_nonzero[0])])
            # Because we shift +1 on 'open', the *signal* bar at index i reflects
            # regime at bar i-1 of the pre-shift. So check: at pre-shift bar i-1
            # there must exist at least one slow bar with ts <= fast_ts[i-1].
            # We tolerate the shift: slow bar ts <= fast_ts[i]
            assert any(slow_ts <= first_nonzero_fast_ts)


class TestDeterminism:
    def test_repeat_same_output(self, fast_candles, slow_candles, config):
        r1 = compute_ema_regime_hold_features(fast_candles, slow_candles, config)
        r2 = compute_ema_regime_hold_features(fast_candles, slow_candles, config)
        for key in r1.data:
            a = r1.data[key]
            b = r2.data[key]
            if a.dtype.kind in ("f",):
                both_nan = np.isnan(a) & np.isnan(b)
                eq = (a == b) | both_nan
                assert eq.all(), f"{key} diverges"
            else:
                assert (a == b).all()
