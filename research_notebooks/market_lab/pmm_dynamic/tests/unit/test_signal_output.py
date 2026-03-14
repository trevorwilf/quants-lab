"""Tests for SignalOutput."""

import numpy as np
import math

from pmm_lab.sim.strategy import SignalOutput


class TestSignalOutputGet:
    """Verify .get(key, bar_idx) returns correct float."""

    def test_signal_output_get(self):
        data = {"price": np.array([10.0, 20.0, 30.0])}
        so = SignalOutput(warmup_end=0, data=data)
        assert so.get("price", 0) == 10.0
        assert so.get("price", 1) == 20.0
        assert so.get("price", 2) == 30.0

    def test_signal_output_get_missing_key(self):
        data = {"price": np.array([10.0, 20.0])}
        so = SignalOutput(warmup_end=0, data=data)
        result = so.get("nonexistent", 0)
        assert math.isnan(result)

    def test_signal_output_get_out_of_bounds(self):
        data = {"price": np.array([10.0, 20.0])}
        so = SignalOutput(warmup_end=0, data=data)
        result = so.get("price", 5)
        assert math.isnan(result)


class TestSignalOutputIsValid:
    """Verify is_valid behavior around warmup boundary."""

    def test_signal_output_is_valid(self):
        so = SignalOutput(warmup_end=5)
        assert not so.is_valid(0)
        assert not so.is_valid(4)
        assert so.is_valid(5)
        assert so.is_valid(6)
        assert so.is_valid(100)


class TestSignalOutputEmpty:
    """Test with empty data dict."""

    def test_signal_output_empty_data(self):
        so = SignalOutput(warmup_end=3, data={})
        assert not so.is_valid(2)
        assert so.is_valid(3)
        result = so.get("anything", 0)
        assert math.isnan(result)
