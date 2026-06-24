"""Tests for the latest-data window anchoring (backtest.{start,end}_date: auto).

The core guarantee: ``anchor_window_start`` returns a start such that
``build_walkforward_splits`` produces EXACTLY ``n_folds`` folds + the holdout.
This is what lets the weekly cron + notebook 10 track the freshest lake session
while keeping a fixed fold count.
"""
import datetime as dt

import pytest

from bowaka_v2_lab.optuna.walkforward import anchor_window_start, build_walkforward_splits


@pytest.mark.parametrize("n_folds", [1, 2, 3, 4, 5])
def test_anchor_yields_exact_fold_count(n_folds):
    end = dt.date(2026, 6, 23)
    kw = dict(train_months=6, val_months=1, final_holdout_months=5, step_months=7)
    start = anchor_window_start(end, n_folds=n_folds, **kw)
    plan = build_walkforward_splits(full_start=start, full_end=end, **kw)
    assert len(plan.splits) == n_folds
    # last fold's validation ends exactly where the holdout begins
    assert plan.splits[-1].val_end == plan.final_holdout_start


def test_anchor_formula_3_folds():
    # end - (holdout 5 + (3-1)*step 7 + train 6 + val 1) = end - 26 months
    assert anchor_window_start(
        dt.date(2026, 6, 23), train_months=6, val_months=1,
        final_holdout_months=5, step_months=7, n_folds=3,
    ) == dt.date(2024, 4, 23)


def test_anchor_holdout_is_final_holdout_months():
    end = dt.date(2026, 6, 23)
    start = anchor_window_start(end, train_months=6, val_months=1,
                               final_holdout_months=5, step_months=7, n_folds=3)
    plan = build_walkforward_splits(full_start=start, full_end=end, train_months=6,
                                   val_months=1, final_holdout_months=5, step_months=7)
    assert plan.final_holdout_end == end
    # 5-month holdout
    assert plan.final_holdout_start == dt.date(2026, 1, 23)


@pytest.mark.parametrize("bad", [dict(n_folds=0), dict(train_months=0), dict(step_months=0)])
def test_anchor_rejects_nonpositive(bad):
    kw = dict(train_months=6, val_months=1, final_holdout_months=5, step_months=7, n_folds=3)
    kw.update(bad)
    with pytest.raises(ValueError):
        anchor_window_start(dt.date(2026, 6, 23), **kw)
