"""Data quality audits for daily, intraday, and quote datasets.

All audit functions return JSON-serializable dicts so they can be persisted to
Mongo (``bowaka_daily_bar_audits``, etc.) without further conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from bowaka_common.calendar.exchange import USEquityCalendar


def _to_session_date(s: pd.Series) -> pd.Series:
    if s.dtype.kind == "M":
        # Datetime-like.
        if getattr(s.dt, "tz", None) is not None:
            return s.dt.tz_convert("America/New_York").dt.date
        return s.dt.date
    return s


@dataclass
class DailyAuditResult:
    symbol: str
    feed: str
    timeframe: str
    start: str
    end: str
    expected_sessions: int
    observed_sessions: int
    duplicate_sessions: int
    ohlc_violations: int
    zero_volume_sessions: int
    large_gap_flags: int
    passed_research_audit: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        return d


def audit_daily_bars(
    bars: pd.DataFrame,
    *,
    symbol: str,
    feed: str,
    start: date,
    end: date,
    calendar: USEquityCalendar | None = None,
    large_gap_threshold: float = 0.40,
) -> DailyAuditResult:
    """Run a daily-bar quality audit for one symbol."""
    cal = calendar or USEquityCalendar()
    expected_sessions = len(cal.sessions(start, end))

    if bars.empty:
        return DailyAuditResult(
            symbol=symbol,
            feed=feed,
            timeframe="1d",
            start=start.isoformat(),
            end=end.isoformat(),
            expected_sessions=expected_sessions,
            observed_sessions=0,
            duplicate_sessions=0,
            ohlc_violations=0,
            zero_volume_sessions=0,
            large_gap_flags=0,
            passed_research_audit=False,
            warnings=["no_data"],
        )

    df = bars.copy()
    df["session_date"] = _to_session_date(df["timestamp"]) if "session_date" not in df else df["session_date"]
    sessions = df["session_date"]
    duplicate_sessions = int(sessions.duplicated().sum())
    ohlc_violations = int(
        ((df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1))).sum()
    )
    zero_volume_sessions = int((df["volume"] <= 0).sum())

    df_sorted = df.sort_values("session_date")
    prev_close = df_sorted["close"].shift(1)
    gap = df_sorted["open"] / prev_close - 1.0
    large_gap_flags = int((gap.abs() >= large_gap_threshold).fillna(False).sum())

    warnings: list[str] = []
    if duplicate_sessions:
        warnings.append("duplicate_sessions")
    if ohlc_violations:
        warnings.append("ohlc_violations")
    if df.shape[0] < 0.8 * expected_sessions and expected_sessions > 0:
        warnings.append("low_session_coverage")
    if large_gap_flags:
        warnings.append("large_overnight_gap_suspected_split")

    passed = duplicate_sessions == 0 and ohlc_violations == 0
    return DailyAuditResult(
        symbol=symbol,
        feed=feed,
        timeframe="1d",
        start=start.isoformat(),
        end=end.isoformat(),
        expected_sessions=expected_sessions,
        observed_sessions=int(df.shape[0]),
        duplicate_sessions=duplicate_sessions,
        ohlc_violations=ohlc_violations,
        zero_volume_sessions=zero_volume_sessions,
        large_gap_flags=large_gap_flags,
        passed_research_audit=passed,
        warnings=warnings,
    )


@dataclass
class IntradayAuditResult:
    symbol: str
    feed: str
    timeframe: str
    session_date: str
    expected_rth_minutes: int
    observed_minutes: int
    missing_minutes: int
    duplicate_timestamps: int
    ohlc_violations: int
    zero_volume_minutes: int
    longest_intraday_gap_minutes: int
    halt_suspected: bool
    passed_research_audit: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def audit_intraday_bars(
    bars: pd.DataFrame,
    *,
    symbol: str,
    feed: str,
    session_date: date,
    calendar: USEquityCalendar | None = None,
    halt_gap_minutes: int = 10,
) -> IntradayAuditResult:
    """Audit one symbol's minute bars for a single session."""
    cal = calendar or USEquityCalendar()
    expected = cal.rth_minutes(session_date)

    if bars.empty:
        return IntradayAuditResult(
            symbol=symbol,
            feed=feed,
            timeframe="1m",
            session_date=session_date.isoformat(),
            expected_rth_minutes=expected,
            observed_minutes=0,
            missing_minutes=expected,
            duplicate_timestamps=0,
            ohlc_violations=0,
            zero_volume_minutes=0,
            longest_intraday_gap_minutes=expected,
            halt_suspected=expected > halt_gap_minutes,
            passed_research_audit=False,
        )

    df = bars.copy().sort_values("timestamp")
    duplicate_timestamps = int(df["timestamp"].duplicated().sum())
    ohlc_violations = int(
        ((df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1))).sum()
    )
    zero_volume_minutes = int((df["volume"] <= 0).sum())

    ts_diff_minutes = df["timestamp"].diff().dt.total_seconds() / 60.0
    longest_gap = int(ts_diff_minutes.max() or 0)
    missing_minutes = max(0, expected - int(df.shape[0]))
    halt_suspected = longest_gap >= halt_gap_minutes

    passed = duplicate_timestamps == 0 and ohlc_violations == 0
    return IntradayAuditResult(
        symbol=symbol,
        feed=feed,
        timeframe="1m",
        session_date=session_date.isoformat(),
        expected_rth_minutes=expected,
        observed_minutes=int(df.shape[0]),
        missing_minutes=missing_minutes,
        duplicate_timestamps=duplicate_timestamps,
        ohlc_violations=ohlc_violations,
        zero_volume_minutes=zero_volume_minutes,
        longest_intraday_gap_minutes=longest_gap,
        halt_suspected=halt_suspected,
        passed_research_audit=passed,
    )


@dataclass
class QuoteAuditResult:
    symbol: str
    feed: str
    session_date: str
    n_quotes: int
    crossed_quotes: int
    nonpositive_quotes: int
    extreme_spread_quotes: int
    max_spread_pct: float
    median_spread_pct: float
    out_of_order_timestamps: int
    passed_research_audit: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def audit_quotes(
    quotes: pd.DataFrame,
    *,
    symbol: str,
    feed: str,
    session_date: date,
    extreme_spread_pct: float = 0.20,
) -> QuoteAuditResult:
    if quotes.empty:
        return QuoteAuditResult(
            symbol=symbol,
            feed=feed,
            session_date=session_date.isoformat(),
            n_quotes=0,
            crossed_quotes=0,
            nonpositive_quotes=0,
            extreme_spread_quotes=0,
            max_spread_pct=0.0,
            median_spread_pct=0.0,
            out_of_order_timestamps=0,
            passed_research_audit=False,
        )
    df = quotes.copy()
    crossed = int((df["bid_price"] > df["ask_price"]).sum())
    nonpositive = int(((df["bid_price"] <= 0) | (df["ask_price"] <= 0)).sum())
    spread = df["ask_price"] - df["bid_price"]
    mid = (df["ask_price"] + df["bid_price"]) / 2.0
    spread_pct = (spread / mid).where(mid > 0, 0.0)
    extreme = int((spread_pct.abs() > extreme_spread_pct).sum())
    max_spread = float(np.nan_to_num(spread_pct.max())) if len(df) else 0.0
    median_spread = float(np.nan_to_num(spread_pct.median())) if len(df) else 0.0
    ooo = int((df["timestamp"].diff().dt.total_seconds() < 0).sum())

    passed = crossed == 0 and nonpositive == 0 and ooo == 0
    return QuoteAuditResult(
        symbol=symbol,
        feed=feed,
        session_date=session_date.isoformat(),
        n_quotes=int(df.shape[0]),
        crossed_quotes=crossed,
        nonpositive_quotes=nonpositive,
        extreme_spread_quotes=extreme,
        max_spread_pct=max_spread,
        median_spread_pct=median_spread,
        out_of_order_timestamps=ooo,
        passed_research_audit=passed,
    )


def quote_age_at(quotes: pd.DataFrame, *, at: pd.Timestamp) -> float:
    """Return the age (seconds) of the most recent quote at-or-before ``at``."""
    if quotes.empty:
        return float("inf")
    if at.tzinfo is None:
        at = at.tz_localize("UTC")
    eligible = quotes[quotes["timestamp"] <= at]
    if eligible.empty:
        return float("inf")
    last = eligible["timestamp"].max()
    return float((at - last).total_seconds())
