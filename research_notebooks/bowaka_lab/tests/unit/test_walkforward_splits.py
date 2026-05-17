"""Phase 9: WalkForwardSplitter behavior."""

from __future__ import annotations

from datetime import date

import pytest

from bowaka_lab.research.splits import WalkForwardSplitter


def test_embargo_enforced():
    splitter = WalkForwardSplitter(train_window=20, test_window=10, step=10, embargo=3, holdout_window=10)
    plan = splitter.plan(date(2025, 1, 2), date(2026, 5, 15))
    for s in plan.splits:
        assert s.embargo_start > s.train_end
        assert s.test_start > s.embargo_end


def test_no_train_test_overlap():
    splitter = WalkForwardSplitter(train_window=20, test_window=10, step=10, embargo=3, holdout_window=10)
    plan = splitter.plan(date(2025, 1, 2), date(2026, 5, 15))
    for s in plan.splits:
        assert s.train_end < s.test_start


def test_final_holdout_reserved():
    splitter = WalkForwardSplitter(train_window=20, test_window=10, step=10, embargo=3, holdout_window=15)
    plan = splitter.plan(date(2025, 1, 2), date(2026, 5, 15))
    assert plan.holdout_start > plan.splits[-1].test_end


def test_holdout_does_not_overlap_any_split():
    splitter = WalkForwardSplitter(train_window=30, test_window=10, step=10, embargo=3, holdout_window=20)
    plan = splitter.plan(date(2025, 1, 2), date(2026, 5, 15))
    for s in plan.splits:
        assert s.test_end < plan.holdout_start


def test_short_range_raises():
    splitter = WalkForwardSplitter(train_window=200, test_window=200, step=10, embargo=3, holdout_window=200)
    with pytest.raises(ValueError):
        splitter.plan(date(2025, 1, 2), date(2025, 6, 30))


def test_zero_windows_rejected():
    with pytest.raises(ValueError):
        WalkForwardSplitter(train_window=0, test_window=10)
    with pytest.raises(ValueError):
        WalkForwardSplitter(train_window=10, test_window=0)
