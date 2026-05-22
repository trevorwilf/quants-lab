"""Realism remediation 2 Phase 3 — replay-level late-session coverage (§P0-010).

A fixture lake whose minute supplier returns bars at the first scan time but
none at later scan times fails ``coverage_missing_late_session``. Under
``intended_realism`` this becomes a required failure that aborts the run.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.data.dq_levels import build_replay_checks


def test_late_session_minute_missing_fails_replay_check() -> None:
    sessions = [dt.date(2024, 9, 4)]
    scan_times = [
        pd.Timestamp("2024-09-04 13:45:00", tz="UTC"),  # 09:45 ET
        pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        pd.Timestamp("2024-09-04 14:15:00", tz="UTC"),
        pd.Timestamp("2024-09-04 14:30:00", tz="UTC"),
    ]
    symbols = ["AAA", "BBB"]

    def minute_supplier(symbol, ts):
        # Return bars only at the FIRST scan timestamp; every later scan -> empty.
        if pd.Timestamp(ts) == scan_times[0]:
            return pd.DataFrame(
                [{"symbol": symbol, "timestamp": pd.Timestamp(ts),
                  "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0,
                  "volume": 1000.0}]
            )
        return pd.DataFrame()

    checks = build_replay_checks(
        requested_symbols=symbols,
        sessions=sessions,
        minute_bars_supplier=minute_supplier,
        scan_times_per_session=lambda d: scan_times,
        max_hold_days=1,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["coverage_missing_late_session"]["status"] == "fail"
    ev = by_name["coverage_missing_late_session"]["evidence"]
    # 3 later scans * 2 symbols = 6 probes, all missing
    assert ev["probes"] == 6
    assert ev["missing"] == 6


def test_late_session_minute_present_passes() -> None:
    sessions = [dt.date(2024, 9, 4)]
    scan_times = [
        pd.Timestamp("2024-09-04 13:45:00", tz="UTC"),
        pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        pd.Timestamp("2024-09-04 14:15:00", tz="UTC"),
    ]

    def minute_supplier(symbol, ts):
        return pd.DataFrame(
            [{"symbol": symbol, "timestamp": pd.Timestamp(ts), "open": 10.0,
              "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1000.0}]
        )

    checks = build_replay_checks(
        requested_symbols=["AAA"],
        sessions=sessions,
        minute_bars_supplier=minute_supplier,
        scan_times_per_session=lambda d: scan_times,
        max_hold_days=1,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["coverage_missing_late_session"]["status"] == "pass"
