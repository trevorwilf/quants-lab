"""Final-holdout write-guard.

Per [Report §14.4]: tuning code must NEVER read from the final-holdout window.
A central guard tracks the active phase and raises if a tuning step attempts a
forbidden read.

Audit 2026-05-23 §P0-002 — all intervals are half-open ``[start, end)``. A
fold whose ``val_end == final_holdout_start`` is allowed; a fold whose
``val_start == final_holdout_end`` is allowed. Pre-remediation the guard used
closed-interval semantics and rejected the boundary-equal case, which the
walk-forward planner then admitted, and the broad ``except Exception`` in the
objective swallowed the resulting :class:`HoldoutGuardError` as
``_FAILED_TRIAL_SCORE``. After this fix the guard matches the planner's
half-open semantics; any true overlap still raises.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional


class HoldoutGuardError(RuntimeError):
    """Raised when tuning code attempts to read final-holdout data."""


@dataclass
class HoldoutGuard:
    final_holdout_start: _dt.date
    final_holdout_end: _dt.date
    _phase: str = field(default="tuning")  # "tuning" | "final_eval"

    def enter_final_eval(self) -> None:
        self._phase = "final_eval"

    def exit_final_eval(self) -> None:
        self._phase = "tuning"

    def assert_can_read(self, start: _dt.date, end: _dt.date) -> None:
        """Raise if ``[start, end)`` overlaps the final-holdout window during tuning.

        Half-open: ``end == final_holdout_start`` is allowed (the read finishes
        exactly when the holdout begins); ``start == final_holdout_end`` is
        allowed (the read begins exactly when the holdout ends); any true
        overlap raises. See audit 2026-05-23 §P0-002.
        """
        if self._phase == "final_eval":
            return
        # half-open [start, end) — see audit 2026-05-23 §P0-002
        if end <= self.final_holdout_start or start >= self.final_holdout_end:
            return
        raise HoldoutGuardError(
            f"tuning code attempted to read [{start}, {end}) which overlaps "
            f"the final-holdout window [{self.final_holdout_start}, {self.final_holdout_end}); "
            "this would leak holdout information into hyperparameter selection"
        )
