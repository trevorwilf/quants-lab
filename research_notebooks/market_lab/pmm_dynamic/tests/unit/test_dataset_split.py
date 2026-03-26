"""Tests for pmm_lab.objective.dataset_split."""

import numpy as np
import pytest

from tests.conftest import _make_sample_candles_500, CANDLE_DTYPE
from pmm_lab.objective.dataset_split import split_for_release_gate


@pytest.fixture
def candles_500():
    return _make_sample_candles_500()


class TestSplitForReleaseGate:
    """Tests for split_for_release_gate with 500-bar 5m fixture.

    500 bars at 300s each spans ~41.7 hours.
    With recent_days=1, the last 24h (~288 bars) are reserved,
    leaving ~212 pre-release bars.
    """

    def test_recent_window_reserved_from_dev_and_holdout(self, candles_500):
        """All dev and holdout timestamps must be before recent window start."""
        slices = split_for_release_gate(
            candles_500,
            recent_days=1,
            holdout_fraction=0.20,
            min_holdout_bars=20,
            min_pre_release_bars=100,
        )
        recent_start_ts = slices.recent_start_timestamp
        assert np.all(slices.dev_candles["timestamp"] < recent_start_ts)
        assert np.all(slices.holdout_candles["timestamp"] < recent_start_ts)

    def test_release_split_fails_when_history_too_short(self):
        """Very short candle array should raise ValueError."""
        rng = np.random.default_rng(seed=0)
        n = 20
        start_ts = 1756833000
        rows = []
        price = 100.0
        for i in range(n):
            ts = start_ts + i * 300
            c = price + rng.normal(0, 1)
            rows.append((ts, price, max(price, c) + 0.5, min(price, c) - 0.5, c, 1.0, False))
            price = c
        short_candles = np.array(rows, dtype=CANDLE_DTYPE)

        with pytest.raises(ValueError, match="Pre-release data too short"):
            split_for_release_gate(
                short_candles,
                recent_days=1,
                holdout_fraction=0.20,
                min_holdout_bars=5,
                min_pre_release_bars=100,
            )

    def test_recent_start_timestamp_matches_last_n_days(self, candles_500):
        """recent_start_timestamp should be approximately last_ts - recent_days * 86400."""
        slices = split_for_release_gate(
            candles_500,
            recent_days=1,
            holdout_fraction=0.20,
            min_holdout_bars=20,
            min_pre_release_bars=100,
        )
        last_ts = int(candles_500["timestamp"][-1])
        expected_start = last_ts - 1 * 86400
        # The actual timestamp should be >= expected_start (searchsorted finds
        # the first bar at or after the boundary)
        assert slices.recent_start_timestamp >= expected_start
        # And it should be within one bar interval (300s) of the boundary
        assert slices.recent_start_timestamp - expected_start < 300

    def test_recent_window_is_nonempty(self, candles_500):
        """Recent release window must have at least one bar."""
        slices = split_for_release_gate(
            candles_500,
            recent_days=1,
            holdout_fraction=0.20,
            min_holdout_bars=20,
            min_pre_release_bars=100,
        )
        assert len(slices.recent_release_candles) > 0

    def test_pre_release_plus_recent_equals_full(self, candles_500):
        """pre_release + recent should equal full candle count."""
        slices = split_for_release_gate(
            candles_500,
            recent_days=1,
            holdout_fraction=0.20,
            min_holdout_bars=20,
            min_pre_release_bars=100,
        )
        assert (
            len(slices.pre_release_candles) + len(slices.recent_release_candles)
            == len(slices.full_candles)
        )
