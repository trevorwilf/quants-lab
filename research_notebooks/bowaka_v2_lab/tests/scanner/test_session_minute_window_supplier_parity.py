"""Parity between the Phase 4 session-minute-window supplier and the legacy
cached ``forming_minutes`` reader — on the REAL SIP lake.

The two suppliers must produce byte-identical frames for matching inputs (the
Phase 4 swap-in invariant). This also re-validates the P1 (L1) forming-bar cutoff
on real data: both readers apply the ``<= scan_ts - 60s`` rule, so a divergence
would surface here.

ENFORCED real-data lane (P2 / §6): on an ordinary host this SKIPS; in the
ql-jupyter container with ``BOWAKA_REAL_DATA_LANE=1`` +
``MARKET_DATA_ROOT=/opt/market_data_cache`` it RUNS and a missing lake FAILS
(see :mod:`tests._real_data_lane`). Repointed IEX->SIP after the 2026-06-04 cutover.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from tests._real_data_lane import require_real_lake

# Real SIP-lake test inputs (microcaps known-present over the 2025-08 window).
_SESSION = _dt.date(2025, 8, 27)
_CUTOFF_UTC = pd.Timestamp("2025-08-27 15:00:00", tz="UTC")   # 11:00 ET
_SYMBOLS = ("IREN", "RIOT", "CLSK", "SOUN", "AMPX", "RGTI", "ATAI")
_FEED = "sip"
_POLICY = "scanner_start_to_scan"


def _store_and_suppliers(symbols, sessions):
    """Resolve the real lake (lane policy) and build both suppliers against it."""
    from bowaka_common.marketdata import MarketDataStore
    from bowaka_v2_lab.data.cached_suppliers import CachedSessionMarketData
    from bowaka_v2_lab.scanner.session_minute_window_supplier import (
        make_session_minute_window_supplier,
    )

    lake_root = require_real_lake("IREN", feed=_FEED)
    store = MarketDataStore(lake_root)
    cached = CachedSessionMarketData(store, feed=_FEED, intraday_window_policy=_POLICY)
    sym_by_session = {s: tuple(symbols) for s in sessions}
    phase4 = make_session_minute_window_supplier(
        store, list(sessions), sym_by_session,
        feed=_FEED, intraday_policy=_POLICY, max_bar_age_seconds=None,
    )
    return cached, phase4


def test_phase4_supplier_matches_cached_forming_minutes_on_real_lake() -> None:
    """Byte-parity: ``make_session_minute_window_supplier`` must produce the same
    frame ``CachedSessionMarketData.forming_minutes`` does for every
    ``(symbol, cutoff)`` pair on a known-active session."""
    cached, phase4 = _store_and_suppliers(_SYMBOLS, [_SESSION])

    compared = 0
    for symbol in _SYMBOLS:
        ref = cached.forming_minutes(symbol, _CUTOFF_UTC)
        got = phase4(symbol, _CUTOFF_UTC)
        if ref.empty:
            continue  # symbol without a bar at this (session, cutoff) — skip
        assert not got.empty, (
            f"{symbol}: Phase 4 supplier returned 0 rows where cached returned "
            f"{len(ref)} (the swap-in regression)."
        )
        ref_sorted = ref.sort_values("timestamp").reset_index(drop=True)
        got_sorted = got.sort_values("timestamp").reset_index(drop=True)
        pd.testing.assert_frame_equal(
            ref_sorted, got_sorted, check_like=True, check_dtype=False,
        )
        compared += 1
    assert compared > 0, "no non-empty (symbol, cutoff) pair found — symbol list stale?"


_FOLD_SESSIONS_RAW = (
    "2025-08-27", "2025-09-03", "2025-09-10", "2025-09-17", "2025-09-24",
)


def _xnys_trading_days(candidates):
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    return [pd.Timestamp(s).date() for s in candidates if cal.is_session(pd.Timestamp(s))]


_PARAM_SESSIONS = _xnys_trading_days(_FOLD_SESSIONS_RAW)
_CUTOFFS_ET = (
    _dt.time(hour=9, minute=45),   # scanner-start
    _dt.time(hour=12, minute=0),   # mid-day
    _dt.time(hour=15, minute=55),  # late-session
)


def _et_to_utc(session: _dt.date, time_et: _dt.time) -> pd.Timestamp:
    return pd.Timestamp(
        _dt.datetime.combine(session, time_et), tz="America/New_York",
    ).tz_convert("UTC")


@pytest.mark.parametrize("session", _PARAM_SESSIONS)
def test_phase4_supplier_byte_parity_with_cached_over_real_fold(session) -> None:
    """Byte-parity over the fold window: each ``(session, symbol, cutoff)`` triple
    compares the Phase 4 supplier vs cached, sorted by timestamp."""
    cached, phase4 = _store_and_suppliers(_SYMBOLS, [session])

    compared_pairs = 0
    for symbol in _SYMBOLS:
        for cutoff_et in _CUTOFFS_ET:
            cutoff_utc = _et_to_utc(session, cutoff_et)
            ref = cached.forming_minutes(symbol, cutoff_utc)
            if ref.empty:
                continue
            got = phase4(symbol, cutoff_utc)
            ref_sorted = ref.sort_values("timestamp").reset_index(drop=True)
            got_sorted = got.sort_values("timestamp").reset_index(drop=True)
            pd.testing.assert_frame_equal(
                ref_sorted, got_sorted, check_like=True, check_dtype=False,
            )
            compared_pairs += 1
    assert compared_pairs > 0, (
        f"session {session}: no (symbol, cutoff) pair found a non-empty cached "
        f"frame — the symbol list is probably wrong for this date."
    )


def test_phase4_supplier_max_bar_age_tightens_lower_bound() -> None:
    """When ``max_bar_age_seconds`` is set, the first returned timestamp must be no
    earlier than ``max(intraday_window_start, cutoff - max_bar_age_seconds)``."""
    from bowaka_common.marketdata import MarketDataStore
    from bowaka_v2_lab.data.suppliers import intraday_window_start
    from bowaka_v2_lab.scanner.session_minute_window_supplier import (
        make_session_minute_window_supplier,
    )

    lake_root = require_real_lake("IREN", feed=_FEED)
    store = MarketDataStore(lake_root)
    cutoff = _CUTOFF_UTC
    # Real microcaps have sparse minutes, so don't hard-depend on one symbol/minute
    # having data. Find a probe symbol with >= 2 closed bars in the no-max-age
    # window at this cutoff, then size max_age to include its LAST closed bar (so
    # the tightened window is non-empty) yet tighter than the policy window.
    base = make_session_minute_window_supplier(
        store, [_SESSION], {_SESSION: _SYMBOLS},
        feed=_FEED, intraday_policy=_POLICY, max_bar_age_seconds=None,
    )
    sym, full = None, None
    for s in _SYMBOLS:
        fr = base(s, cutoff)
        if len(fr) >= 2:
            sym, full = s, fr
            break
    assert sym is not None, "no probe symbol has >= 2 closed bars at the cutoff (window/date stale)"

    last_ts = full["timestamp"].iloc[-1]
    max_age = int((cutoff - last_ts).total_seconds()) + 120  # covers the last closed bar
    phase4 = make_session_minute_window_supplier(
        store, [_SESSION], {_SESSION: (sym,)},
        feed=_FEED, intraday_policy=_POLICY, max_bar_age_seconds=max_age,
    )
    got = phase4(sym, cutoff)
    assert not got.empty, f"{sym}: max-bar-age window empty despite covering the last bar"
    floor = max(
        intraday_window_start(cutoff, _POLICY),
        cutoff - pd.Timedelta(seconds=max_age),
    )
    assert got["timestamp"].iloc[0] >= floor, "max-bar-age path leaked bars older than the floor"
    # P1 upper cut: the still-forming minute (<= cutoff - 60s) is excluded.
    assert got["timestamp"].iloc[-1] <= cutoff - pd.Timedelta(seconds=60), (
        "max-bar-age path returned the still-forming minute (PIT cut regression)"
    )
    # max_age only tightens the LOWER bound -> a subset of the no-max-age frame.
    assert set(got["timestamp"]) <= set(full["timestamp"])


def test_phase4_supplier_unknown_symbol_returns_empty_frame_with_canonical_columns() -> None:
    """An unknown symbol returns an empty frame whose columns match the cached
    supplier's empty frame (stable swap-in schema)."""
    cached, phase4 = _store_and_suppliers(("IREN",), [_SESSION])
    unknown = "DEFINITELY_NOT_A_REAL_TICKER"
    cached_empty = cached.forming_minutes(unknown, _CUTOFF_UTC)
    phase4_empty = phase4(unknown, _CUTOFF_UTC)
    assert cached_empty.empty and phase4_empty.empty
    assert tuple(phase4_empty.columns) == tuple(cached_empty.columns), (
        f"unknown-symbol columns differ: cached={tuple(cached_empty.columns)} "
        f"phase4={tuple(phase4_empty.columns)}"
    )
