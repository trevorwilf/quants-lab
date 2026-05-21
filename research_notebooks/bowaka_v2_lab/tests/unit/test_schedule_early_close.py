"""Realism Phase 4 — early-close days truncate the scan window.

The live scanner (``bowaka_intraday_scanner.py`` ``_run_live``) builds its loop
bound purely from the configured ``scanner_end`` and never consults the exchange
calendar — on an early-close day it would tick past the real close. The Phase 4
scheduler deliberately **deviates**: it truncates the window to the exchange's
early close so a backtest never emits a scan into a closed market. The deviation
is documented in ``docs/current_code_vs_intended_realism.md`` (section 5).
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.schedule import scan_times_for_session


def _cfg(**session_overrides):
    session = {
        "calendar": "XNYS",
        "timezone": "America/New_York",
        "scanner_start": "09:45",
        "scanner_end": "15:30",
        "scan_interval_seconds": 60,
    }
    session.update(session_overrides)
    return {"session": session}


def test_early_close_truncates_to_one_pm_et() -> None:
    # 2024-11-29 (day after Thanksgiving) — XNYS closes 13:00 ET.
    scans = scan_times_for_session(_dt.date(2024, 11, 29), _cfg())
    assert scans, "early-close day is still a trading session"
    last_et = scans[-1].tz_convert("America/New_York")
    # Window truncated to the 13:00 ET early close, not the 15:30 ET scanner_end.
    assert last_et.hour == 13 and last_et.minute == 0
    # 09:45 -> 13:00 ET at 60s = (3h15m)/60 + 1 = 196 scans.
    assert len(scans) == 196


def test_christmas_eve_early_close_also_truncates() -> None:
    # 2024-12-24 (Christmas Eve) — XNYS closes 13:00 ET.
    scans = scan_times_for_session(_dt.date(2024, 12, 24), _cfg())
    assert scans
    last_et = scans[-1].tz_convert("America/New_York")
    assert (last_et.hour, last_et.minute) == (13, 0)


def test_normal_day_not_truncated_by_early_close_logic() -> None:
    # A normal session's 16:00 ET close is well past scanner_end (15:30 ET),
    # so the early-close truncation is a no-op.
    scans = scan_times_for_session(_dt.date(2024, 9, 4), _cfg())
    assert scans[-1] == pd.Timestamp("2024-09-04 19:30:00", tz="UTC")
    assert len(scans) == 346


def test_early_close_before_scanner_start_yields_empty() -> None:
    # Pathological: scanner_start after the early close — no scans.
    scans = scan_times_for_session(
        _dt.date(2024, 11, 29), _cfg(scanner_start="14:00", scanner_end="15:30")
    )
    assert scans == []
