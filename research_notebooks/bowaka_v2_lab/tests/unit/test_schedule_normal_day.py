"""Realism Phase 4 — ``scan_times_for_session`` on a normal XNYS session.

A 09:45→15:30 ET window at a 60s interval produces ``(15:30-09:45)/60 + 1 = 346``
inclusive scan timestamps, all tz-aware UTC and strictly increasing.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.schedule import expected_scan_count, scan_times_for_session


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


def test_normal_day_produces_346_scans() -> None:
    # 2024-09-04 is an ordinary Wednesday XNYS session.
    scans = scan_times_for_session(_dt.date(2024, 9, 4), _cfg())
    assert len(scans) == 346
    assert expected_scan_count(_dt.date(2024, 9, 4), _cfg()) == 346


def test_normal_day_endpoints_inclusive_and_utc() -> None:
    scans = scan_times_for_session(_dt.date(2024, 9, 4), _cfg())
    # 09:45 ET = 13:45 UTC (EDT, -4) ; 15:30 ET = 19:30 UTC. Both endpoints present.
    assert scans[0] == pd.Timestamp("2024-09-04 13:45:00", tz="UTC")
    assert scans[-1] == pd.Timestamp("2024-09-04 19:30:00", tz="UTC")
    for ts in scans:
        assert ts.tzinfo is not None
        assert str(ts.tz) == "UTC"


def test_normal_day_strictly_increasing_at_interval() -> None:
    scans = scan_times_for_session(_dt.date(2024, 9, 4), _cfg())
    diffs = {(b - a) for a, b in zip(scans, scans[1:])}
    assert diffs == {pd.Timedelta(seconds=60)}


def test_custom_interval_changes_count() -> None:
    # 5-minute cadence: (15:30-09:45)/300 + 1 = 70 scans.
    scans = scan_times_for_session(_dt.date(2024, 9, 4), _cfg(scan_interval_seconds=300))
    assert len(scans) == 70


def test_accepts_validated_config_object() -> None:
    # scan_times_for_session must accept a Pydantic BowakaV2Config too.
    from bowaka_v2_lab.config.models import BowakaV2Config

    cfg = BowakaV2Config.model_validate(
        {
            "strategy_id": "bowaka_v2",
            "market_data": {"feed": "iex"},
            "session": {"scanner_start": "09:45", "scanner_end": "15:30",
                        "scan_interval_seconds": 60},
            "paths": {"lab_root": "x", "data_root": "x", "artifact_root": "x"},
        }
    )
    assert len(scan_times_for_session(_dt.date(2024, 9, 4), cfg)) == 346
