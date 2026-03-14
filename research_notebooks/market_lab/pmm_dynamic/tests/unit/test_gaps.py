"""Tests for forward-fill detection."""

import numpy as np
import pytest

from pmm_lab.data.gaps import detect_forward_fill
from tests.conftest import CANDLE_DTYPE


class TestDetectForwardFillEmpty:
    def test_detect_ff_empty_array(self):
        candles = np.array([], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert len(mask) == 0
        assert mask.dtype == bool


class TestDetectForwardFillClean:
    def test_detect_ff_clean_data(self):
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),
            (1300, 100.5, 102.0, 99.5, 101.0, 1.5, False),
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert not np.any(mask)


class TestDetectForwardFillFlatPlusZeroVol:
    def test_detect_ff_flat_plus_zero_volume(self):
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),
            (1300, 100.5, 100.5, 100.5, 100.5, 0.0, False),  # flat + zero vol
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert mask[1] == True
        assert mask[0] == False
        assert mask[2] == False


class TestDetectForwardFillOnlyFlat:
    def test_detect_ff_only_flat_not_flagged(self):
        """Flat candle but volume > 0 — only 1 heuristic, not flagged."""
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),
            (1300, 100.5, 100.5, 100.5, 100.5, 1.0, False),  # flat but has volume
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert mask[1] == False


class TestDetectForwardFillOnlyZeroVol:
    def test_detect_ff_only_zero_volume_not_flagged(self):
        """Zero volume but different OHLC — only 1 heuristic, not flagged."""
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),
            (1300, 100.0, 102.0, 99.0, 101.0, 0.0, False),  # zero vol, different OHLC
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert mask[1] == False


class TestDetectForwardFillRepeatedClose:
    def test_detect_ff_repeated_close_plus_zero_volume(self):
        """close[t] == close[t-1] AND volume[t] == 0 — 2 heuristics (zero_vol + repeated)."""
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),
            (1300, 101.0, 102.0, 99.0, 100.5, 0.0, False),  # repeated close + zero vol
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert mask[1] == True


class TestDetectForwardFillAllThree:
    def test_detect_ff_all_three_heuristics(self):
        """Flat + zero vol + repeated close — all 3 heuristics match."""
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),
            (1300, 100.5, 100.5, 100.5, 100.5, 0.0, False),  # flat + zero vol + repeated close
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert mask[1] == True


class TestDetectForwardFillMixed:
    def test_detect_ff_mixed_array(self):
        """Array with some FF bars and some clean — correct mask."""
        candles = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 1.0, False),  # clean
            (1300, 100.5, 100.5, 100.5, 100.5, 0.0, False),  # FF (flat + zero vol)
            (1600, 101.0, 103.0, 100.0, 102.0, 2.0, False),  # clean
            (1900, 102.0, 104.0, 101.0, 103.0, 1.5, False),  # clean
            (2200, 103.0, 103.0, 103.0, 103.0, 0.0, False),  # FF (flat + zero vol)
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        assert list(mask) == [False, True, False, False, True]


class TestDetectForwardFillFirstBar:
    def test_detect_ff_first_bar_cannot_be_repeated_close(self):
        """Bar 0 has no previous bar, so repeated_close is always False for bar 0."""
        candles = np.array([
            (1000, 100.0, 100.0, 100.0, 100.0, 0.0, False),  # flat + zero vol (2 heuristics)
        ], dtype=CANDLE_DTYPE)
        mask = detect_forward_fill(candles)
        # flat + zero vol = 2 heuristics → flagged
        assert mask[0] == True

        # But a bar with only zero volume should NOT be flagged (1 heuristic)
        candles2 = np.array([
            (1000, 100.0, 101.0, 99.0, 100.5, 0.0, False),  # only zero vol
        ], dtype=CANDLE_DTYPE)
        mask2 = detect_forward_fill(candles2)
        assert mask2[0] == False


class TestDetectForwardFillReturnType:
    def test_detect_ff_returns_bool_array(self, sample_candles_5m):
        mask = detect_forward_fill(sample_candles_5m)
        assert mask.dtype == bool
        assert len(mask) == len(sample_candles_5m)
