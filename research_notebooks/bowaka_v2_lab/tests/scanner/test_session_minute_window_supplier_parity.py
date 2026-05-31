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


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Phase 4 supplier returns empty bars / column mismatch — root cause "
        "pending Phase 2; see PHASE_NOTES/session_minute_window_supplier_parity_fix.md"
    ),
)
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
            check_dtype=False,  # column-dtype delta (Phase 2 reconciles)
        )
