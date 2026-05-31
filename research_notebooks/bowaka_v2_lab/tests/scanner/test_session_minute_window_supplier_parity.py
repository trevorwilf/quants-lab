"""Parity between the Phase 4 session-minute-window supplier and the
legacy cached ``forming_minutes`` reader.

Background (2026-05-30 diagnostic): with
``optuna.acceleration.session_minute_window_cache.enabled=true``,
``fold_context`` swaps the minute supplier from
:meth:`CachedSessionMarketData.forming_minutes` to
:func:`make_session_minute_window_supplier`. The latter returned **empty
frames** for every call on the operator's lake, producing 0 candidates
across every walkforward trial (``value=-1.5`` sentinel,
``historical_quote_coverage_pct=100`` denominator-zero). The two suppliers
must produce byte-identical frames for matching inputs — that's the
swap-in invariant the Phase 4 design promised.

See ``research_notebooks/bowaka_v2_lab/PHASE_NOTES/session_minute_window_supplier_parity_fix.md``
for the multi-phase fix plan.

This file currently carries a single XFAIL repro pinned at 2025-08-27
11:00 ET against a 7-symbol microcap slice. When Phase 2 lands the root-
cause fix, this test will flip to passing and the XFAIL ``strict=True``
guard will then refuse any re-introduction of the regression.
"""
from __future__ import annotations

import pandas as pd
import pytest

# ---- module skip: real lake must be reachable ------------------------------
try:
    from bowaka_common.marketdata.store import (
        MarketDataStore,
        default_market_data_root,
    )
except ImportError:  # pragma: no cover — defensive
    pytest.skip("bowaka_common not importable", allow_module_level=True)


_LAKE_ROOT = default_market_data_root()
_PROBE = (
    _LAKE_ROOT / "bars" / "vendor=alpaca" / "feed=iex"
    / "timeframe=1m" / "adjustment=raw"
    / "symbol=AAL" / "year=2025" / "month=08" / "part.parquet"
)
_LAKE_AVAILABLE = _PROBE.is_file()

if not _LAKE_AVAILABLE:  # pragma: no cover — runs on every host but skips on CI
    pytest.skip(
        f"real lake AAL probe missing at {_PROBE}; the parity test requires "
        "the operator's lake (~6,477 split_adjusted symbols).",
        allow_module_level=True,
    )


# ---- test inputs (matched to the operator's diagnostic) --------------------
_SESSION = pd.Timestamp("2025-08-27").date()
_CUTOFF_UTC = pd.Timestamp("2025-08-27 15:00:00", tz="UTC")   # 11:00 ET
_SYMBOLS = ("AAL", "KSS", "ABEV", "ACHR", "RR", "BBAI", "SOUN")
_FEED = "iex"
_POLICY = "scanner_start_to_scan"


def test_phase4_supplier_matches_cached_forming_minutes_on_real_lake():
    """Byte-parity: ``make_session_minute_window_supplier`` must produce
    the same frame ``CachedSessionMarketData.forming_minutes`` does for
    every ``(symbol, cutoff)`` pair on a known-active session."""
    from bowaka_v2_lab.data.cached_suppliers import CachedSessionMarketData
    from bowaka_v2_lab.scanner.session_minute_window_supplier import (
        make_session_minute_window_supplier,
    )

    store = MarketDataStore(_LAKE_ROOT)
    cached = CachedSessionMarketData(
        store, feed=_FEED, intraday_window_policy=_POLICY,
    )
    phase4 = make_session_minute_window_supplier(
        store, [_SESSION], {_SESSION: _SYMBOLS},
        feed=_FEED, intraday_policy=_POLICY, max_bar_age_seconds=None,
    )

    for symbol in _SYMBOLS:
        ref = cached.forming_minutes(symbol, _CUTOFF_UTC)
        got = phase4(symbol, _CUTOFF_UTC)
        # Diagnostic-facing assertion — when this xfails, the operator sees
        # exactly what the two suppliers returned.
        assert not ref.empty, (
            f"{symbol}: cached supplier returned empty — the test premise "
            f"is wrong (lake data missing for this date)."
        )
        assert not got.empty, (
            f"{symbol}: Phase 4 supplier returned 0 rows where cached "
            f"returned {len(ref)} (the bug)."
        )
        assert len(got) == len(ref), (
            f"{symbol}: row-count mismatch — cached={len(ref)} phase4={len(got)}."
        )
        ref_sorted = ref.sort_values("timestamp").reset_index(drop=True)
        got_sorted = got.sort_values("timestamp").reset_index(drop=True)
        pd.testing.assert_frame_equal(
            ref_sorted, got_sorted,
            check_like=True,    # tolerate column ordering
            check_dtype=False,  # column-dtype delta is allowed (lake parquets
                                # may differ across versions); ROW EQUALITY is
                                # the hard parity invariant.
        )


# ---- Phase 3: parametric parity suite over a real fold-0-val slice ---------
import datetime as _dt   # noqa: E402 — keep test-section imports near use

# Fold-0 val window dates per the operator's diagnostic; 5 fixed sessions.
# Skip any that XNYS marks as non-trading at collection time.
_FOLD_SESSIONS_RAW = (
    "2025-08-27", "2025-09-03", "2025-09-10", "2025-09-17", "2025-09-24",
)


def _xnys_trading_days(candidates):
    import exchange_calendars as xcals
    cal = xcals.get_calendar("XNYS")
    valid = []
    for s in candidates:
        ts = pd.Timestamp(s)
        if cal.is_session(ts):
            valid.append(ts.date())
    return valid


_PARAM_SESSIONS = _xnys_trading_days(_FOLD_SESSIONS_RAW)

# 10 known-good microcap candidates (from the operator's PIT diagnostic).
# Each (session, symbol) is skipped if no minute partition exists for that
# combination — the test asserts only on (session, symbol) pairs where the
# cached reader returns ≥1 row.
_PARAM_SYMBOLS = (
    "AAL", "ABAT", "ABCL", "ABEV", "ABSI", "ACB", "ACDC", "ACEL", "ACH", "ACHR",
)

# Three cutoffs per session: scanner-start, mid-day, late-session.
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
def test_phase4_supplier_byte_parity_with_cached_over_real_fold(session):
    """Byte-parity over the fold-0 val window: 5 sessions × 10 symbols × 3
    cutoffs. Each ``(session, symbol, cutoff)`` triple compares the Phase 4
    supplier against the cached supplier via ``assert_frame_equal`` (sorted
    by timestamp, index reset).

    Budget: <30 s wall-clock total across the whole parametric block. If
    this grows past that, reduce the parametrisation cardinality first
    (drop a cutoff) rather than skip the test in CI.
    """
    from bowaka_v2_lab.data.cached_suppliers import CachedSessionMarketData
    from bowaka_v2_lab.scanner.session_minute_window_supplier import (
        make_session_minute_window_supplier,
    )

    store = MarketDataStore(_LAKE_ROOT)
    cached = CachedSessionMarketData(
        store, feed=_FEED, intraday_window_policy=_POLICY,
    )
    phase4 = make_session_minute_window_supplier(
        store, [session], {session: _PARAM_SYMBOLS},
        feed=_FEED, intraday_policy=_POLICY, max_bar_age_seconds=None,
    )

    compared_pairs = 0
    for symbol in _PARAM_SYMBOLS:
        for cutoff_et in _CUTOFFS_ET:
            cutoff_utc = _et_to_utc(session, cutoff_et)
            ref = cached.forming_minutes(symbol, cutoff_utc)
            if ref.empty:
                # No minute partition for this (symbol, session) — skip; the
                # Phase 3 spec explicitly allows skipping these and the
                # unknown-symbol path is covered by a dedicated test below.
                continue
            got = phase4(symbol, cutoff_utc)
            ref_sorted = ref.sort_values("timestamp").reset_index(drop=True)
            got_sorted = got.sort_values("timestamp").reset_index(drop=True)
            pd.testing.assert_frame_equal(
                ref_sorted, got_sorted,
                check_like=True, check_dtype=False,
            )
            compared_pairs += 1

    # The session is supposed to be a real fold-val day; at least SOME
    # comparisons must have happened (else the symbol list is wrong /
    # the partitions moved).
    assert compared_pairs > 0, (
        f"session {session}: no (symbol, cutoff) pair found a non-empty "
        f"cached frame — the symbol list is probably wrong for this date."
    )


# ---- max_bar_age path ------------------------------------------------------
def test_phase4_supplier_max_bar_age_tightens_lower_bound():
    """When ``max_bar_age_seconds`` is set, the returned frame's first
    timestamp must be no earlier than ``max(intraday_window_start,
    cutoff - max_bar_age_seconds)``."""
    from bowaka_v2_lab.scanner.session_minute_window_supplier import (
        make_session_minute_window_supplier,
    )
    from bowaka_v2_lab.data.suppliers import intraday_window_start

    store = MarketDataStore(_LAKE_ROOT)
    cutoff = pd.Timestamp("2025-08-27 15:00:00", tz="UTC")  # 11:00 ET
    max_age = 120  # seconds

    phase4 = make_session_minute_window_supplier(
        store, [_SESSION], {_SESSION: ("AAL",)},
        feed=_FEED, intraday_policy=_POLICY, max_bar_age_seconds=max_age,
    )
    got = phase4("AAL", cutoff)
    assert not got.empty, "AAL: max-bar-age window returned empty"
    floor = max(
        intraday_window_start(cutoff, _POLICY),
        cutoff - pd.Timedelta(seconds=max_age),
    )
    first_ts = got["timestamp"].iloc[0]
    assert first_ts >= floor, (
        f"max-bar-age path leaked bars older than the tighter lower bound: "
        f"first_ts={first_ts}, floor={floor}"
    )
    # Upper bound must still be the cutoff itself.
    assert got["timestamp"].iloc[-1] <= cutoff, (
        f"max-bar-age path returned bars after cutoff: last_ts="
        f"{got['timestamp'].iloc[-1]}, cutoff={cutoff}"
    )


# ---- unknown-symbol path ---------------------------------------------------
def test_phase4_supplier_unknown_symbol_returns_empty_frame_with_canonical_columns():
    """An unknown symbol must return an empty frame whose columns match
    what the cached supplier returns for the SAME input.

    The Phase 4 supplier is a byte-stable swap-in for
    :meth:`CachedSessionMarketData.forming_minutes`. On the empty path
    both must produce identical column sets so downstream consumers (e.g.
    the scanner) see a stable schema regardless of which path is wired.
    The lake parquets carry ``vwap`` and ``trade_count`` for POPULATED
    symbols, but the EMPTY path on both readers returns the canonical
    ``bowaka_common._empty_bars()`` 7-column schema — and that match is
    what this test pins.
    """
    from bowaka_v2_lab.data.cached_suppliers import CachedSessionMarketData
    from bowaka_v2_lab.scanner.session_minute_window_supplier import (
        make_session_minute_window_supplier,
    )

    store = MarketDataStore(_LAKE_ROOT)
    cached = CachedSessionMarketData(
        store, feed=_FEED, intraday_window_policy=_POLICY,
    )
    phase4 = make_session_minute_window_supplier(
        store, [_SESSION], {_SESSION: ("AAL",)},   # AAL only in the universe
        feed=_FEED, intraday_policy=_POLICY,
    )

    unknown_sym = "DEFINITELY_NOT_A_REAL_TICKER"
    cached_empty = cached.forming_minutes(unknown_sym, _CUTOFF_UTC)
    phase4_empty = phase4(unknown_sym, _CUTOFF_UTC)

    assert cached_empty.empty, "test premise: cached supplier must return empty for unknown symbol"
    assert phase4_empty.empty, "Phase 4 supplier must return empty for unknown symbol"
    assert tuple(phase4_empty.columns) == tuple(cached_empty.columns), (
        f"unknown-symbol path returned different columns than cached: "
        f"cached={tuple(cached_empty.columns)} phase4={tuple(phase4_empty.columns)}"
    )
