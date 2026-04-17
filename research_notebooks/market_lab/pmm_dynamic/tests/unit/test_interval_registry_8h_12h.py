"""Tests for 8h + 12h interval additions to INTERVAL_SECONDS.

Originally added 12h in phase-1; phase-2 delta adds 8h (now that both
exchanges have 8h candles available after a backfill).

The registry test uses synthetic candles only — no Mongo dependency.
"""

import numpy as np
import pytest

from pmm_lab.config.defaults import INTERVAL_SECONDS
from tests.conftest import CANDLE_DTYPE


class TestIntervalRegistry12h:
    def test_12h_present_with_correct_value(self):
        assert "12h" in INTERVAL_SECONDS
        assert INTERVAL_SECONDS["12h"] == 43200

    def test_existing_keys_unchanged(self):
        """Regression: the pre-existing intervals must not have been altered."""
        assert INTERVAL_SECONDS["1m"] == 60
        assert INTERVAL_SECONDS["5m"] == 300
        assert INTERVAL_SECONDS["15m"] == 900
        assert INTERVAL_SECONDS["1h"] == 3600
        assert INTERVAL_SECONDS["4h"] == 14400
        assert INTERVAL_SECONDS["1d"] == 86400

    def test_12h_between_4h_and_1d(self):
        """Ordering sanity — 12h must be between 4h and 1d in seconds."""
        assert INTERVAL_SECONDS["4h"] < INTERVAL_SECONDS["12h"] < INTERVAL_SECONDS["1d"]


class TestIntervalRegistry8h:
    def test_8h_present_with_correct_value(self):
        assert "8h" in INTERVAL_SECONDS
        assert INTERVAL_SECONDS["8h"] == 28800

    def test_8h_between_4h_and_12h(self):
        assert INTERVAL_SECONDS["4h"] < INTERVAL_SECONDS["8h"] < INTERVAL_SECONDS["12h"]


class TestMonotonicOrdering:
    def test_iteration_is_strictly_monotonic(self):
        """Catches accidental dict-order bugs after edits to the registry.

        Python dicts preserve insertion order since 3.7, so iterating the
        values must produce strictly increasing seconds.
        """
        values = list(INTERVAL_SECONDS.values())
        for prev, nxt in zip(values, values[1:]):
            assert prev < nxt, (
                f"INTERVAL_SECONDS values are not strictly monotonically "
                f"increasing: {prev} then {nxt}. Full list: {values}"
            )


class TestValidateCandles12h:
    def test_validate_candles_accepts_12h(self):
        """validate_candles must accept 12h input without raising KeyError."""
        from pmm_lab.data.candles import validate_candles

        n = 30
        start_ts = 1_700_000_000
        interval = 43200
        timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
        rows = []
        price = 100.0
        for i in range(n):
            rows.append((int(timestamps[i]), price, price + 1.0, price - 1.0, price + 0.5, 1.0, False))
            price += 0.2
        candles = np.array(rows, dtype=CANDLE_DTYPE)

        try:
            result = validate_candles(candles, "12h", strict=False)
        except KeyError as e:
            pytest.fail(f"validate_candles raised KeyError for '12h' interval: {e}")
        assert result is not None


class TestValidateCandles8h:
    def test_validate_candles_accepts_8h(self):
        """validate_candles must accept 8h input without raising KeyError."""
        from pmm_lab.data.candles import validate_candles

        n = 10
        start_ts = 1_700_000_000
        interval = 28800  # 8h
        timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
        rows = []
        price = 100.0
        for i in range(n):
            rows.append((int(timestamps[i]), price, price + 1.0, price - 1.0, price + 0.5, 1.0, False))
            price += 0.2
        candles = np.array(rows, dtype=CANDLE_DTYPE)

        try:
            result = validate_candles(candles, "8h", strict=False)
        except KeyError as e:
            pytest.fail(f"validate_candles raised KeyError for '8h' interval: {e}")
        assert result is not None
