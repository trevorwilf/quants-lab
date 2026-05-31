"""Session minute-window supplier adapter (speedup report v2 §4 P3 / §5.7).

Wraps a per-session :class:`SessionMinuteWindowCache` so the fold context
can expose the same ``minute_bars_supplier(symbol, scan_ts)`` callable
the legacy supplier produces. The adapter lazily builds one cache per
session on first scan into that session.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Callable, Mapping, Optional, Sequence

import pandas as pd

from bowaka_common.marketdata import MarketDataStore

from ..data.suppliers import _DEFAULT_INTRADAY_WINDOW_POLICY
from .session_minute_window_cache import SessionMinuteWindowCache, _empty_minute_frame


def make_session_minute_window_supplier(
    store: MarketDataStore | Any,
    sessions: Sequence[_dt.date],
    symbols_by_session: Mapping[_dt.date, Sequence[str]],
    *,
    feed: str = "iex",
    intraday_policy: str = _DEFAULT_INTRADAY_WINDOW_POLICY,
    max_bar_age_seconds: Optional[float] = None,
) -> Callable[[str, Any], pd.DataFrame]:
    """Return a ``bars_supplier(symbol, scan_ts) -> pd.DataFrame`` closure.

    The closure routes each call to the appropriate session's
    :class:`SessionMinuteWindowCache` based on ``scan_ts.tz_convert("America/
    New_York").date()``. The cache for a session is built lazily on first
    scan into that session — so a session that never has any candidate
    inspections pays zero cost.

    On a session-cache miss for the resolved session (symbol absent from
    ``symbols_by_session[session]``), the supplier returns the canonical
    empty minute frame — same as the legacy supplier.

    Parity with :meth:`bowaka_v2_lab.data.cached_suppliers.CachedSessionMarketData.forming_minutes`
    is enforced by ``tests/scanner/test_session_minute_window_supplier_parity.py``
    — do not modify either implementation's boundary semantics or the
    canonical empty-frame schema without updating that test.
    """
    cache_by_session: dict[_dt.date, SessionMinuteWindowCache] = {}
    sessions_set = {pd.Timestamp(s).date() if not isinstance(s, _dt.date) else s
                    for s in sessions}

    def _resolve_session(scan_ts: Any) -> Optional[_dt.date]:
        ts = pd.Timestamp(scan_ts)
        ts_utc = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        return ts_utc.tz_convert("America/New_York").date()

    def bars_supplier(symbol: str, scan_ts: Any) -> pd.DataFrame:
        session = _resolve_session(scan_ts)
        if session is None or session not in sessions_set:
            return _empty_minute_frame()
        cache = cache_by_session.get(session)
        if cache is None:
            cache = SessionMinuteWindowCache(
                store, session, symbols_by_session.get(session, ()),
                feed=feed, intraday_policy=intraday_policy,
                max_bar_age_seconds=max_bar_age_seconds,
            )
            cache_by_session[session] = cache
        return cache.bars_until(symbol, scan_ts)

    return bars_supplier


__all__ = ["make_session_minute_window_supplier"]
