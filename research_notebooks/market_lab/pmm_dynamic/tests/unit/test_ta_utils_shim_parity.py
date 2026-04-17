"""Parity tests: pmm_lab ta_utils_shim vs hummingbot ta_utils.

Skipped if hummingbot is not on the import path. This is a developer
check, not a CI gate.
"""

import numpy as np
import pandas as pd
import pytest

from tests.conftest import CANDLE_DTYPE


hb_ta = pytest.importorskip("hummingbot.strategy_v2.utils.ta_utils")
from pmm_lab.features import ta_utils_shim as lab_ta


def _make_deterministic_candles(n: int = 1000, seed: int = 7) -> np.ndarray:
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
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


def _assert_series_close(left: pd.Series, right: pd.Series, atol: float = 1e-10):
    l = left.to_numpy(dtype="float64")
    r = right.to_numpy(dtype="float64")
    assert l.shape == r.shape
    nan_mask = np.isnan(l) & np.isnan(r)
    # Both NaN positions are fine; at positions where either is NaN but not both, we fail.
    only_l_nan = np.isnan(l) & ~np.isnan(r)
    only_r_nan = ~np.isnan(l) & np.isnan(r)
    assert not only_l_nan.any(), "lab has NaN where hb has value"
    assert not only_r_nan.any(), "hb has NaN where lab has value"
    diff = np.abs(l - r)
    diff[nan_mask] = 0.0
    assert np.nanmax(diff) <= atol, f"Max diff {np.nanmax(diff)} exceeds atol={atol}"


@pytest.fixture(scope="module")
def candles():
    return _make_deterministic_candles()


@pytest.fixture(scope="module")
def h(candles):
    return pd.Series(candles["high"].astype("float64"))


@pytest.fixture(scope="module")
def l(candles):
    return pd.Series(candles["low"].astype("float64"))


@pytest.fixture(scope="module")
def c(candles):
    return pd.Series(candles["close"].astype("float64"))


@pytest.fixture(scope="module")
def v(candles):
    return pd.Series(candles["volume"].astype("float64"))


class TestEMA:
    def test_ema_parity(self, c):
        _assert_series_close(lab_ta.ema(c, 20), hb_ta.ema(c, 20))
        _assert_series_close(lab_ta.ema(c, 50), hb_ta.ema(c, 50))
        _assert_series_close(lab_ta.ema(c, 200), hb_ta.ema(c, 200))


class TestRSI:
    def test_rsi_parity(self, c):
        for length in (7, 14, 21, 30):
            _assert_series_close(lab_ta.rsi_wilder(c, length), hb_ta.rsi_wilder(c, length))


class TestTrueRange:
    def test_true_range_parity(self, h, l, c):
        _assert_series_close(lab_ta.true_range(h, l, c), hb_ta.true_range(h, l, c))


class TestATR:
    def test_atr_parity(self, h, l, c):
        for length in (7, 14, 21):
            _assert_series_close(lab_ta.atr_wilder(h, l, c, length), hb_ta.atr_wilder(h, l, c, length))


class TestADX:
    def test_adx_parity(self, h, l, c):
        for length in (7, 14, 21):
            _assert_series_close(lab_ta.adx_wilder(h, l, c, length), hb_ta.adx_wilder(h, l, c, length))


class TestBollinger:
    def test_bollinger_bands_parity(self, c):
        lab_u, lab_m, lab_l = lab_ta.bollinger_bands(c, 20, 2.0)
        hb_u, hb_m, hb_l = hb_ta.bollinger_bands(c, 20, 2.0)
        _assert_series_close(lab_u, hb_u)
        _assert_series_close(lab_m, hb_m)
        _assert_series_close(lab_l, hb_l)

    def test_bollinger_percent_b_parity(self, c):
        lab = lab_ta.bollinger_percent_b(c, 80, 2.0)
        hb = hb_ta.bollinger_percent_b(c, 80, 2.0)
        for a, b in zip(lab, hb):
            _assert_series_close(a, b)


class TestVolumeQuantileOk:
    def test_volume_quantile_parity(self, v):
        lab = lab_ta.rolling_volume_quantile_ok(v, 288, 0.30)
        hb = hb_ta.rolling_volume_quantile_ok(v, 288, 0.30)
        assert (lab.astype(bool) == hb.astype(bool)).all()
