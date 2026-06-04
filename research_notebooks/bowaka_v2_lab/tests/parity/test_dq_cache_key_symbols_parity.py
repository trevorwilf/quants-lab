"""Regression lock — the startup_dq_cache key must agree on its symbol set.

Per-trial speedup: the per-fold ``build_data_quality_report`` (~81% of the
per-trial wall-clock) is supposed to be built ONCE per fold context (its
invariant half) and reused via ``startup_dq_cache``. It was rebuilt on EVERY
fold because the two sides keyed the cache on DIFFERENT symbol sets:

* stamp side (``fold_context._build_one_fold_context``) hashed the per-fold
  ELIGIBLE-symbol union; while
* check side (``backtester._build_dq_report_with_optional_cache``) hashed
  ``{s["symbol"] for u in universe.values() for s in u.get("symbols", [])}`` —
  which is EMPTY for the raw ``{symbol: record}`` PIT universe shape
  (``.get("symbols")`` is absent there) → the empty-string hash, never matching.

The fix routes both sides through
:func:`bowaka_v2_lab.universe.builder.dq_cache_symbol_set` (shape-robust eligible
union). This pins: (a) the helper returns the eligible union for BOTH the raw
and scanner-snapshot shapes, and (b) the old buggy check-side formula really did
collapse to empty on the raw shape — so a regression to it is caught here.
"""
from __future__ import annotations

import hashlib
import types

from bowaka_v2_lab.universe.builder import dq_cache_symbol_set


def _rec(symbol: str, eligible: bool):
    return types.SimpleNamespace(
        symbol=symbol, eligible_for_bowaka_equity_bucket=eligible,
    )


def _raw_universe() -> dict:
    """``{session: {symbol: UniverseRecord}}`` — the PIT shape the fold context
    and ``_run_fold_backtest_objective`` carry into the backtester."""
    return {
        "2024-09-04": {
            "AAA": _rec("AAA", True), "BBB": _rec("BBB", True),
            "ZZZ": _rec("ZZZ", False),  # ineligible — excluded from the union
        },
        "2024-09-05": {
            "AAA": _rec("AAA", True), "CCC": _rec("CCC", True),
        },
    }


def _snapshot_universe() -> dict:
    """``{session: {"symbols": [{symbol, ...}], ...}}`` — the scanner-snapshot
    shape (to_scanner_snapshot), which only ever lists eligible symbols."""
    return {
        "2024-09-04": {"universe_hash": "x", "symbols": [
            {"symbol": "AAA"}, {"symbol": "BBB"}]},
        "2024-09-05": {"universe_hash": "y", "symbols": [
            {"symbol": "AAA"}, {"symbol": "CCC"}]},
    }


def _hash(symbols) -> str:
    return hashlib.sha256(",".join(sorted(symbols)).encode("utf-8")).hexdigest()[:16]


def test_helper_eligible_union_excludes_ineligible() -> None:
    assert dq_cache_symbol_set(_raw_universe()) == ["AAA", "BBB", "CCC"]


def test_helper_agrees_across_raw_and_snapshot_shapes() -> None:
    raw = dq_cache_symbol_set(_raw_universe())
    snap = dq_cache_symbol_set(_snapshot_universe())
    assert raw == snap == ["AAA", "BBB", "CCC"]
    # …and therefore the cache-key symbols_hash agrees between the two sides.
    assert _hash(raw) == _hash(snap)


def test_old_check_side_formula_collapsed_to_empty_on_raw_shape() -> None:
    """The exact bug: the pre-fix check-side extraction is empty on the raw PIT
    universe, so its symbols_hash was the empty-string hash and never matched
    the stamp side's real hash."""
    raw = _raw_universe()
    old_requested = sorted(
        {s["symbol"] for u in raw.values() for s in u.get("symbols", [])}
    )
    assert old_requested == []  # <-- the silent miss
    stamp_hash = _hash(dq_cache_symbol_set(raw))
    old_check_hash = _hash(old_requested)
    assert stamp_hash != old_check_hash  # the cache could NEVER hit
    # The fix makes the check side use the helper → hashes now match.
    assert _hash(dq_cache_symbol_set(raw)) == stamp_hash


def test_empty_universe_hashes_equal_on_both_sides() -> None:
    # Degenerate but consistent: an all-empty universe hashes identically on
    # both sides (no false discrimination), and the per-fold ``sessions`` field
    # in the key still distinguishes folds.
    assert dq_cache_symbol_set({"2024-09-04": {}}) == []
    assert dq_cache_symbol_set({"2024-09-04": {"symbols": []}}) == []
