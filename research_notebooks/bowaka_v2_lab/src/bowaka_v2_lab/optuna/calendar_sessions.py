"""Shared half-open XNYS session helper (speedup report §3, §11.1).

The walk-forward planner uses half-open ``[start, end)`` windows
(audit 2026-05-23 §P0-002): a fold whose ``val_end == final_holdout_start``
must NOT include the holdout's first session. ``exchange_calendars``'
``sessions_in_range`` is closed-closed, so the half-open semantics is emulated
by stepping the end back by one day before calling it. ``start == end`` yields
an empty list.

This module is the single source of truth for that helper — both
:mod:`bowaka_v2_lab.optuna.walkforward_runner` and
:mod:`bowaka_v2_lab.optuna.pit_universe` import it so the two cannot drift.
"""
from __future__ import annotations

import datetime as _dt
from typing import List

import pandas as pd


def calendar_sessions_half_open(
    start: _dt.date,
    end: _dt.date,
    *,
    calendar: str = "XNYS",
) -> List[_dt.date]:
    """Return the trading sessions in the half-open ``[start, end)`` window.

    ``start == end`` (or any ``start >= end``) yields ``[]`` — a zero-length
    window has no sessions. The end date itself is **excluded** even when it
    is a trading day; this is the property the walk-forward planner relies on
    to prevent a fold from leaking into the final holdout window.
    """
    import exchange_calendars as xcals

    if start >= end:
        return []
    cal = xcals.get_calendar(calendar)
    closed_end = pd.Timestamp(end) - pd.Timedelta(days=1)
    sessions = cal.sessions_in_range(pd.Timestamp(start), closed_end)
    return [pd.Timestamp(s).date() for s in sessions]


__all__ = ["calendar_sessions_half_open"]
