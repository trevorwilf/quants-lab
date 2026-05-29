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

import contextlib
import datetime as _dt
import functools
from dataclasses import dataclass, field
from typing import Iterator, Optional


class HoldoutGuardError(RuntimeError):
    """Raised when tuning code attempts to read final-holdout data."""


@dataclass
class HoldoutGuard:
    final_holdout_start: _dt.date
    final_holdout_end: _dt.date
    _phase: str = field(default="tuning")  # "tuning" | "final_eval"
    _finalist_read_declared: bool = field(default=False)

    def enter_final_eval(self) -> None:
        self._phase = "final_eval"

    def exit_final_eval(self) -> None:
        self._phase = "tuning"

    def declare_finalist_read(self) -> None:
        """Authorise a single finalist holdout-evaluation phase.

        Speedup report v2 §1.4 / §5.x / Phase 5 task 1. The finalist
        evaluation pipeline is the ONE place where the holdout window may
        be read AFTER tuning has completed. Without this declaration the
        ``assert_can_read`` block continues to refuse holdout reads even
        in ``final_eval`` mode — defence-in-depth against accidental
        re-runs that would re-fit on holdout.
        """
        self._finalist_read_declared = True

    def revoke_finalist_read(self) -> None:
        """Revoke the finalist declaration — typically after the holdout-read phase."""
        self._finalist_read_declared = False

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
        # Speedup report v2 §1.4 / Phase 5 task 1 — the finalist-evaluation
        # pipeline is the one authorised reader of the holdout window AFTER
        # tuning. The declaration is per-guard so a stray test that constructs
        # a fresh ``HoldoutGuard`` does not inherit the authorisation.
        if self._finalist_read_declared:
            return
        raise HoldoutGuardError(
            f"tuning code attempted to read [{start}, {end}) which overlaps "
            f"the final-holdout window [{self.final_holdout_start}, {self.final_holdout_end}); "
            "this would leak holdout information into hyperparameter selection"
        )


def _coerce_date(v: object) -> Optional[_dt.date]:
    if v is None:
        return None
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    try:
        import pandas as pd

        return pd.Timestamp(v).date()
    except Exception:
        try:
            return _dt.date.fromisoformat(str(v)[:10])
        except Exception:
            return None


@contextlib.contextmanager
def tuning_phase_lock(
    final_holdout_start: _dt.date, final_holdout_end: _dt.date,
) -> Iterator[HoldoutGuard]:
    """Process-local tuning-phase lock (audit 2026-05-29 §9 Phase 5 task 6).

    While active, ANY ``MarketDataStore.daily_bars`` / ``minute_bars`` read whose
    ``[start, end)`` overlaps the final-holdout window raises
    :class:`HoldoutGuardError` — defence-in-depth on top of the per-fold
    :meth:`HoldoutGuard.assert_can_read`. The originals are restored on exit, so
    the finalist-evaluation step (run after the lock exits) can read the holdout.
    Each ``process_parallel`` worker installs its own lock.
    """
    from bowaka_common.marketdata.store import MarketDataStore

    guard = HoldoutGuard(final_holdout_start, final_holdout_end)
    originals: dict[str, object] = {}

    def _wrap(method_name: str):
        orig = getattr(MarketDataStore, method_name)
        originals[method_name] = orig

        @functools.wraps(orig)
        def wrapper(self, symbol, start, end, *args, **kwargs):  # noqa: ANN001
            s = _coerce_date(start)
            e = _coerce_date(end)
            if s is not None and e is not None:
                guard.assert_can_read(s, e)
            return orig(self, symbol, start, end, *args, **kwargs)

        setattr(MarketDataStore, method_name, wrapper)

    for name in ("daily_bars", "minute_bars"):
        if hasattr(MarketDataStore, name):
            _wrap(name)
    try:
        yield guard
    finally:
        for name, orig in originals.items():
            setattr(MarketDataStore, name, orig)


__all__ = ["HoldoutGuardError", "HoldoutGuard", "tuning_phase_lock"]
