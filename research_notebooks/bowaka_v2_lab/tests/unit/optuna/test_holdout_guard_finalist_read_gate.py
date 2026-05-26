"""``HoldoutGuard.declare_finalist_read`` authorises ONE holdout-read phase.

Speedup report v2 §1.4 / §5.x / Phase 5 task 1. The finalist evaluation
pipeline is the one authorised reader of the holdout window AFTER
tuning. Without the explicit declaration the guard continues to refuse
the read.
"""
from __future__ import annotations

import datetime as dt

import pytest

from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError


def _guard() -> HoldoutGuard:
    return HoldoutGuard(
        final_holdout_start=dt.date(2025, 1, 1),
        final_holdout_end=dt.date(2025, 4, 1),
    )


def test_default_guard_refuses_holdout_read() -> None:
    g = _guard()
    with pytest.raises(HoldoutGuardError, match="final-holdout"):
        g.assert_can_read(dt.date(2025, 1, 15), dt.date(2025, 2, 1))


def test_finalist_declaration_authorises_holdout_read() -> None:
    g = _guard()
    g.declare_finalist_read()
    g.assert_can_read(dt.date(2025, 1, 15), dt.date(2025, 2, 1))
    # Still passes after multiple calls.
    g.assert_can_read(dt.date(2025, 2, 1), dt.date(2025, 3, 1))


def test_revoke_finalist_read_restores_refusal() -> None:
    g = _guard()
    g.declare_finalist_read()
    g.assert_can_read(dt.date(2025, 1, 15), dt.date(2025, 2, 1))
    g.revoke_finalist_read()
    with pytest.raises(HoldoutGuardError):
        g.assert_can_read(dt.date(2025, 1, 15), dt.date(2025, 2, 1))


def test_validation_window_is_unaffected_by_declaration() -> None:
    """Reads that do NOT overlap the holdout window pass either way."""
    g = _guard()
    g.assert_can_read(dt.date(2024, 1, 1), dt.date(2024, 12, 1))
    g.declare_finalist_read()
    g.assert_can_read(dt.date(2024, 1, 1), dt.date(2024, 12, 1))


def test_finalist_declaration_is_per_guard_instance() -> None:
    """A separate guard does NOT inherit the declaration."""
    g1 = _guard()
    g2 = _guard()
    g1.declare_finalist_read()
    g1.assert_can_read(dt.date(2025, 1, 15), dt.date(2025, 2, 1))
    with pytest.raises(HoldoutGuardError):
        g2.assert_can_read(dt.date(2025, 1, 15), dt.date(2025, 2, 1))
