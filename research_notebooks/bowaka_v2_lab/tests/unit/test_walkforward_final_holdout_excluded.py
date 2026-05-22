"""Training and validation windows never overlap the final holdout.

Realism remediation Phase 9 extends this with the HoldoutGuard read-guard: the
guard raises if a tuning step attempts to read the holdout window, and stays
silent once explicitly switched to the final-eval phase. The end-to-end
study-level check (the holdout is scored only via ``--final-holdout``) lives in
``tests/integration/test_walkforward_final_holdout_excluded.py``.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def test_holdout_disjoint_from_all_splits() -> None:
    plan = build_walkforward_splits(
        full_start=_dt.date(2023, 1, 1), full_end=_dt.date(2024, 12, 31),
        train_months=9, val_months=1, final_holdout_months=2,
    )
    for s in plan.splits:
        assert s.val_end <= plan.final_holdout_start
        assert s.train_end <= plan.final_holdout_start


def test_guard_blocks_every_split_that_touches_the_holdout() -> None:
    """No walk-forward split may be read into the holdout window during tuning."""
    plan = build_walkforward_splits(
        full_start=_dt.date(2023, 1, 1), full_end=_dt.date(2024, 12, 31),
        train_months=9, val_months=1, final_holdout_months=2,
    )
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    # Every real split's validation window is readable during tuning.
    for s in plan.splits:
        guard.assert_can_read(s.val_start, s.val_end)
    # A read inside the holdout window is forbidden during tuning.
    with pytest.raises(HoldoutGuardError):
        guard.assert_can_read(plan.final_holdout_start, plan.final_holdout_end)


def test_guard_allows_holdout_read_only_in_final_eval_phase() -> None:
    """The holdout window is readable ONLY after enter_final_eval()."""
    guard = HoldoutGuard(_dt.date(2024, 11, 1), _dt.date(2024, 12, 31))
    with pytest.raises(HoldoutGuardError):
        guard.assert_can_read(_dt.date(2024, 11, 15), _dt.date(2024, 12, 1))
    guard.enter_final_eval()
    # No raise now — this is the sanctioned final-holdout read.
    guard.assert_can_read(_dt.date(2024, 11, 15), _dt.date(2024, 12, 1))
    guard.exit_final_eval()
    # Back in tuning phase — forbidden again.
    with pytest.raises(HoldoutGuardError):
        guard.assert_can_read(_dt.date(2024, 11, 15), _dt.date(2024, 12, 1))
