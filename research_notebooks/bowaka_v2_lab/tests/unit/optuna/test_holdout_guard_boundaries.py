"""HoldoutGuard half-open boundary semantics (audit 2026-05-23 §P0-002).

Pre-remediation the guard used closed-interval logic and rejected the
boundary-equal cases that the walk-forward planner (half-open) admits — every
such fold then surfaced a swallowed ``HoldoutGuardError`` as
``_FAILED_TRIAL_SCORE``. These tests pin the new half-open semantics:
``end == final_holdout_start`` and ``start == final_holdout_end`` are allowed;
any true overlap still raises.
"""
from __future__ import annotations

import datetime as dt

import pytest

from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError


def test_val_end_equal_to_holdout_start_is_allowed():
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    g.assert_can_read(dt.date(2024, 3, 1), dt.date(2024, 4, 1))  # must not raise


def test_val_start_equal_to_holdout_end_is_allowed():
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    g.assert_can_read(dt.date(2024, 5, 1), dt.date(2024, 6, 1))  # must not raise


def test_true_overlap_blocked():
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(dt.date(2024, 3, 15), dt.date(2024, 4, 15))


def test_strictly_inside_holdout_blocked():
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(dt.date(2024, 4, 10), dt.date(2024, 4, 20))


def test_final_eval_phase_permits_holdout_read():
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    g.enter_final_eval()
    g.assert_can_read(dt.date(2024, 4, 10), dt.date(2024, 4, 20))  # must not raise


def test_read_that_brackets_holdout_blocked():
    """A read whose ``[start, end)`` strictly contains the holdout overlaps it."""
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(dt.date(2024, 3, 1), dt.date(2024, 6, 1))


def test_read_ending_one_day_into_holdout_blocked():
    """``end == final_start + 1`` is still an overlap (half-open)."""
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(dt.date(2024, 3, 1), dt.date(2024, 4, 2))


def test_read_starting_one_day_before_holdout_end_blocked():
    """``start == final_end - 1`` is still an overlap (half-open)."""
    g = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(dt.date(2024, 4, 30), dt.date(2024, 6, 1))
