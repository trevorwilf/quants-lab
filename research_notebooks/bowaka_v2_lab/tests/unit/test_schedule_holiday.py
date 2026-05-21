"""Realism Phase 4 — non-trading days return an empty scan list."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.schedule import expected_scan_count, scan_times_for_session


def _cfg():
    return {
        "session": {
            "calendar": "XNYS",
            "timezone": "America/New_York",
            "scanner_start": "09:45",
            "scanner_end": "15:30",
            "scan_interval_seconds": 60,
        }
    }


def test_christmas_holiday_returns_empty() -> None:
    # 2024-12-25 — XNYS closed for Christmas.
    assert scan_times_for_session(_dt.date(2024, 12, 25), _cfg()) == []
    assert expected_scan_count(_dt.date(2024, 12, 25), _cfg()) == 0


def test_new_years_day_holiday_returns_empty() -> None:
    # 2024-01-01 — XNYS closed for New Year's Day.
    assert scan_times_for_session(_dt.date(2024, 1, 1), _cfg()) == []


def test_saturday_returns_empty() -> None:
    # 2024-09-07 is a Saturday.
    assert scan_times_for_session(_dt.date(2024, 9, 7), _cfg()) == []


def test_sunday_returns_empty() -> None:
    # 2024-09-08 is a Sunday.
    assert scan_times_for_session(_dt.date(2024, 9, 8), _cfg()) == []


def test_normal_session_is_non_empty() -> None:
    # Control: an ordinary trading day is not empty.
    assert len(scan_times_for_session(_dt.date(2024, 9, 4), _cfg())) > 0
