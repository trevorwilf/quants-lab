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
    """One walk-forward training / validation split.

    All intervals are half-open ``[start, end)`` — see audit 2026-05-23 §P0-002.
    A split with ``val_end == final_holdout_start`` is admissible (the
    validation window ends exactly when the holdout begins).
    """

    train_start: _dt.date
    train_end: _dt.date
    val_start: _dt.date
    val_end: _dt.date


@dataclass(frozen=True)
class WalkForwardPlan:
    """A walk-forward plan: a tuple of train/val splits + a final-holdout window.

    All intervals are half-open ``[start, end)`` — see audit 2026-05-23 §P0-002.
    """

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


def anchor_window_start(
    full_end: _dt.date,
    *,
    train_months: int,
    val_months: int,
    final_holdout_months: int,
    step_months: int,
    n_folds: int,
) -> _dt.date:
    """Start date that yields EXACTLY ``n_folds`` rolling folds + the holdout when
    fed to :func:`build_walkforward_splits` with ``full_end``.

    The holdout is reserved at ``[full_end - final_holdout, full_end)``; folds roll
    forward from the returned start (stepping ``step_months``) and the last fold's
    ``val_end`` lands exactly on ``final_holdout_start``. Hence
    ``start = full_end - final_holdout - (n_folds-1)*step - train - val``. Used by
    the ``start_date: auto`` anchoring (resolve_walkforward_config) so the window
    tracks the latest lake session while keeping a fixed fold count. Exact month
    arithmetic guarantees the fold count (do NOT month-snap — that breaks it).
    """
    if n_folds < 1:
        raise ValueError("n_folds must be >= 1")
    if train_months <= 0 or val_months <= 0 or step_months <= 0 or final_holdout_months <= 0:
        raise ValueError("train/val/step/holdout months must all be > 0")
    total = final_holdout_months + (n_folds - 1) * step_months + train_months + val_months
    return _add_months(full_end, -total)
