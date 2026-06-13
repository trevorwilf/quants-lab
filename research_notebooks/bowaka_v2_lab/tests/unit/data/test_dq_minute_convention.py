"""P1 (L1) — the ``minute_bar_stamp_convention`` DQ check pins the START-of-
interval stamping the PIT forming-bar cutoff depends on. START-stamped regular
sessions open at 09:30 ET; an END-stamped lake would open at 09:31 (no 09:30
bar), which would silently invalidate the ``scan_ts - 60s`` cutoff.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.data.dq_levels import build_session_checks

_COLS = ["timestamp", "open", "high", "low", "close", "volume"]


def _frame(session: dt.date, first_hh: int, first_mm: int, n: int) -> pd.DataFrame:
    base = pd.Timestamp(
        dt.datetime.combine(session, dt.time(first_hh, first_mm)), tz="America/New_York"
    )
    rows = [
        ((base + pd.Timedelta(minutes=i)).tz_convert("UTC"), 10.0, 10.1, 9.9, 10.0, 100.0)
        for i in range(n)
    ]
    return pd.DataFrame(rows, columns=_COLS)


def _conv(checks: list[dict]) -> dict:
    return next(c for c in checks if c["name"] == "minute_bar_stamp_convention")


def test_convention_passes_on_start_stamped_lake() -> None:
    sessions = [dt.date(2025, 8, d) for d in (20, 21, 22)]
    frames = {(f"S{i}", s): _frame(s, 9, 30, 380) for i, s in enumerate(sessions)}
    assert _conv(build_session_checks(minute_frames_by_session=frames))["status"] == "pass"


def test_convention_fails_on_end_stamped_lake() -> None:
    # First regular bar at 09:31 with no 09:30 bar across every probed session ->
    # END-stamp signature -> fail-closed.
    sessions = [dt.date(2025, 8, d) for d in (20, 21, 22)]
    frames = {(f"S{i}", s): _frame(s, 9, 31, 380) for i, s in enumerate(sessions)}
    assert _conv(build_session_checks(minute_frames_by_session=frames))["status"] == "fail"
