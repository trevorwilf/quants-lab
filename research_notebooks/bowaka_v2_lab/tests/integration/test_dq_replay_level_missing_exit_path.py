"""Realism remediation 2 Phase 3 — replay-level exit-path coverage (§P0-010).

A fixture lake with entry-minute bars but no forward minute bars across the
strategy's ``max_hold_days`` window fails ``coverage_missing_exit_path`` —
without forward minutes the simulator cannot evaluate a stop / target /
max-hold exit. Under ``intended_realism`` this becomes a required failure.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.data.dq_levels import build_replay_checks


def test_missing_exit_path_fails_replay_check() -> None:
    sessions = [
        dt.date(2024, 9, 4),  # entry session
        dt.date(2024, 9, 5),  # forward d+1
        dt.date(2024, 9, 6),  # forward d+2
        dt.date(2024, 9, 9),  # forward d+3 (skipping weekend)
    ]
    scan_times = [pd.Timestamp(f"2024-09-{d.day:02d} 13:45:00", tz="UTC") for d in sessions]
    # Only the entry session has minute bars; forward sessions return empty.

    def minute_supplier(symbol, ts):
        t = pd.Timestamp(ts)
        if t.date() == dt.date(2024, 9, 4):
            return pd.DataFrame(
                [{"symbol": symbol, "timestamp": t, "open": 10.0, "high": 10.1,
                  "low": 9.9, "close": 10.0, "volume": 1000.0}]
            )
        return pd.DataFrame()

    def scan_times_per_session(d):
        return [t for t in scan_times if t.date() == d]

    checks = build_replay_checks(
        requested_symbols=["AAA", "BBB"],
        sessions=sessions,
        minute_bars_supplier=minute_supplier,
        scan_times_per_session=scan_times_per_session,
        max_hold_days=3,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["coverage_missing_exit_path"]["status"] == "fail"
    ev = by_name["coverage_missing_exit_path"]["evidence"]
    assert ev["missing"] >= 2  # both symbols across forward sessions


def test_exit_path_present_passes() -> None:
    sessions = [dt.date(2024, 9, 4), dt.date(2024, 9, 5), dt.date(2024, 9, 6)]
    scan_times = [pd.Timestamp(f"2024-09-{d.day:02d} 13:45:00", tz="UTC") for d in sessions]

    def minute_supplier(symbol, ts):
        return pd.DataFrame(
            [{"symbol": symbol, "timestamp": pd.Timestamp(ts), "open": 10.0,
              "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1000.0}]
        )

    def scan_times_per_session(d):
        return [t for t in scan_times if t.date() == d]

    checks = build_replay_checks(
        requested_symbols=["AAA"],
        sessions=sessions,
        minute_bars_supplier=minute_supplier,
        scan_times_per_session=scan_times_per_session,
        max_hold_days=2,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["coverage_missing_exit_path"]["status"] == "pass"
