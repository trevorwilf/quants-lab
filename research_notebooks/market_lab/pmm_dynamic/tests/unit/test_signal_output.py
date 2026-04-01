"""Tests for SignalOutput."""

import numpy as np
import math
import pytest

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


class TestSignalOutputSlice:
    """Verify sliced signals preserve local indexing and warmup semantics."""

    def test_signal_output_slice_preserves_values(self):
        data = {
            "price": np.array([10.0, 20.0, 30.0, 40.0]),
            "signal": np.array([0.0, 1.0, 0.0, -1.0]),
        }
        so = SignalOutput(warmup_end=2, data=data)
        sliced = so.slice(1, 4)

        assert sliced.warmup_end == 1
        assert sliced.get("price", 0) == 20.0
        assert sliced.get("price", 2) == 40.0
        assert sliced.get("signal", 2) == -1.0
        assert not sliced.is_valid(0)
        assert sliced.is_valid(1)

    def test_signal_output_slice_rejects_invalid_bounds(self):
        so = SignalOutput(warmup_end=0, data={"x": np.array([1.0, 2.0])})
        with pytest.raises(ValueError):
            so.slice(-1, 1)
        with pytest.raises(ValueError):
            so.slice(2, 1)
