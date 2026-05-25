"""Half-open ``[start, end)`` XNYS session helper (speedup report §3 / audit §P0-002).

Phase 0. The walk-forward planner uses half-open windows; the session
enumerator must honour that — a fold whose ``val_end == final_holdout_start``
must NOT include the holdout's first session. This test fixes both helpers
(walk-forward runner + PIT preflight) to the same half-open contract via
the shared :func:`calendar_sessions_half_open`.
"""
from __future__ import annotations

import datetime as dt
import random

import pytest

from bowaka_v2_lab.optuna.calendar_sessions import calendar_sessions_half_open
from bowaka_v2_lab.optuna.pit_universe import _xnys_sessions as pit_xnys
from bowaka_v2_lab.optuna.walkforward_runner import _xnys_sessions as wf_xnys


def test_excludes_trading_day_end():
    """``end`` is excluded even when it is a trading day."""
    # 2025-10-27 is a Monday (a trading day).
    sessions = calendar_sessions_half_open(dt.date(2025, 9, 27), dt.date(2025, 10, 27))
    assert dt.date(2025, 10, 27) not in sessions
    # The prior Friday IS included.
    assert dt.date(2025, 10, 24) in sessions


def test_single_day_window_is_empty():
    """``start == end`` is a zero-length window — no sessions."""
    assert calendar_sessions_half_open(dt.date(2024, 6, 3), dt.date(2024, 6, 3)) == []
    assert calendar_sessions_half_open(dt.date(2024, 6, 4), dt.date(2024, 6, 3)) == []


def test_weekend_end_returns_full_inclusive_set():
    """``end`` on a Saturday returns every weekday in the window (Saturday is
    not a session, so excluding it from the half-open window has no effect)."""
    sat = dt.date(2025, 10, 25)  # Saturday
    fri = dt.date(2025, 10, 24)  # Friday — the last session before sat
    half = set(calendar_sessions_half_open(dt.date(2025, 9, 27), sat))
    # The closed-closed answer through Friday equals the half-open answer
    # through Saturday: both include Friday and exclude Saturday.
    closed_through_friday_inclusive = set(
        calendar_sessions_half_open(dt.date(2025, 9, 27), fri + dt.timedelta(days=1))
    )
    assert half == closed_through_friday_inclusive
    assert sat not in half
    assert fri in half


def test_pit_universe_helper_and_runner_helper_agree():
    """Both XNYS helpers (PIT preflight + walk-forward runner) must agree."""
    rng = random.Random(20260524)
    base = dt.date(2023, 1, 1)
    for _ in range(20):
        d1_offset = rng.randint(0, 600)
        d2_offset = rng.randint(d1_offset, d1_offset + 365)
        start = base + dt.timedelta(days=d1_offset)
        end = base + dt.timedelta(days=d2_offset)
        a = pit_xnys(start, end)
        b = wf_xnys(start, end)
        c = calendar_sessions_half_open(start, end)
        assert a == b == c, (
            f"helpers disagree for [{start}, {end}): "
            f"pit={a[:3]}..{a[-3:] if len(a) > 3 else a}, "
            f"wf={b[:3]}..{b[-3:] if len(b) > 3 else b}, "
            f"shared={c[:3]}..{c[-3:] if len(c) > 3 else c}"
        )


def test_holdout_boundary_fold_does_not_include_holdout_start():
    """The regression that motivated the half-open switch (audit §P0-002):
    ``val_end == final_holdout_start`` must NOT include the holdout's first
    session in the validation window."""
    # 2024-10-21 is a Monday (trading day) — pretend it's the holdout start.
    holdout_start = dt.date(2024, 10, 21)
    val_window = calendar_sessions_half_open(dt.date(2024, 9, 23), holdout_start)
    assert holdout_start not in val_window
    # The prior Friday (2024-10-18) IS in the validation window.
    assert dt.date(2024, 10, 18) in val_window


@pytest.mark.parametrize("start_offset,end_offset", [(0, 1), (10, 11), (0, 30)])
def test_known_windows_match_closed_minus_end(start_offset, end_offset):
    """Independent oracle: half-open(start, end) ≡ closed-closed(start, end-1)."""
    import exchange_calendars as xcals
    import pandas as pd

    cal = xcals.get_calendar("XNYS")
    base = dt.date(2024, 1, 2)
    start = base + dt.timedelta(days=start_offset)
    end = base + dt.timedelta(days=end_offset)
    closed_end = end - dt.timedelta(days=1)
    if closed_end < start:
        oracle: list[dt.date] = []
    else:
        oracle = [
            pd.Timestamp(s).date()
            for s in cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(closed_end))
        ]
    assert calendar_sessions_half_open(start, end) == oracle
