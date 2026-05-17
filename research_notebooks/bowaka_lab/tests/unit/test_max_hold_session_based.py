"""Phase 4: §F.4 max_hold_days counts trading sessions, not calendar days."""

from __future__ import annotations

from datetime import date

from bowaka_lab.data.calendar import USEquityCalendar


def test_max_hold_skips_weekend():
    cal = USEquityCalendar()
    # Enter Friday 2026-05-15; max_hold_days=3 → exit by Wednesday 2026-05-20.
    exit_date = cal.add_sessions(date(2026, 5, 15), 3)
    assert exit_date == date(2026, 5, 20)


def test_max_hold_skips_holiday():
    cal = USEquityCalendar()
    # Enter Friday 2026-05-22; +1 trading day = Tuesday 2026-05-26 (Memorial Day Monday is closed).
    exit_date = cal.add_sessions(date(2026, 5, 22), 1)
    assert exit_date == date(2026, 5, 26)


def test_max_hold_three_sessions_across_weekend_and_holiday():
    cal = USEquityCalendar()
    # Enter Friday 2026-05-22; +3 sessions = Thursday 2026-05-28.
    exit_date = cal.add_sessions(date(2026, 5, 22), 3)
    assert exit_date == date(2026, 5, 28)


def test_max_hold_zero_is_same_day():
    cal = USEquityCalendar()
    assert cal.add_sessions(date(2026, 5, 22), 0) == date(2026, 5, 22)
