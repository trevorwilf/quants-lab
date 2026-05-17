"""Opening-range computation for entry rules and signal-fade context."""

from __future__ import annotations

from datetime import date, time
from typing import Literal

import pandas as pd

from bowaka_lab.data.calendar import USEquityCalendar


def opening_range(
    bars: pd.DataFrame,
    *,
    session_date: date,
    minutes: int = 15,
    calendar: USEquityCalendar | None = None,
) -> dict[str, float]:
    """Compute opening-range high/low over ``minutes`` from the session open.

    Respects early-close days — if the session is shorter than ``minutes``,
    the range is truncated to the available bars.
    """
    if bars.empty:
        return {"high": float("nan"), "low": float("nan"), "minutes_used": 0}
    cal = calendar or USEquityCalendar()
    open_ts = cal.session_open(session_date)
    close_ts = cal.session_close(session_date)
    end_ts = min(open_ts + pd.Timedelta(minutes=minutes), close_ts)
    df = bars[(bars["timestamp"] >= open_ts) & (bars["timestamp"] < end_ts)]
    if df.empty:
        return {"high": float("nan"), "low": float("nan"), "minutes_used": 0}
    return {
        "high": float(df["high"].max()),
        "low": float(df["low"].min()),
        "minutes_used": int(df.shape[0]),
    }


def session_open_price(bars: pd.DataFrame, *, session_date: date, calendar: USEquityCalendar | None = None) -> float | None:
    """First bar's open price for the session."""
    cal = calendar or USEquityCalendar()
    open_ts = cal.session_open(session_date)
    df = bars[bars["timestamp"] >= open_ts].sort_values("timestamp")
    if df.empty:
        return None
    return float(df.iloc[0]["open"])
