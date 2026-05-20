"""Walk-forward train / val / final-holdout splits per [Report §14.4]."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Iterable


def _add_months(d: _dt.date, n: int) -> _dt.date:
    year = d.year + (d.month - 1 + n) // 12
    month = (d.month - 1 + n) % 12 + 1
    try:
        return _dt.date(year, month, d.day)
    except ValueError:
        # last day of target month
        import calendar
        return _dt.date(year, month, calendar.monthrange(year, month)[1])


@dataclass(frozen=True)
class WalkForwardSplit:
    train_start: _dt.date
    train_end: _dt.date
    val_start: _dt.date
    val_end: _dt.date


@dataclass(frozen=True)
class WalkForwardPlan:
    splits: tuple[WalkForwardSplit, ...]
    final_holdout_start: _dt.date
    final_holdout_end: _dt.date


def build_walkforward_splits(
    *,
    full_start: _dt.date,
    full_end: _dt.date,
    train_months: int,
    val_months: int,
    final_holdout_months: int,
    step_months: int | None = None,
) -> WalkForwardPlan:
    """Build a rolling walk-forward plan ending with a final-holdout window.

    The final-holdout window is reserved at the tail; train/val splits step
    through the prefix.
    """
    if final_holdout_months <= 0:
        raise ValueError("final_holdout_months must be > 0")
    if train_months <= 0 or val_months <= 0:
        raise ValueError("train_months and val_months must be > 0")
    step_months = step_months or val_months
    final_start = _add_months(full_end, -final_holdout_months)
    final_holdout_start = final_start
    final_holdout_end = full_end
    if final_start <= full_start:
        raise ValueError("final-holdout window must not overlap or precede the full start")
    splits: list[WalkForwardSplit] = []
    cur_train_start = full_start
    while True:
        train_end = _add_months(cur_train_start, train_months)
        val_start = train_end
        val_end = _add_months(val_start, val_months)
        if val_end > final_start:
            break
        splits.append(WalkForwardSplit(cur_train_start, train_end, val_start, val_end))
        cur_train_start = _add_months(cur_train_start, step_months)
    return WalkForwardPlan(tuple(splits), final_holdout_start, final_holdout_end)
