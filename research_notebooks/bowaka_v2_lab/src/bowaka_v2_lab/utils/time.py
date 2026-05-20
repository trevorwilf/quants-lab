"""Time helpers for bowaka_v2_lab.

Per [Report §8.5]: silent localisation of naive timestamps is forbidden — it
masks data-quality bugs (e.g. v2 source ``_et_minute_of_day`` would treat a
naive ts as UTC and yield a wrong ET minute). The canonical contract is:

- All ingress points must produce ``Timestamp``s with ``tzinfo`` set.
- ``require_aware_timestamp()`` raises ``ValueError`` on any naive input.
- ``to_et()`` / ``to_utc()`` are conversion-only; they never localise.

When ``assume_naive_timezone=True`` is set in config, callers may convert
explicitly via ``localise_assuming(tz)``, which logs an audit record.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import pandas as pd

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def is_aware(ts: Any) -> bool:
    if isinstance(ts, pd.Timestamp):
        return ts.tzinfo is not None
    if isinstance(ts, _dt.datetime):
        return ts.tzinfo is not None and ts.tzinfo.utcoffset(ts) is not None
    return False


def require_aware_timestamp(ts: Any, *, label: str = "timestamp") -> pd.Timestamp:
    """Return a Pandas ``Timestamp`` if ``ts`` is timezone-aware, else raise.

    Accepts ``pd.Timestamp``, ``datetime.datetime``, or anything ``pd.Timestamp``
    can parse. Naive values raise ``ValueError``.
    """
    if ts is None:
        raise ValueError(f"{label}: timestamp is None")
    pts = pd.Timestamp(ts)
    if pts.tzinfo is None:
        raise ValueError(
            f"{label}: naive timestamp {ts!r} rejected; "
            "v2 callers must supply tz-aware timestamps "
            "(set market_data.assume_naive_timezone=true in config to opt out, with explicit localise_assuming(...))"
        )
    return pts


def to_et(ts: Any) -> pd.Timestamp:
    pts = require_aware_timestamp(ts, label="to_et")
    return pts.tz_convert(ET)


def to_utc(ts: Any) -> pd.Timestamp:
    pts = require_aware_timestamp(ts, label="to_utc")
    return pts.tz_convert(UTC)


def localise_assuming(ts: Any, tz: str | ZoneInfo) -> pd.Timestamp:
    """Explicit-opt-in naive-to-aware conversion.

    Only call this when ``market_data.assume_naive_timezone=True`` AND the caller
    is logging the audit reason. Never call from feature / event-builder code.
    """
    if isinstance(tz, str):
        tz = ZoneInfo(tz)
    pts = pd.Timestamp(ts)
    if pts.tzinfo is not None:
        return pts
    return pts.tz_localize(tz)
