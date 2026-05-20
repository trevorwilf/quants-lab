"""Walk-forward time-series splits with embargo and reserved final holdout."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Sequence

from bowaka_common.calendar.exchange import USEquityCalendar


@dataclass(frozen=True)
class WalkForwardSplit:
    fold: int
    train_start: date
    train_end: date
    embargo_start: date
    embargo_end: date
    test_start: date
    test_end: date


@dataclass(frozen=True)
class WalkForwardPlan:
    splits: tuple[WalkForwardSplit, ...]
    holdout_start: date
    holdout_end: date


class WalkForwardSplitter:
    """Train_window, test_window, step, embargo — counted in trading sessions.

    The final ``holdout`` window is *reserved* from optimization — it does not
    appear in any split. Callers must explicitly evaluate on it after model
    selection.
    """

    def __init__(
        self,
        *,
        train_window: int = 90,
        test_window: int = 21,
        step: int = 21,
        embargo: int = 3,
        holdout_window: int = 21,
        calendar: USEquityCalendar | None = None,
    ):
        if min(train_window, test_window, step, embargo, holdout_window) < 0:
            raise ValueError("all window arguments must be non-negative")
        if train_window == 0 or test_window == 0:
            raise ValueError("train_window and test_window must be > 0")
        self.train_window = train_window
        self.test_window = test_window
        self.step = step
        self.embargo = embargo
        self.holdout_window = holdout_window
        self.cal = calendar or USEquityCalendar()

    def plan(self, start: date, end: date) -> WalkForwardPlan:
        sessions = self.cal.sessions(start, end)
        if len(sessions) < self.train_window + self.embargo + self.test_window + self.holdout_window:
            raise ValueError("session range too short for the requested splits + holdout")
        holdout_sessions = sessions[-self.holdout_window :]
        optimizable = sessions[: -self.holdout_window]
        splits: list[WalkForwardSplit] = []
        idx = 0
        fold = 1
        while idx + self.train_window + self.embargo + self.test_window <= len(optimizable):
            train_start = optimizable[idx]
            train_end = optimizable[idx + self.train_window - 1]
            embargo_start = optimizable[idx + self.train_window]
            embargo_end = optimizable[idx + self.train_window + self.embargo - 1] if self.embargo > 0 else embargo_start
            test_start = optimizable[idx + self.train_window + self.embargo]
            test_end = optimizable[idx + self.train_window + self.embargo + self.test_window - 1]
            splits.append(
                WalkForwardSplit(
                    fold=fold,
                    train_start=train_start,
                    train_end=train_end,
                    embargo_start=embargo_start,
                    embargo_end=embargo_end,
                    test_start=test_start,
                    test_end=test_end,
                )
            )
            idx += self.step
            fold += 1
        return WalkForwardPlan(
            splits=tuple(splits),
            holdout_start=holdout_sessions[0],
            holdout_end=holdout_sessions[-1],
        )
