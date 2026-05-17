"""Phase 2: intraday-bar quality audit."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.quality import audit_intraday_bars


def _minute_bars(session_date: date, n_minutes: int = 390) -> pd.DataFrame:
    cal = USEquityCalendar()
    times = cal.session_open(session_date)
    rows = []
    for i in range(n_minutes):
        ts = times + pd.Timedelta(minutes=i)
        rows.append((ts, 10.0, 10.1, 9.9, 10.05, 100))
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def test_full_session_passes():
    df = _minute_bars(date(2026, 5, 15), 390)
    res = audit_intraday_bars(df, symbol="X", feed="iex", session_date=date(2026, 5, 15))
    assert res.observed_minutes == 390
    assert res.missing_minutes == 0
    assert res.passed_research_audit


def test_partial_session_flags_missing():
    df = _minute_bars(date(2026, 5, 15), 350)
    res = audit_intraday_bars(df, symbol="X", feed="iex", session_date=date(2026, 5, 15))
    assert res.missing_minutes == 40


def test_early_close_uses_calendar_expected_minutes():
    # 2025-11-28 is the early-close Thanksgiving Friday (210 min session).
    df = _minute_bars(date(2025, 11, 28), 210)
    res = audit_intraday_bars(df, symbol="X", feed="iex", session_date=date(2025, 11, 28))
    assert res.expected_rth_minutes < 390
    assert res.missing_minutes == 0


def test_halt_suspected_when_long_gap():
    df = _minute_bars(date(2026, 5, 15), 30).copy()
    # Inject a 30-minute gap by removing rows.
    df2 = pd.concat([df.iloc[:10], df.iloc[20:]]).reset_index(drop=True)
    res = audit_intraday_bars(df2, symbol="X", feed="iex", session_date=date(2026, 5, 15))
    assert res.halt_suspected
    assert res.longest_intraday_gap_minutes >= 10


def test_duplicate_timestamps_flagged():
    df = _minute_bars(date(2026, 5, 15), 5).copy()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    res = audit_intraday_bars(df, symbol="X", feed="iex", session_date=date(2026, 5, 15))
    assert res.duplicate_timestamps >= 1
    assert not res.passed_research_audit


def test_ohlc_violation_flagged():
    df = _minute_bars(date(2026, 5, 15), 5).copy()
    df.loc[0, "high"] = 1.0  # less than low/open
    df.loc[0, "low"] = 50.0
    res = audit_intraday_bars(df, symbol="X", feed="iex", session_date=date(2026, 5, 15))
    assert res.ohlc_violations >= 1
    assert not res.passed_research_audit


def test_empty_intraday_audit():
    res = audit_intraday_bars(
        pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]),
        symbol="X",
        feed="iex",
        session_date=date(2026, 5, 15),
    )
    assert res.observed_minutes == 0
    assert res.missing_minutes == 390
    assert not res.passed_research_audit
