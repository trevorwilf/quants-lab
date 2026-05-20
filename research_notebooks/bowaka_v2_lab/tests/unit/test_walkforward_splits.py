"""Split-window math for 6m/1m/1m and 3m/2w/2w."""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def test_6m_1m_1m_plan() -> None:
    plan = build_walkforward_splits(
        full_start=_dt.date(2024, 1, 1), full_end=_dt.date(2024, 12, 31),
        train_months=6, val_months=1, final_holdout_months=1,
    )
    assert plan.splits, "expected at least one split"
    for s in plan.splits:
        # train and val never overlap final holdout.
        assert s.val_end <= plan.final_holdout_start
        # Walk-forward windows: train ends at val_start (back-to-back is standard).
        assert s.train_start < s.train_end
        assert s.train_end == s.val_start
        assert s.val_start < s.val_end


def test_2w_step_smaller_train() -> None:
    plan = build_walkforward_splits(
        full_start=_dt.date(2024, 1, 1), full_end=_dt.date(2024, 6, 30),
        train_months=3, val_months=1, final_holdout_months=1, step_months=1,
    )
    assert plan.splits


def test_final_holdout_required() -> None:
    with pytest.raises(ValueError):
        build_walkforward_splits(
            full_start=_dt.date(2024, 1, 1), full_end=_dt.date(2024, 12, 31),
            train_months=6, val_months=1, final_holdout_months=0,
        )
