"""Phase 2: USEquityCalendar behavior."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.data.calendar import USEquityCalendar


@pytest.fixture(scope="module")
def cal():
    return USEquityCalendar()


def test_friday_to_monday(cal):
    # 2026-05-15 is a Friday; next trading session is Monday 2026-05-18.
    assert cal.next_session(date(2026, 5, 15)) == date(2026, 5, 18)


def test_friday_before_monday_holiday(cal):
    # Memorial Day 2026 falls on Monday 2026-05-25. Friday 2026-05-22 → Tuesday 2026-05-26.
    assert cal.next_session(date(2026, 5, 22)) == date(2026, 5, 26)


def test_thanksgiving_friday_is_early_close(cal):
    # Friday after Thanksgiving 2025 is 2025-11-28; XNYS closes at 13:00 ET.
    assert cal.is_early_close(date(2025, 11, 28))


def test_christmas_eve_2025_is_early_close(cal):
    # 2025-12-24 was an XNYS early close.
    assert cal.is_early_close(date(2025, 12, 24))


def test_regular_close_has_390_minutes(cal):
    # 2026-05-15 is a regular Friday session.
    assert cal.rth_minutes(date(2026, 5, 15)) == 390


def test_early_close_has_fewer_minutes(cal):
    rth = cal.rth_minutes(date(2025, 11, 28))
    assert rth < 390


def test_rth_minutes_le_390(cal):
    sessions = cal.sessions(date(2025, 1, 1), date(2025, 12, 31))
    for s in sessions:
        assert cal.rth_minutes(s) <= 390


def test_dst_spring_forward(cal):
    # 2026 DST spring forward: 2026-03-08. Next session after 2026-03-06 (Fri)
    # should be Monday 2026-03-09.
    assert cal.next_session(date(2026, 3, 6)) == date(2026, 3, 9)


def test_dst_fall_back(cal):
    # 2025 DST fall back: 2025-11-02. Next session after 2025-10-31 (Fri)
    # should be Monday 2025-11-03.
    assert cal.next_session(date(2025, 10, 31)) == date(2025, 11, 3)


def test_add_sessions_positive(cal):
    # Three trading sessions after Monday 2026-05-18 = Thursday 2026-05-21.
    assert cal.add_sessions(date(2026, 5, 18), 3) == date(2026, 5, 21)


def test_add_sessions_zero(cal):
    assert cal.add_sessions(date(2026, 5, 18), 0) == date(2026, 5, 18)


def test_add_sessions_negative(cal):
    # Two trading sessions before Wednesday 2026-05-20 = Monday 2026-05-18.
    assert cal.add_sessions(date(2026, 5, 20), -2) == date(2026, 5, 18)


def test_add_sessions_skips_holiday(cal):
    # From Friday 2026-05-22, +1 session crosses Memorial Day → Tuesday 2026-05-26.
    assert cal.add_sessions(date(2026, 5, 22), 1) == date(2026, 5, 26)


def test_sessions_between_excludes_weekend(cal):
    sessions = cal.sessions(date(2026, 5, 15), date(2026, 5, 18))
    # Should include Fri 5/15 and Mon 5/18 only.
    assert sessions == [date(2026, 5, 15), date(2026, 5, 18)]


def test_session_times_contains_open_and_close(cal):
    st = cal.session_times(date(2026, 5, 15))
    assert st.open_utc < st.close_utc
    assert isinstance(st.open_utc, pd.Timestamp)
    assert st.rth_minutes == 390
    assert st.is_early_close is False


def test_is_session(cal):
    assert cal.is_session(date(2026, 5, 15)) is True
    # 2026-05-16 is a Saturday.
    assert cal.is_session(date(2026, 5, 16)) is False


def test_previous_session(cal):
    # Previous trading session before Monday 2026-05-18 is Friday 2026-05-15.
    assert cal.previous_session(date(2026, 5, 18)) == date(2026, 5, 15)
