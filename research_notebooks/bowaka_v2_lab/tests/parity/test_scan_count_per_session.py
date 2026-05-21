"""Realism Phase 4 — scan cadence matches the live scanner on a normal session.

The live scanner (``bowaka_intraday_scanner.py`` ``_run_live``) ticks every
``scan_interval_seconds`` between ``scanner_start`` and ``scanner_end`` (ET).
The Phase-4 ``scan_times_for_session`` must reproduce that cadence: with the
frozen-contract values (``scan_interval_seconds: 60``, ``scanner_start: 09:45``,
``scanner_end: 15:30``) a normal session has ``(15:30-09:45)/60 + 1 = 346``
scans.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.schedule import scan_times_for_session


def _live_cadence_cfg():
    """The session block with the live frozen-contract scan cadence."""
    return {
        "session": {
            "calendar": "XNYS",
            "timezone": "America/New_York",
            "scanner_start": "09:45",
            "scanner_end": "15:30",
            "scan_interval_seconds": 60,
        }
    }


def _expected_count(start: str, end: str, interval_s: int) -> int:
    """The inclusive-endpoint scan count the live loop would tick."""
    s = pd.Timestamp(f"2024-09-04 {start}", tz="America/New_York")
    e = pd.Timestamp(f"2024-09-04 {end}", tz="America/New_York")
    return int((e - s).total_seconds() // interval_s) + 1


def test_scan_count_matches_live_cadence_normal_session() -> None:
    cfg = _live_cadence_cfg()
    scans = scan_times_for_session(_dt.date(2024, 9, 4), cfg)
    assert len(scans) == _expected_count("09:45", "15:30", 60) == 346


def test_scan_window_endpoints_match_configured_session() -> None:
    cfg = _live_cadence_cfg()
    scans = scan_times_for_session(_dt.date(2024, 9, 4), cfg)
    first_et = scans[0].tz_convert("America/New_York")
    last_et = scans[-1].tz_convert("America/New_York")
    # The live loop starts at scanner_start and stops at scanner_end.
    assert (first_et.hour, first_et.minute) == (9, 45)
    assert (last_et.hour, last_et.minute) == (15, 30)


def test_cadence_interval_is_exactly_scan_interval_seconds() -> None:
    cfg = _live_cadence_cfg()
    scans = scan_times_for_session(_dt.date(2024, 9, 4), cfg)
    gaps = {(b - a).total_seconds() for a, b in zip(scans, scans[1:])}
    assert gaps == {60.0}


def test_contract_scan_interval_is_60s() -> None:
    # Guard: the frozen live contract pins scan_interval_seconds: 60. If the
    # contract changes this number, the 346-scan expectation above must too.
    from bowaka_v2_lab.reference import contract_available, load_actual_contract

    if not contract_available():
        import pytest

        pytest.skip("frozen contract not generated on this host")
    contract = load_actual_contract()
    scanner = contract.get("scanner") or {}
    assert int(scanner.get("scan_interval_seconds", 60)) == 60
