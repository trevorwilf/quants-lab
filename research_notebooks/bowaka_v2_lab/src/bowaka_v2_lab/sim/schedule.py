"""Intraday scan schedule — calendar-aware scan-timestamp generation.

Realism Phase 4 (audit P0-003, P0-006). The pre-Phase-4 backtester ran exactly
one scan per session at a hard-coded ``14:00 UTC``; this module produces the
**real** intraday cadence the live scanner runs.

:func:`scan_times_for_session` returns the list of UTC scan timestamps for a
single session:

- ``exchange_calendars.get_calendar(session.calendar)`` confirms the date is a
  trading session — holidays and weekends return ``[]``.
- The scan window runs ``[scanner_start, scanner_start+interval, ..., end]`` in
  the configured local timezone (``session.timezone``), where
  ``end = min(scanner_end, early_close)``.
- DST is handled automatically: each local timestamp is constructed tz-aware in
  ``session.timezone`` then converted to UTC, so a spring-forward / fall-back
  session yields the correct UTC offsets.

**Early closes.** The live scanner (``reference/source_strategy/scripts/
bowaka_intraday_scanner.py`` ``_run_live``, lines 671-725) builds ``session_end``
purely from the configured ``scanner_end`` and does **not** consult the exchange
calendar — on an early-close day it would keep scanning past the real market
close. This module deliberately **deviates** from that live behaviour: it
truncates the scan window to the exchange's early close so a backtest never
emits a scan after the market is shut. The deviation is documented in
``docs/current_code_vs_intended_realism.md``.
"""
from __future__ import annotations

import datetime as _dt
from functools import lru_cache
from typing import Any

import pandas as pd

__all__ = ["scan_times_for_session", "expected_scan_count"]


@lru_cache(maxsize=8)
def _calendar(name: str):
    """Cached ``exchange_calendars`` calendar (construction is expensive)."""
    import exchange_calendars as xcals

    return xcals.get_calendar(name)


def _as_date(value: Any) -> _dt.date:
    """Coerce a date-ish value (date / datetime / str / Timestamp) to ``date``."""
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def _parse_hhmm(value: Any, *, default: str) -> _dt.time:
    """Parse a ``"HH:MM"`` / ``"HH:MM:SS"`` local clock time."""
    text = str(value) if value is not None else default
    parts = text.strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(parts[2]) if len(parts) > 2 else 0
    return _dt.time(hour=hour, minute=minute, second=second)


def _session_cfg(cfg: Any) -> Any:
    """Return the ``session`` block, accepting either a Pydantic config or a dict.

    ``cfg`` may be the validated :class:`BowakaV2Config` (``cfg.session`` is a
    :class:`SessionConfig`) or a raw ``dict`` (``cfg["session"]``). A small
    accessor wrapper normalises both to attribute access.
    """
    session = getattr(cfg, "session", None)
    if session is None and isinstance(cfg, dict):
        session = cfg.get("session") or {}
    if session is None:
        session = {}

    class _Accessor:
        __slots__ = ("_obj",)

        def __init__(self, obj: Any) -> None:
            self._obj = obj

        def get(self, key: str, default: Any = None) -> Any:
            if isinstance(self._obj, dict):
                return self._obj.get(key, default)
            return getattr(self._obj, key, default)

    return _Accessor(session)


def scan_times_for_session(session_date: Any, cfg: Any) -> list[pd.Timestamp]:
    """UTC scan timestamps for ``session_date`` given the run config.

    Parameters
    ----------
    session_date:
        The session calendar date (``date`` / ``datetime`` / ``str`` / Timestamp).
    cfg:
        The run config — either a validated :class:`BowakaV2Config` or a raw
        ``dict``. Only the ``session`` block is consulted.

    Returns
    -------
    list[pandas.Timestamp]
        ``[start, start+interval, ..., end]`` as tz-aware UTC timestamps, where
        ``start = scanner_start`` and ``end = min(scanner_end, early_close)`` in
        the configured local timezone. **Empty** when ``session_date`` is not a
        trading session (weekend / holiday).

    Notes
    -----
    The list is inclusive of both endpoints: a 09:45→15:30 window at a 60s
    interval yields ``(15:30-09:45)/60 + 1 = 346`` timestamps.
    """
    session = _session_cfg(cfg)
    calendar_name = str(session.get("calendar", "XNYS") or "XNYS")
    local_tz = str(session.get("timezone", "America/New_York") or "America/New_York")
    interval_seconds = int(session.get("scan_interval_seconds", 60) or 60)
    if interval_seconds < 1:
        raise ValueError(
            f"scan_times_for_session: scan_interval_seconds must be >= 1, got {interval_seconds}"
        )

    date = _as_date(session_date)
    cal = _calendar(calendar_name)
    cal_ts = pd.Timestamp(date)
    # Holiday / weekend → no scans this session.
    if not cal.is_session(cal_ts):
        return []

    scanner_start = _parse_hhmm(session.get("scanner_start", "09:45"), default="09:45")
    scanner_end = _parse_hhmm(session.get("scanner_end", "15:30"), default="15:30")

    # Window start/end as tz-aware local timestamps; tz_convert handles DST.
    start_local = pd.Timestamp(
        _dt.datetime.combine(date, scanner_start), tz=local_tz
    )
    end_local = pd.Timestamp(
        _dt.datetime.combine(date, scanner_end), tz=local_tz
    )

    # Honour early closes: the exchange calendar's session close (UTC) is
    # converted to local time and used to cap scanner_end. On a normal day the
    # calendar close (16:00 ET) is well past scanner_end (15:30 ET) so this is a
    # no-op; on an early-close day (e.g. 13:00 ET) it truncates the window.
    early_close_local = pd.Timestamp(cal.session_close(cal_ts)).tz_convert(local_tz)
    if early_close_local < end_local:
        end_local = early_close_local

    start_utc = start_local.tz_convert("UTC")
    end_utc = end_local.tz_convert("UTC")
    if end_utc < start_utc:
        # scanner_end before scanner_start (or an early close before the scan
        # window opens) — no scans.
        return []

    step = pd.Timedelta(seconds=interval_seconds)
    times: list[pd.Timestamp] = []
    ts = start_utc
    while ts <= end_utc:
        times.append(ts)
        ts = ts + step
    return times


def expected_scan_count(session_date: Any, cfg: Any) -> int:
    """Number of scan timestamps :func:`scan_times_for_session` produces.

    Convenience wrapper used by the scan-count summary in the run manifest.
    """
    return len(scan_times_for_session(session_date, cfg))
