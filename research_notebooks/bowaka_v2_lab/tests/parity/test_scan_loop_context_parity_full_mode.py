"""Scan-context vs inline build: same emitted candidates, same gate dump.

Speedup report §5.4 / §11.2 Phase 4. Full-mode parity: passing
``scan_context=ctx, collect_gate_dump=True`` must produce identical
``ScanResult`` to the legacy ``scan_context=None`` path.
"""
from __future__ import annotations

import datetime as dt
from copy import deepcopy

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


@pytest.mark.parametrize("symbols", [
    ["AAA"],
    ["AAA", "BBB"],
    ["AAA", "BBB", "CCC", "DDD", "EEE"],  # exercises max_entries_per_scan capping
])
def test_full_mode_parity_legacy_vs_context(symbols: list[str]):
    """Same scan, same state — legacy and context paths produce identical results."""
    cfg = _cfg()
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars_supplier(symbols)
    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    scan_times = [scan_ts]

    state_legacy: dict = {}
    state_ctx: dict = {}

    r_legacy = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state=state_legacy, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=None, collect_gate_dump=True,
    )

    ctx = build_scan_session_context(
        cfg, daily_cache, universe, scan_times,
        volume_curve=None, collect_gate_dump=True,
    )
    r_ctx = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, state=state_ctx, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
        scan_context=ctx, collect_gate_dump=True,
    )

    # Identical emitted candidate symbols + ranks + event ids.
    legacy_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in r_legacy.emitted]
    ctx_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in r_ctx.emitted]
    assert legacy_emits == ctx_emits

    # Identical gate_dump rows (order-sensitive).
    assert len(r_legacy.gate_dump) == len(r_ctx.gate_dump)
    for a, b in zip(r_legacy.gate_dump, r_ctx.gate_dump):
        assert a.get("symbol") == b.get("symbol")
        assert a.get("rejection_reason") == b.get("rejection_reason")
        assert a.get("score") == b.get("score")
        assert a.get("rank") == b.get("rank")
        assert a.get("candidate_emitted") == b.get("candidate_emitted")

    # Identical scanner state updates.
    assert state_legacy.get("symbol_last_emit_ts") == state_ctx.get("symbol_last_emit_ts")
    assert state_legacy.get("signal_emits_per_symbol_today") == \
        state_ctx.get("signal_emits_per_symbol_today")
