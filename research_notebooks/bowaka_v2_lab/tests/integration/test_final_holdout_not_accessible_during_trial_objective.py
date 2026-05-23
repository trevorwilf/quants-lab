"""The final-holdout window is unreachable from any trial-objective fold.

Realism remediation 2 Phase 8 (cf. audit §13.1 / §14.4). The HoldoutGuard
raises ``HoldoutGuardError`` if a tuning step's fold overlaps the holdout
window. Phase 8 makes the holdout's substantive metrics identical to validation
folds (§P1-004), which makes it doubly important that the holdout is read
exactly once — via :func:`optuna.holdout.score_final_holdout` — and never by a
trial objective.
"""
from __future__ import annotations

import datetime as dt

import pytest

from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError


def test_guard_blocks_tuning_read_of_holdout_window() -> None:
    """A tuning step asking to read inside the holdout window raises."""
    guard = HoldoutGuard(
        final_holdout_start=dt.date(2024, 11, 1),
        final_holdout_end=dt.date(2024, 12, 31),
    )
    # Validation fold ending well before the holdout — permitted.
    guard.assert_can_read(dt.date(2024, 5, 1), dt.date(2024, 5, 31))
    # Fold ending inside the holdout — blocked.
    with pytest.raises(HoldoutGuardError, match="final-holdout window"):
        guard.assert_can_read(dt.date(2024, 11, 15), dt.date(2024, 12, 15))
    # Fold straddling the holdout boundary — blocked.
    with pytest.raises(HoldoutGuardError):
        guard.assert_can_read(dt.date(2024, 10, 15), dt.date(2024, 11, 15))


def test_guard_unblocks_in_final_eval_phase() -> None:
    """After ``enter_final_eval`` the guard becomes a no-op (the one sanctioned read)."""
    guard = HoldoutGuard(
        final_holdout_start=dt.date(2024, 11, 1),
        final_holdout_end=dt.date(2024, 12, 31),
    )
    guard.enter_final_eval()
    # No raise — the holdout is the sanctioned read inside final_eval.
    guard.assert_can_read(dt.date(2024, 11, 15), dt.date(2024, 12, 15))
    guard.exit_final_eval()
    # Out of final_eval, the guard is hot again.
    with pytest.raises(HoldoutGuardError):
        guard.assert_can_read(dt.date(2024, 11, 15), dt.date(2024, 12, 15))


def test_trial_objective_cannot_synthesize_a_holdout_read() -> None:
    """A synthetic trial objective trying to read the holdout window raises."""
    from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError

    guard = HoldoutGuard(
        final_holdout_start=dt.date(2024, 11, 1),
        final_holdout_end=dt.date(2024, 12, 31),
    )

    def trial_objective_with_holdout_read() -> float:
        # The trial objective tries to "read" the holdout window — the
        # HoldoutGuard rejects it before any data is touched.
        guard.assert_can_read(dt.date(2024, 11, 5), dt.date(2024, 11, 10))
        return 0.42

    with pytest.raises(HoldoutGuardError):
        trial_objective_with_holdout_read()
