"""Tests for pmm_lab.features.regime — market regime classification."""

import numpy as np
import pytest

from pmm_lab.features.regime import classify_regime, RegimeClassification

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n, close_fn, vol_scale=50.0, seed=42):
    """Build candles from a close price function."""
    rng = np.random.default_rng(seed=seed)
    rows = []
    for i in range(n):
        c = close_fn(i)
        o = c + rng.normal(0, vol_scale * 0.1)
        h = max(o, c) + abs(rng.normal(0, vol_scale * 0.2))
        l = min(o, c) - abs(rng.normal(0, vol_scale * 0.2))
        o = max(o, 1.0)
        c = max(c, 1.0)
        h = max(h, max(o, c))
        l = max(l, 0.01)
        l = min(l, min(o, c))
        rows.append((1756833000 + i * 300, o, h, l, c, rng.uniform(0.1, 2.0), False))
    return np.array(rows, dtype=CANDLE_DTYPE)


class TestClassifyRegimeReturnsClassification:
    def test_classify_regime_returns_classification(self, sample_candles_500):
        regime = classify_regime(sample_candles_500)
        assert isinstance(regime, RegimeClassification)
        assert isinstance(regime.volatility, str)
        assert isinstance(regime.trend, str)
        assert isinstance(regime.label, str)
        assert isinstance(regime.natr_mean, float)
        assert isinstance(regime.efficiency_ratio, float)
        assert isinstance(regime.total_return_pct, float)


class TestClassifyRegimeLabelFormat:
    def test_classify_regime_label_format(self, sample_candles_500):
        regime = classify_regime(sample_candles_500)
        parts = regime.label.split("_")
        assert len(parts) >= 2
        assert parts[0] in ("high", "low")
        assert "vol" in regime.label


class TestHighVolDetection:
    def test_high_vol_detection(self):
        """Large price swings -> high_vol."""
        candles = _make_candles(100, lambda i: 100000 + np.sin(i * 0.5) * 5000, vol_scale=5000)
        # Use a low threshold to ensure high_vol classification
        regime = classify_regime(candles, natr_threshold=0.0001)
        assert regime.volatility == "high_vol"


class TestLowVolDetection:
    def test_low_vol_detection(self):
        """Tiny price changes -> low_vol."""
        candles = _make_candles(100, lambda i: 100000 + i * 0.01, vol_scale=0.1)
        # Use a high threshold to ensure low_vol classification
        regime = classify_regime(candles, natr_threshold=0.1)
        assert regime.volatility == "low_vol"


class TestTrendingDetection:
    def test_trending_detection(self):
        """Steady uptrend -> trending."""
        candles = _make_candles(100, lambda i: 100000 + i * 100, vol_scale=5.0)
        regime = classify_regime(candles, efficiency_threshold=0.30)
        assert regime.trend == "trending"
        assert regime.efficiency_ratio >= 0.30


class TestRangingDetection:
    def test_ranging_detection(self):
        """Oscillating close -> ranging."""
        candles = _make_candles(100, lambda i: 100000 + 500 * np.sin(i * 0.5), vol_scale=50.0)
        regime = classify_regime(candles, efficiency_threshold=0.30)
        assert regime.trend == "ranging"
        assert regime.efficiency_ratio < 0.30


class TestShortCandlesUnknown:
    def test_short_candles_unknown(self):
        """Fewer bars than natr_window -> unknown."""
        candles = _make_candles(10, lambda i: 100000 + i)
        regime = classify_regime(candles, natr_window=14)
        assert regime.label == "unknown"


class TestEfficiencyRatioRange:
    def test_efficiency_ratio_range(self, sample_candles_500):
        regime = classify_regime(sample_candles_500)
        assert 0.0 <= regime.efficiency_ratio <= 1.0


class TestTotalReturnCorrect:
    def test_total_return_correct(self, sample_candles_500):
        regime = classify_regime(sample_candles_500)
        close = sample_candles_500["close"].astype("float64")
        expected = (close[-1] / close[0] - 1.0) * 100.0
        assert abs(regime.total_return_pct - expected) < 1e-6
