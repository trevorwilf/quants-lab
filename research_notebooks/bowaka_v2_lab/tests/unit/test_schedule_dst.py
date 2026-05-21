"""Realism Phase 4 — DST transitions produce correct UTC scan timestamps.

US DST: spring-forward 2024-03-10 (EST→EDT), fall-back 2024-11-03 (EDT→EST).
Both fall on a Sunday so are not trading sessions; the test uses the adjacent
Monday sessions, which carry the *new* offset:

- 2024-03-11 is in EDT (UTC-4) → 09:45 ET = 13:45 UTC.
- 2024-11-04 is in EST (UTC-5) → 09:45 ET = 14:45 UTC.

A session that pre-dates the spring-forward (e.g. 2024-03-08) is still EST.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.schedule import scan_times_for_session


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


def test_session_before_spring_forward_is_est() -> None:
    # 2024-03-08 (Friday before spring-forward) — EST, UTC-5.
    scans = scan_times_for_session(_dt.date(2024, 3, 8), _cfg())
    assert scans[0] == pd.Timestamp("2024-03-08 14:45:00", tz="UTC")
    assert scans[-1] == pd.Timestamp("2024-03-08 20:30:00", tz="UTC")


def test_session_after_spring_forward_is_edt() -> None:
    # 2024-03-11 (Monday after spring-forward) — EDT, UTC-4.
    scans = scan_times_for_session(_dt.date(2024, 3, 11), _cfg())
    assert scans[0] == pd.Timestamp("2024-03-11 13:45:00", tz="UTC")
    assert scans[-1] == pd.Timestamp("2024-03-11 19:30:00", tz="UTC")
    # Same count either side of the transition — the local window is unchanged.
    assert len(scans) == 346


def test_session_before_fall_back_is_edt() -> None:
    # 2024-11-01 (Friday before fall-back) — EDT, UTC-4.
    scans = scan_times_for_session(_dt.date(2024, 11, 1), _cfg())
    assert scans[0] == pd.Timestamp("2024-11-01 13:45:00", tz="UTC")
    assert scans[-1] == pd.Timestamp("2024-11-01 19:30:00", tz="UTC")


def test_session_after_fall_back_is_est() -> None:
    # 2024-11-04 (Monday after fall-back) — EST, UTC-5.
    scans = scan_times_for_session(_dt.date(2024, 11, 4), _cfg())
    assert scans[0] == pd.Timestamp("2024-11-04 14:45:00", tz="UTC")
    assert scans[-1] == pd.Timestamp("2024-11-04 20:30:00", tz="UTC")
    assert len(scans) == 346


def test_dst_count_invariant() -> None:
    # The scan count depends only on the local window + interval, never on the
    # UTC offset — equal on EDT and EST sessions.
    edt = scan_times_for_session(_dt.date(2024, 3, 11), _cfg())
    est = scan_times_for_session(_dt.date(2024, 11, 4), _cfg())
    assert len(edt) == len(est) == 346
