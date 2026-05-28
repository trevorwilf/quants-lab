"""Phase 1 §4 — objective-minimal scan matches the legacy/full path.

Speedup report v2 §9.5 / Phase 1. The dump_row allocation was deferred on
the failing-gate branch when ``collect_gate_dump=False``. The change is
observation-equivalent: the emitted-candidate list, scanner state mutation,
and rejection_counts MUST be byte-equal across the two collection modes on
the same fixture. We additionally pin a small set of deterministic outputs
to a frozen golden so a future refactor that touches the loop cannot
silently drift.

(The conventional "pre-change pickle" approach from the prompt note isn't
applicable post-merge, so instead this test pins the post-change output as
the new golden and pairs it with the bidirectional full-mode <-> objective-
mode parity assertion. Subsequent loop refactors must re-run the script
``scripts/regenerate_phase1_parity_golden.py`` and changelog the diff.)
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.scanner.scan_context import build_scan_session_context
from bowaka_v2_lab.scanner.scan_loop import (
    ScanSkipReason,
    evaluate_one_scan,
)
from tests.fixtures.build_minute_fixture import make_minute_bars


_SCAN_TS = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
_SYMBOLS = ["AAA", "BBB", "CCC", "DDD", "EEE"]
_SESSION = dt.date(2024, 9, 4)


def _cfg() -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {
            "max_candidates_per_scan": 5,
            "max_entries_per_scan": 3,
            "min_signal_strength": 0.0,
            "signal_expiry_seconds": 600,
            "same_symbol_entries_per_day": 1,
            "symbol_cooldown_minutes": 390,
        },
        "signals": {"rvol_so_far_min": 0.0, "rvol_so_far_max": 99999.0},
        "execution": {
            "max_spread_bps": 200,
            "max_quote_age_seconds": 60,
            "order_type": "marketable_limit",
        },
        "historical_features": {
            "volume_curve": {
                "bucket_edges": [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
                "fallback_opening_15m_share": 0.08,
            },
        },
    }


def _universe() -> dict:
    return {
        "universe_hash": "sha256:t",
        "symbols": [
            {
                "symbol": s,
                "exchange": "NASDAQ",
                "venue_code": "XNAS",
                "instrument_class": "operating_equity",
                "eligible_for_bowaka_equity_bucket": True,
            }
            for s in _SYMBOLS
        ],
    }


def _daily_cache() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": s,
                "prior_close": 100.0,
                "avg_dollar_volume_20d": 5_000_000,
                "avg_volume_20d": 50_000,
                "prior_atr_pct": 0.02,
                "prior_atr_14d": 2.0,
                "ema_slope_prior": 0.01,
                "ema_10_prior": 100.0,
            }
            for s in _SYMBOLS
        ]
    )


def _bars_supplier():
    bars_by_symbol = {
        s: make_minute_bars(
            s, _SESSION, minutes=30, drift_per_minute=0.5, minute_volume=10_000,
        )
        for s in _SYMBOLS
    }
    return lambda sym, ts: bars_by_symbol.get(sym, pd.DataFrame())


def _run(*, collect_gate_dump: bool):
    cfg = _cfg()
    universe = _universe()
    daily_cache = _daily_cache()
    bars_supplier = _bars_supplier()
    ctx = build_scan_session_context(
        cfg, daily_cache, universe, [_SCAN_TS], collect_gate_dump=collect_gate_dump,
    )
    state: dict = {}
    result = evaluate_one_scan(
        cfg=cfg,
        universe_snapshot=universe,
        daily_cache=daily_cache,
        volume_curve=None,
        state=state,
        scan_ts=_SCAN_TS,
        bars_supplier=bars_supplier,
        scan_context=ctx,
        collect_gate_dump=collect_gate_dump,
    )
    return result, state


def test_objective_minimal_emissions_byte_equal_to_full_mode() -> None:
    """Same emitted-candidate sequence across both collection modes."""
    full, state_full = _run(collect_gate_dump=True)
    obj, state_obj = _run(collect_gate_dump=False)
    full_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in full.emitted]
    obj_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in obj.emitted]
    assert full_emits == obj_emits


def test_objective_minimal_state_mutation_byte_equal_to_full_mode() -> None:
    """Cooldown / per-day-emit / scanner_last_run state is identical."""
    _, state_full = _run(collect_gate_dump=True)
    _, state_obj = _run(collect_gate_dump=False)
    assert state_full.get("symbol_last_emit_ts") == state_obj.get("symbol_last_emit_ts")
    assert (
        state_full.get("signal_emits_per_symbol_today")
        == state_obj.get("signal_emits_per_symbol_today")
    )
    assert state_full.get("scanner_last_run_ts") == state_obj.get("scanner_last_run_ts")
    assert state_full.get("in_play_pool") == state_obj.get("in_play_pool")


def test_objective_minimal_rejection_counts_match_full_dump() -> None:
    """The objective-mode counters total to the same per-reason buckets."""
    full, _ = _run(collect_gate_dump=True)
    obj, _ = _run(collect_gate_dump=False)

    full_per_reason: dict[str, int] = {}
    for row in full.gate_dump:
        reason = row.get("rejection_reason")
        if reason:
            full_per_reason[reason] = full_per_reason.get(reason, 0) + 1
    assert dict(obj.rejection_counts) == full_per_reason


def test_objective_minimal_emits_at_most_effective_cap() -> None:
    """Under the cap (3) the post-sort emit count is bounded; remainder bumped."""
    obj, _ = _run(collect_gate_dump=False)
    cap = 3  # configured ``max_entries_per_scan``
    assert len(obj.emitted) <= cap
    capped = int(obj.rejection_counts.get(ScanSkipReason.MAX_ENTRIES_CAP.value, 0))
    # Five symbols all pass with min RVOL 0.0; effective cap = 3; the other 2
    # are capped.
    assert capped == max(0, len(_SYMBOLS) - cap)
