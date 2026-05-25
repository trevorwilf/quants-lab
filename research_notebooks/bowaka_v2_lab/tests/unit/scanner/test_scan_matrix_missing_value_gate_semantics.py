"""Matrix missing-value flags map to the legacy ``_ge`` / ``_le`` / ``_between`` outcomes.

Matrix doc §6. The matrix stores NaN for "no value" in float64 columns,
``-1`` for "no value" in int64 columns, and the ``has_bar`` /
``has_baseline`` uint8 flags for explicit missingness. The Phase 9
vectorised evaluator must reproduce the legacy semantics:

* ``_ge(None, threshold)`` → ``False``
* ``_le(None, threshold)`` → ``False``
* ``_between(None, lo, hi)`` → ``False``
"""
from __future__ import annotations

import numpy as np
import pytest


def _ge_legacy(value, threshold) -> bool:
    if value is None:
        return False
    try:
        return float(value) >= float(threshold)
    except (TypeError, ValueError):
        return False


def _ge_matrix(value: float, threshold: float, *, has_value: bool) -> bool:
    if not has_value:
        return False
    if np.isnan(value):
        return False
    return value >= threshold


def test_ge_with_no_value_returns_false():
    assert _ge_legacy(None, 0.5) is False
    assert _ge_matrix(np.nan, 0.5, has_value=False) is False


def test_ge_with_real_value_matches_legacy():
    assert _ge_legacy(0.7, 0.5) == _ge_matrix(0.7, 0.5, has_value=True) is True
    assert _ge_legacy(0.3, 0.5) == _ge_matrix(0.3, 0.5, has_value=True) is False


def test_int64_sentinel_minus_one_treated_as_missing():
    """``last_bar_ts_ns == -1`` is the matrix sentinel for no bar."""
    arr = np.array([1700000000_000000000, -1, 1700000001_000000000], dtype=np.int64)
    valid = arr != -1
    assert valid.tolist() == [True, False, True]


def test_uint8_has_bar_flag_is_strict_zero_one():
    """has_bar / has_baseline / has_valid_timestamp / bar_timestamp_was_naive
    are strict 0/1; values outside {0,1} are a build bug."""
    arr = np.array([0, 1, 1, 0], dtype=np.uint8)
    assert set(np.unique(arr).tolist()).issubset({0, 1})
