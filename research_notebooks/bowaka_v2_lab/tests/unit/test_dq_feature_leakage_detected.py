"""Realism remediation 2 Phase 3 — feature-leakage check (audit §P0-010).

A daily-feature cache that contains a row whose ``session_date`` is the scan
session itself (or any later session) is same-day leakage — feature gates
(RVOL / ATR / EMA / price-band) would compute on data that wasn't available at
scan time. The ``feature_leakage`` check flags this as ``fail``.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.data.dq_levels import build_feature_checks


def test_feature_leakage_detected_same_day() -> None:
    """A daily cache row whose ``session_date`` equals the scan session fails."""
    scan_session = dt.date(2024, 9, 4)
    cache = pd.DataFrame(
        [
            {"symbol": "AAA", "session_date": dt.date(2024, 9, 2)},  # prior — ok
            {"symbol": "AAA", "session_date": dt.date(2024, 9, 3)},  # prior — ok
            {"symbol": "AAA", "session_date": scan_session},          # SAME DAY — leakage
        ]
    )
    checks = build_feature_checks(
        daily_cache_by_session={scan_session: cache},
        require_adjusted_daily_bars=False,
        lake_adjustment="raw",
        corporate_actions_available=False,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["feature_leakage"]["status"] == "fail"
    ev = by_name["feature_leakage"]["evidence"]
    assert ev["leaking_sessions"][0]["scan_session"] == scan_session.isoformat()
    assert ev["leaking_sessions"][0]["leaked_rows"] >= 1


def test_feature_leakage_future_row() -> None:
    """A daily cache row dated *after* the scan session also fails."""
    scan_session = dt.date(2024, 9, 4)
    cache = pd.DataFrame(
        [{"symbol": "AAA", "session_date": dt.date(2024, 9, 5)}]  # future — leakage
    )
    checks = build_feature_checks(
        daily_cache_by_session={scan_session: cache},
        require_adjusted_daily_bars=False,
        lake_adjustment="raw",
        corporate_actions_available=False,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["feature_leakage"]["status"] == "fail"


def test_feature_leakage_clean_cache_passes() -> None:
    """A cache with only prior sessions passes."""
    scan_session = dt.date(2024, 9, 4)
    cache = pd.DataFrame(
        [
            {"symbol": "AAA", "session_date": dt.date(2024, 9, 2)},
            {"symbol": "AAA", "session_date": dt.date(2024, 9, 3)},
            {"symbol": "BBB", "session_date": dt.date(2024, 9, 3)},
        ]
    )
    checks = build_feature_checks(
        daily_cache_by_session={scan_session: cache},
        require_adjusted_daily_bars=False,
        lake_adjustment="raw",
        corporate_actions_available=False,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["feature_leakage"]["status"] == "pass"


def test_feature_split_unaware_warning_when_required_and_raw() -> None:
    """``require_adjusted_daily_bars=True`` + raw lake + no CA -> ``warn``."""
    checks = build_feature_checks(
        daily_cache_by_session={},
        require_adjusted_daily_bars=True,
        lake_adjustment="raw",
        corporate_actions_available=False,
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["feature_split_unaware"]["status"] == "warn"
