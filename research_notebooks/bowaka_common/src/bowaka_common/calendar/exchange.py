"""US equities session calendar wrapping ``exchange_calendars`` XNYS.

Behavior contracts:

- Friday signal → Monday trade unless Monday is a holiday, then Tuesday.
- Holiday signal dates are skipped from the iterable returned by ``sessions``.
- Early close days are detected via ``is_early_close``; ``rth_minutes`` is shorter.
- DST transitions do not shift ET-clock decisions like 09:45 / 15:45.
- ``add_sessions`` counts trading sessions, positive or negative.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Iterable

import exchange_calendars as xcals
import pandas as pd


@dataclass(frozen=True)
class SessionTimes:
    open_utc: pd.Timestamp
    close_utc: pd.Timestamp
    is_early_close: bool
    rth_minutes: int


class USEquityCalendar:
    """Session-aware US equities calendar wrapper."""

    REGULAR_RTH_MINUTES = 390  # 09:30 to 16:00 ET

    def __init__(self, exchange: str = "XNYS"):
        self.exchange = exchange
        self.cal = xcals.get_calendar(exchange)

    def _ts(self, d: date | str | pd.Timestamp) -> pd.Timestamp:
        if isinstance(d, pd.Timestamp):
            return d.normalize()
        if isinstance(d, str):
            return pd.Timestamp(d).normalize()
        return pd.Timestamp(d)

    def is_session(self, session_date: date | str) -> bool:
        return self.cal.is_session(self._ts(session_date))

    def sessions(self, start: date | str, end: date | str) -> list[date]:
        return [ts.date() for ts in self.cal.sessions_in_range(self._ts(start), self._ts(end))]

    def sessions_between(self, start: date | str, end: date | str) -> list[date]:
        return self.sessions(start, end)

    def next_session(self, session_date: date | str) -> date:
        ts = self._ts(session_date)
        # Search a 14-day window to cover long holiday weekends.
        end = ts + pd.Timedelta(days=14)
        upcoming = self.cal.sessions_in_range(ts + pd.Timedelta(days=1), end)
        if len(upcoming) == 0:
            raise ValueError(f"No next session found after {session_date}")
        return upcoming[0].date()

    def previous_session(self, session_date: date | str) -> date:
        ts = self._ts(session_date)
        start = ts - pd.Timedelta(days=14)
        prior = self.cal.sessions_in_range(start, ts - pd.Timedelta(days=1))
        if len(prior) == 0:
            raise ValueError(f"No previous session found before {session_date}")
        return prior[-1].date()

    def add_sessions(self, session_date: date | str, n: int) -> date:
        out = self._ts(session_date).date()
        if n == 0:
            return out
        if n > 0:
            for _ in range(n):
                out = self.next_session(out)
        else:
            for _ in range(abs(n)):
                out = self.previous_session(out)
        return out

    def session_open(self, session_date: date | str) -> pd.Timestamp:
        return self.cal.session_open(self._ts(session_date))

    def session_close(self, session_date: date | str) -> pd.Timestamp:
        return self.cal.session_close(self._ts(session_date))

    def is_early_close(self, session_date: date | str) -> bool:
        if not self.is_session(session_date):
            return False
        # Early-close sessions in XNYS close before 16:00 ET (i.e. before 20:00 UTC
        # in standard time / 21:00 UTC in DST). We use the calendar's own knowledge
        # of close time relative to a standard 6.5-hour session.
        rth = self.rth_minutes(session_date)
        return rth < self.REGULAR_RTH_MINUTES

    def rth_minutes(self, session_date: date | str) -> int:
        ts = self._ts(session_date)
        open_ts = self.cal.session_open(ts)
        close_ts = self.cal.session_close(ts)
        seconds = (close_ts - open_ts).total_seconds()
        return int(seconds / 60.0)

    def session_times(self, session_date: date | str) -> SessionTimes:
        ts = self._ts(session_date)
        o = self.cal.session_open(ts)
        c = self.cal.session_close(ts)
        rth = int((c - o).total_seconds() / 60.0)
        return SessionTimes(open_utc=o, close_utc=c, is_early_close=rth < self.REGULAR_RTH_MINUTES, rth_minutes=rth)

    def iter_sessions(self, start: date | str, end: date | str) -> Iterable[date]:
        yield from self.sessions(start, end)
