"""ET/UTC conversion helpers.

US equities trade in `America/New_York`. The convention is:

- Daily bars are referenced by their session_date (ET calendar date).
- Intraday bars are timezone-aware UTC; analytics convert to ET.
- Intraday eval times like "15:45" are interpreted in ET.
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def et_to_utc(et_dt: datetime) -> datetime:
    if et_dt.tzinfo is None:
        et_dt = et_dt.replace(tzinfo=NY)
    return et_dt.astimezone(UTC)


def utc_to_et(utc_dt: datetime) -> datetime:
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=UTC)
    return utc_dt.astimezone(NY)


def session_at_et(session_date: date, hhmm: str) -> datetime:
    """Return an ET-aware datetime for ``session_date`` at ``HH:MM`` ET."""
    t = parse_hhmm(hhmm)
    return datetime.combine(session_date, t).replace(tzinfo=NY)


def session_at_utc(session_date: date, hhmm: str) -> datetime:
    return et_to_utc(session_at_et(session_date, hhmm))
