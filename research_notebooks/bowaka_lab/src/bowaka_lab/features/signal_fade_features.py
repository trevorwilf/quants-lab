"""Per-position intraday context assembler for signal-fade scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.features.intraday_features import (
    session_extrema,
    short_ema_distance,
    vwap,
)
from bowaka_lab.features.opening_range import opening_range, session_open_price


@dataclass
class IntradayContext:
    current_price: float
    prior_close: float | None
    session_open: float | None
    vwap_now: float | None
    opening_range_high: float | None
    opening_range_low: float | None
    running_high: float
    running_low: float
    short_ema_distance: float
    spread_pct: float | None
    quote_age_seconds: float | None
    minutes_since_entry: int
    rvol_now: float | None
    morning_continuation_volume: float | None
    last_30m_volume: float | None
    made_higher_high_since_entry: bool


def assemble_intraday_context(
    *,
    bars_through_now: pd.DataFrame,
    entry_price: float,
    entry_time: pd.Timestamp,
    now_ts: pd.Timestamp,
    prior_close: float | None,
    session_date: date,
    quote: dict | None = None,
    calendar: USEquityCalendar | None = None,
) -> IntradayContext:
    if bars_through_now.empty:
        return IntradayContext(
            current_price=entry_price,
            prior_close=prior_close,
            session_open=None,
            vwap_now=None,
            opening_range_high=None,
            opening_range_low=None,
            running_high=entry_price,
            running_low=entry_price,
            short_ema_distance=0.0,
            spread_pct=None,
            quote_age_seconds=None,
            minutes_since_entry=0,
            rvol_now=None,
            morning_continuation_volume=None,
            last_30m_volume=None,
            made_higher_high_since_entry=False,
        )
    cal = calendar or USEquityCalendar()
    df = bars_through_now.sort_values("timestamp").copy()
    sym = df["symbol"].iloc[0] if "symbol" in df.columns else "X"
    if "symbol" not in df.columns:
        df["symbol"] = sym

    df["vwap"] = vwap(df)
    extrema = session_extrema(df)
    df["running_high"] = extrema["running_high"]
    df["running_low"] = extrema["running_low"]
    df["ema_dist"] = short_ema_distance(df)

    last = df.iloc[-1]
    or_range = opening_range(df, session_date=session_date, calendar=cal)
    session_open = session_open_price(df, session_date=session_date, calendar=cal)

    post_entry = df[df["timestamp"] >= entry_time]
    morning = df[df["timestamp"] < entry_time + pd.Timedelta(minutes=30)]
    last_30m = df.iloc[-30:]
    morning_vol = float(morning["volume"].sum()) if not morning.empty else None
    last_30m_vol = float(last_30m["volume"].sum()) if not last_30m.empty else None
    high_post = float(post_entry["high"].max()) if not post_entry.empty else float(last["high"])
    made_higher_high = high_post > float(post_entry["high"].iloc[0]) if not post_entry.empty else False

    if quote is not None:
        spread_pct = float(quote.get("spread_pct", 0.0))
        quote_age = float(quote.get("quote_age_seconds", 0.0))
    else:
        spread_pct = None
        quote_age = None

    minutes_since_entry = int(max(0, (now_ts - entry_time).total_seconds() / 60.0))

    return IntradayContext(
        current_price=float(last["close"]),
        prior_close=prior_close,
        session_open=session_open,
        vwap_now=float(last["vwap"]) if not pd.isna(last["vwap"]) else None,
        opening_range_high=or_range["high"] if not pd.isna(or_range["high"]) else None,
        opening_range_low=or_range["low"] if not pd.isna(or_range["low"]) else None,
        running_high=float(last["running_high"]),
        running_low=float(last["running_low"]),
        short_ema_distance=float(last["ema_dist"]) if not pd.isna(last["ema_dist"]) else 0.0,
        spread_pct=spread_pct,
        quote_age_seconds=quote_age,
        minutes_since_entry=minutes_since_entry,
        rvol_now=None,
        morning_continuation_volume=morning_vol,
        last_30m_volume=last_30m_vol,
        made_higher_high_since_entry=made_higher_high,
    )
