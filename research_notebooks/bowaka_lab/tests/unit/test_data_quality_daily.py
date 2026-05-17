"""Phase 2: daily-bar quality audits."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.quality import audit_daily_bars


def _make_bars(rows: list[tuple], tz_aware: bool = True) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if tz_aware:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    return df


def test_clean_bars_pass_audit():
    cal = USEquityCalendar()
    sessions = cal.sessions(date(2026, 5, 11), date(2026, 5, 15))
    rows = [(pd.Timestamp(s, tz="UTC"), 10, 11, 9, 10.5, 1000) for s in sessions]
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    res = audit_daily_bars(df, symbol="X", feed="iex", start=date(2026, 5, 11), end=date(2026, 5, 15), calendar=cal)
    assert res.passed_research_audit
    assert res.duplicate_sessions == 0
    assert res.ohlc_violations == 0
    assert res.observed_sessions == len(sessions)


def test_duplicate_sessions_flagged():
    df = _make_bars(
        [
            ("2026-05-11", 10, 11, 9, 10.5, 1000),
            ("2026-05-11", 10, 11, 9, 10.5, 1000),
            ("2026-05-12", 10.5, 11, 10, 10.8, 1100),
        ]
    )
    res = audit_daily_bars(df, symbol="X", feed="iex", start=date(2026, 5, 11), end=date(2026, 5, 12))
    assert res.duplicate_sessions >= 1
    assert not res.passed_research_audit


def test_ohlc_violation_flagged():
    df = _make_bars(
        [
            ("2026-05-11", 10, 9, 11, 10.5, 1000),  # high < open, low > open
        ]
    )
    res = audit_daily_bars(df, symbol="X", feed="iex", start=date(2026, 5, 11), end=date(2026, 5, 11))
    assert res.ohlc_violations >= 1
    assert not res.passed_research_audit


def test_zero_volume_counted():
    df = _make_bars(
        [
            ("2026-05-11", 10, 11, 9, 10.5, 0),
            ("2026-05-12", 10, 11, 9, 10.5, 1000),
        ]
    )
    res = audit_daily_bars(df, symbol="X", feed="iex", start=date(2026, 5, 11), end=date(2026, 5, 12))
    assert res.zero_volume_sessions == 1


def test_large_gap_flagged_as_split_suspect():
    df = _make_bars(
        [
            ("2026-05-11", 10, 11, 9, 10.5, 1000),
            ("2026-05-12", 5.2, 5.4, 5.0, 5.3, 1000),  # ~50% gap-down → suspected reverse split
        ]
    )
    res = audit_daily_bars(df, symbol="X", feed="iex", start=date(2026, 5, 11), end=date(2026, 5, 12))
    assert res.large_gap_flags >= 1


def test_empty_dataframe():
    df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    res = audit_daily_bars(df, symbol="X", feed="iex", start=date(2026, 5, 11), end=date(2026, 5, 11))
    assert res.observed_sessions == 0
    assert not res.passed_research_audit
    assert "no_data" in res.warnings
