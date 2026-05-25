"""Objective-mode scan (collect_gate_dump=False) emits the same candidates.

Speedup report §5.4 / §11.2 Phase 4. With ``collect_gate_dump=False`` the
per-symbol gate-dump rows are replaced with bounded ``rejection_counts``
counters; emitted candidates and scanner-state updates must still match
the full-mode path exactly.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from bowaka_v2_lab.scanner.scan_context import build_scan_session_context
from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from tests.fixtures.build_minute_fixture import make_minute_bars


def _cfg() -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600,
                    "same_symbol_entries_per_day": 1,
                    "symbol_cooldown_minutes": 390},
        "signals": {},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                       "order_type": "marketable_limit"},
        "historical_features": {
            "volume_curve": {
                "bucket_edges": [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
                "fallback_opening_15m_share": 0.08,
            },
        },
    }


def _universe(symbols: list[str]) -> dict:
    return {
        "universe_hash": "sha256:t",
        "symbols": [
            {"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
             "instrument_class": "operating_equity",
             "eligible_for_bowaka_equity_bucket": True}
            for s in symbols
        ],
    }


def _daily_cache(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame([
        {"symbol": s, "prior_close": 100.0,
         "avg_dollar_volume_20d": 5_000_000,
         "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
        for s in symbols
    ])


def _bars_supplier(symbols: list[str]):
    sd = dt.date(2024, 9, 4)
    bars_by_symbol = {
        s: make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5, minute_volume=10_000)
        for s in symbols
    }
    return lambda sym, ts: bars_by_symbol.get(sym, pd.DataFrame())


def test_objective_mode_emits_same_candidates_as_full_mode():
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cfg = _cfg()
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars_supplier(symbols)
    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    scan_times = [scan_ts]

    state_full: dict = {}
    state_obj: dict = {}
    ctx_full = build_scan_session_context(
        cfg, daily_cache, universe, scan_times, collect_gate_dump=True,
    )
    ctx_obj = build_scan_session_context(
        cfg, daily_cache, universe, scan_times, collect_gate_dump=False,
    )

    r_full = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state=state_full, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=ctx_full, collect_gate_dump=True,
    )
    r_obj = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state=state_obj, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=ctx_obj, collect_gate_dump=False,
    )

    # Emitted candidates must match exactly.
    full_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in r_full.emitted]
    obj_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in r_obj.emitted]
    assert full_emits == obj_emits

    # Scanner state updates must match.
    assert state_full.get("symbol_last_emit_ts") == state_obj.get("symbol_last_emit_ts")
    assert state_full.get("signal_emits_per_symbol_today") == \
        state_obj.get("signal_emits_per_symbol_today")

    # Objective mode produces no per-symbol gate_dump but DOES produce
    # rejection counters whose per-reason totals match the full-mode dump.
    assert r_obj.gate_dump == []
    full_counts: dict[str, int] = {}
    for row in r_full.gate_dump:
        reason = row.get("rejection_reason")
        if reason:
            full_counts[reason] = full_counts.get(reason, 0) + 1
    assert dict(r_obj.rejection_counts) == full_counts


def test_objective_mode_no_dump_when_collect_false_with_legacy_inline_path():
    """Even without a precomputed scan_context, collect_gate_dump=False
    still suppresses the per-symbol dump and bumps counters."""
    symbols = ["AAA"]
    cfg = _cfg()
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars_supplier(symbols)
    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")

    r = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state={}, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=None, collect_gate_dump=False,
    )
    # If AAA passed gates, there is 1 emitted candidate and no dump row for it.
    assert r.gate_dump == []
