"""Realism remediation 2 Phase 3 — session-level minute-count check (audit §P0-010).

A minute frame missing minutes in the middle of a session is detected by the
session-level checks: the gap is flagged by ``intraday_gap`` (as a ``warn`` —
not a systemic severe-gap shortfall, just a single drop) and the bar count is
short on ``session_minute_count_violation``. A *systemic* shortfall (the only
probed session lacks the expected 390 bars) fails the check.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.data.dq_levels import build_session_checks


def _session_minute_frame(session: dt.date, n_minutes: int, *, gap_at: int | None = None) -> pd.DataFrame:
    """``n_minutes`` consecutive minute bars; optionally omit a single minute."""
    open_et = pd.Timestamp(session, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
    rows = []
    for i in range(n_minutes):
        if gap_at is not None and i == gap_at:
            continue
        ts = (open_et + pd.Timedelta(minutes=i)).tz_convert("UTC")
        rows.append({"timestamp": ts, "open": 10.0, "high": 10.1, "low": 9.9,
                     "close": 10.05, "volume": 1000.0 + i})
    return pd.DataFrame(rows)


def test_full_session_passes_all() -> None:
    session = dt.date(2024, 9, 4)
    df = _session_minute_frame(session, 390)
    checks = build_session_checks(minute_frames_by_session={("AAA", session): df})
    by_name = {c["name"]: c for c in checks}
    assert by_name["session_minute_count_violation"]["status"] == "pass"
    assert by_name["intraday_gap"]["status"] == "pass"


def test_single_session_short_minute_count_fails() -> None:
    """A systemic shortfall (the only probed session) fails the check."""
    session = dt.date(2024, 9, 4)
    df = _session_minute_frame(session, 150)  # 150 << 390 (regular) — systemic
    checks = build_session_checks(minute_frames_by_session={("AAA", session): df})
    by_name = {c["name"]: c for c in checks}
    assert by_name["session_minute_count_violation"]["status"] == "fail"
    ev = by_name["session_minute_count_violation"]["evidence"]
    assert ev["short_sessions"][0]["observed"] == 150
    assert ev["short_sessions"][0]["expected"] == 390


def test_session_with_internal_gap_flagged() -> None:
    """A missing minute in the middle of a session is flagged."""
    session = dt.date(2024, 9, 4)
    # Skip minute index 100, then minutes 101-109 too -> a 10-minute gap.
    rows = []
    open_et = pd.Timestamp(session, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
    for i in range(390):
        if 100 <= i < 110:
            continue
        rows.append({
            "timestamp": (open_et + pd.Timedelta(minutes=i)).tz_convert("UTC"),
            "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.05, "volume": 1000.0,
        })
    df = pd.DataFrame(rows)
    checks = build_session_checks(minute_frames_by_session={("AAA", session): df})
    by_name = {c["name"]: c for c in checks}
    # A single 10-minute gap is not severe (>30 min), so it warns, not fails.
    assert by_name["intraday_gap"]["status"] == "warn"
    ev = by_name["intraday_gap"]["evidence"]
    assert ev["sessions_with_gap"] >= 1


def test_severe_systemic_gap_fails() -> None:
    """Every probed session has a > 30-min gap -> systemic severe shortfall."""
    sessions = [dt.date(2024, 9, 4), dt.date(2024, 9, 5)]
    frames = {}
    for s in sessions:
        rows = []
        open_et = pd.Timestamp(s, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
        for i in range(390):
            if 100 <= i < 150:  # 50-minute gap — severe
                continue
            rows.append({
                "timestamp": (open_et + pd.Timedelta(minutes=i)).tz_convert("UTC"),
                "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.05, "volume": 1000.0,
            })
        frames[("AAA", s)] = pd.DataFrame(rows)
    checks = build_session_checks(minute_frames_by_session=frames)
    by_name = {c["name"]: c for c in checks}
    assert by_name["intraday_gap"]["status"] == "fail"
