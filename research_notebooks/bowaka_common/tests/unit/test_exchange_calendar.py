"""Exchange-calendar helpers: holidays, DST transitions, session boundaries."""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_common.calendar.exchange import USEquityCalendar


def test_calendar_constructs() -> None:
    cal = USEquityCalendar()
    assert cal is not None


def test_july_fourth_2024_is_closed_or_early_close() -> None:
    cal = USEquityCalendar()
    # July 4, 2024 was a Thursday, a market holiday.
    assert cal.is_session(_dt.date(2024, 7, 4)) is False
    # July 3, 2024 was an early-close day (1pm ET).
    if cal.is_session(_dt.date(2024, 7, 3)):
        assert cal.is_early_close(_dt.date(2024, 7, 3)) is True


def test_dst_spring_forward_session_present() -> None:
    cal = USEquityCalendar()
    sessions = cal.sessions(_dt.date(2024, 3, 8), _dt.date(2024, 3, 12))
    # 2024-03-10 is Sunday (no session); 03-11 is Monday and should be present.
    assert _dt.date(2024, 3, 11) in sessions
    # Sundays excluded.
    assert _dt.date(2024, 3, 10) not in sessions


def test_session_open_close_for_normal_day() -> None:
    cal = USEquityCalendar()
    times = cal.session_times(_dt.date(2024, 4, 15))
    assert times is not None
    # 09:30 ET on a non-DST day in April == 13:30 UTC (EDT, UTC-4).
    assert times.open_utc.hour == 13
    assert times.open_utc.minute == 30
    # 16:00 ET == 20:00 UTC
    assert times.close_utc.hour == 20
    assert times.close_utc.minute == 0
    assert times.rth_minutes == 390


def test_iter_sessions_excludes_weekends() -> None:
    cal = USEquityCalendar()
    sessions = list(cal.iter_sessions(_dt.date(2024, 4, 1), _dt.date(2024, 4, 7)))
    # Monday April 1 through Sunday April 7 → 5 weekday sessions
    assert len(sessions) == 5
    for s in sessions:
        assert s.weekday() < 5
