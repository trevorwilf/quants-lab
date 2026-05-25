"""Matrix-sensitive search-space guard refuses every listed prefix.

Matrix doc §17. The precomputed matrix becomes invalid the moment a
trial tunes any input that feeds the matrix — feed, scanner cadence,
intraday-window policy, historical-features knobs, universe filters,
ATR/EMA lookbacks. The guard fails closed at study start.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.scanner.scan_matrix import (
    MATRIX_SENSITIVE_PREFIXES,
    assert_search_space_compatible_with_matrix,
)


def test_default_search_space_passes():
    assert_search_space_compatible_with_matrix(None)
    assert_search_space_compatible_with_matrix({})


@pytest.mark.parametrize("key", [
    "session.scanner_start",
    "session.scanner_end",
    "session.scan_interval_seconds",
    "simulation.intraday_window_policy",
    "historical_features.volume_curve.bucket_count",
    "universe.min_price",
    "universe.max_price",
    "market_data.feed",
    "market_data.adjustment",
    "signals.atr_window",
    "signals.ema_window",
])
def test_each_sensitive_prefix_is_refused(key: str):
    with pytest.raises(OptunaStudyInvalidError) as info:
        assert_search_space_compatible_with_matrix({key: ("uniform", 1.0, 5.0)})
    assert key in str(info.value)


def test_non_matrix_signal_key_passes():
    """A signals.gap_pct_max override does NOT invalidate the matrix."""
    assert_search_space_compatible_with_matrix(
        {"signals.gap_pct_max": ("uniform", 0.05, 0.20)},
    )


def test_prefix_constants_present():
    for required in (
        "session.scanner_start",
        "session.scanner_end",
        "session.scan_interval_seconds",
        "simulation.intraday_window_policy",
        "historical_features.",
        "universe.",
        "market_data.feed",
        "market_data.adjustment",
    ):
        assert required in MATRIX_SENSITIVE_PREFIXES
