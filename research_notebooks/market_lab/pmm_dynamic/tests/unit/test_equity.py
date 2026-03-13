"""Tests for pmm_lab.metrics.equity — drawdown computation."""

import numpy as np
import pytest
from pmm_lab.metrics.equity import compute_max_drawdown, compute_drawdown_series


class TestComputeMaxDrawdown:
    def test_drawdown_simple_peak_trough(self):
        """Peak at 110, trough at 90 → (110-90)/110*100 ≈ 18.18%."""
        eq = np.array([100.0, 110.0, 105.0, 90.0, 95.0, 100.0], dtype="float64")
        dd = compute_max_drawdown(eq)
        assert abs(dd - (110.0 - 90.0) / 110.0 * 100.0) < 0.01

    def test_drawdown_monotonic_up(self):
        """Strictly increasing equity → drawdown = 0."""
        eq = np.array([100.0, 101.0, 102.0, 103.0, 104.0], dtype="float64")
        dd = compute_max_drawdown(eq)
        assert dd == 0.0

    def test_drawdown_monotonic_down(self):
        """Equity = [100, 90, 80, 70]. Drawdown = (100-70)/100*100 = 30%."""
        eq = np.array([100.0, 90.0, 80.0, 70.0], dtype="float64")
        dd = compute_max_drawdown(eq)
        assert abs(dd - 30.0) < 0.01

    def test_drawdown_series_length(self):
        """compute_drawdown_series returns array of same length as input."""
        eq = np.array([100.0, 110.0, 105.0, 90.0, 95.0], dtype="float64")
        series = compute_drawdown_series(eq)
        assert len(series) == len(eq)

    def test_drawdown_empty_array(self):
        """Empty equity curve → 0.0."""
        eq = np.array([], dtype="float64")
        dd = compute_max_drawdown(eq)
        assert dd == 0.0
