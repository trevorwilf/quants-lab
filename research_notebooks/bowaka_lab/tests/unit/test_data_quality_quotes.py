"""Phase 2: quote audits."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.data.quality import audit_quotes, quote_age_at


def _quotes(rows: list[tuple]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["timestamp", "bid_price", "ask_price", "bid_size", "ask_size"])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize("UTC")
    return df


def test_clean_quotes_pass():
    df = _quotes(
        [
            ("2026-05-12 13:30:00", 10.0, 10.02, 100, 100),
            ("2026-05-12 13:30:01", 10.01, 10.03, 100, 100),
        ]
    )
    res = audit_quotes(df, symbol="X", feed="iex", session_date=date(2026, 5, 12))
    assert res.passed_research_audit
    assert res.crossed_quotes == 0
    assert res.max_spread_pct > 0


def test_crossed_quote_flagged():
    df = _quotes([("2026-05-12 13:30:00", 10.05, 10.00, 100, 100)])
    res = audit_quotes(df, symbol="X", feed="iex", session_date=date(2026, 5, 12))
    assert res.crossed_quotes == 1
    assert not res.passed_research_audit


def test_nonpositive_quote_flagged():
    df = _quotes([("2026-05-12 13:30:00", 0.0, 10.00, 100, 100)])
    res = audit_quotes(df, symbol="X", feed="iex", session_date=date(2026, 5, 12))
    assert res.nonpositive_quotes == 1


def test_extreme_spread_counted():
    df = _quotes(
        [
            ("2026-05-12 13:30:00", 10.0, 14.0, 100, 100),  # 40% spread
            ("2026-05-12 13:30:01", 10.0, 10.05, 100, 100),
        ]
    )
    res = audit_quotes(df, symbol="X", feed="iex", session_date=date(2026, 5, 12))
    assert res.extreme_spread_quotes == 1


def test_out_of_order_flagged():
    df = _quotes(
        [
            ("2026-05-12 13:30:02", 10.0, 10.05, 100, 100),
            ("2026-05-12 13:30:01", 10.0, 10.05, 100, 100),
        ]
    )
    res = audit_quotes(df, symbol="X", feed="iex", session_date=date(2026, 5, 12))
    assert res.out_of_order_timestamps == 1
    assert not res.passed_research_audit


def test_quote_age_at_timestamp_returns_seconds():
    df = _quotes(
        [
            ("2026-05-12 13:30:00", 10.0, 10.02, 100, 100),
            ("2026-05-12 13:30:30", 10.01, 10.03, 100, 100),
        ]
    )
    at = pd.Timestamp("2026-05-12 13:31:00", tz="UTC")
    age = quote_age_at(df, at=at)
    assert age == 30.0


def test_quote_age_empty_quotes_returns_inf():
    df = _quotes([])
    at = pd.Timestamp("2026-05-12 13:31:00", tz="UTC")
    assert quote_age_at(df, at=at) == float("inf")
