"""P1 (PIT look-ahead, L1) regression — the forming-bar cutoff must EXCLUDE the
still-forming minute.

Lake minute bars are START-stamped (the bar stamped at ``scan_ts`` covers
``[scan_ts, scan_ts+60s)``), so admitting it leaks up to a full minute of FUTURE
price into the scan decision. Round-2 reproduced a +48.5% ``last_price`` delta
from this. The fix cuts the forming-bar window at ``scan_ts - 60s`` (one bar
interval) so only fully-CLOSED bars are visible.

This pins the corrected behavior (look-ahead delta = 0) on the session-minute
cache path. The supplier, matrix-pandas, and numba-kernel readers are held
byte-identical to this path by the existing differential parity tests
(``tests/parity/test_scan_matrix_*``, ``tests/scanner/test_session_minute_*``,
``tests/integration/test_numba_scan_matrix_build_parity``), so a regression in
any one of them surfaces there.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.features.forming_bar import aggregate_forming_session_bar
from bowaka_v2_lab.scanner.session_minute_window_cache import SessionMinuteWindowCache

_SESSION = dt.date(2025, 8, 20)
_MINUTE_COLS = ["timestamp", "open", "high", "low", "close", "volume"]


def _et_to_utc(hh: int, mm: int) -> pd.Timestamp:
    return pd.Timestamp(
        dt.datetime.combine(_SESSION, dt.time(hh, mm)), tz="America/New_York"
    ).tz_convert("UTC")


def _make_cache(symbol: str, frame: pd.DataFrame, policy: str) -> SessionMinuteWindowCache:
    """Build the cache's internal representation directly (mirrors ``__init__``),
    so ``bars_until``'s cutoff is exercised without a lake. ``_timestamps`` is the
    tz-naive int64-ns view ``__init__`` produces."""
    cache = SessionMinuteWindowCache.__new__(SessionMinuteWindowCache)
    cache.session = _SESSION
    cache.feed = "sip"
    cache.intraday_policy = policy
    cache.max_bar_age_seconds = None
    f = frame.sort_values("timestamp").reset_index(drop=True)
    ts = pd.to_datetime(f["timestamp"], utc=True)
    cache._frames = {symbol: f}
    cache._timestamps = {
        symbol: ts.dt.tz_convert("UTC").dt.tz_localize(None)
        .to_numpy("datetime64[ns]").view("int64")
    }
    return cache


def _spike_session() -> pd.DataFrame:
    """09:45..09:59 ET flat at 100; the 10:00 ET bar is a +50% spike (high 999)."""
    rows = []
    for mm in range(45, 60):  # 09:45..09:59 inclusive = 15 closed bars
        rows.append((_et_to_utc(9, mm), 100.0, 101.0, 99.0, 100.0, 10.0))
    rows.append((_et_to_utc(10, 0), 150.0, 999.0, 150.0, 888.0, 99.0))  # forming
    return pd.DataFrame(rows, columns=_MINUTE_COLS)


def test_cache_excludes_still_forming_minute() -> None:
    cache = _make_cache("AAA", _spike_session(), "scanner_start_to_scan")

    bars = cache.bars_until("AAA", _et_to_utc(10, 0))
    # The 10:00 (still-forming) bar must be EXCLUDED: last visible bar = 09:59.
    assert len(bars) == 15  # 09:45..09:59 closed bars
    assert bars["timestamp"].max() == _et_to_utc(9, 59)

    sess = aggregate_forming_session_bar(bars)
    # Look-ahead delta = 0: the forming-minute spike does NOT enter the decision.
    assert sess["last_price"] == 100.0  # NOT 888.0 (the forming-bar close)
    assert sess["session_high"] == 101.0  # NOT 999.0 (the forming-bar high)


def test_cache_includes_minute_once_closed() -> None:
    cache = _make_cache("AAA", _spike_session(), "scanner_start_to_scan")

    # One minute later the 10:00 bar has fully closed -> it IS now visible.
    bars = cache.bars_until("AAA", _et_to_utc(10, 1))
    assert bars["timestamp"].max() == _et_to_utc(10, 0)
    sess = aggregate_forming_session_bar(bars)
    assert sess["session_high"] == 999.0  # the now-closed bar contributes


def test_first_scan_sees_no_unclosed_bar() -> None:
    """At the very first scan (policy window start), no in-window bar has closed
    yet, so the forming-bar window is empty rather than peeking at the open bar."""
    cache = _make_cache("AAA", _spike_session(), "scanner_start_to_scan")
    bars = cache.bars_until("AAA", _et_to_utc(9, 45))
    assert len(bars) == 0
