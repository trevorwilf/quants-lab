"""Phase 1 §2 — subphase timers cover the scanner loop.

The scanner sub-timer fields (``scanner_time_*_seconds``) are populated when
counters are enabled. Their values must be >= 0; at least one must register
a non-zero duration on a small fixture so we know the perf_counter wiring
is alive.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import fields

import pandas as pd

from bowaka_v2_lab.scanner.scan_context import build_scan_session_context
from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.utils.profile_counters import (
    ProfileCounters,
    profile_counters_context,
)
from tests.fixtures.build_minute_fixture import make_minute_bars


_SUBPHASE_TIMER_FIELDS = (
    "scanner_time_bars_supplier_seconds",
    "scanner_time_stale_check_seconds",
    "scanner_time_aggregate_seconds",
    "scanner_time_features_seconds",
    "scanner_time_gates_seconds",
    "scanner_time_score_seconds",
    "scanner_time_event_builder_seconds",
    "scanner_time_sort_rank_seconds",
)


def test_all_subphase_timers_are_defined_on_profile_counters() -> None:
    """Defense in depth: the dataclass schema MUST include every timer field."""
    profile_field_names = {f.name for f in fields(ProfileCounters)}
    for name in _SUBPHASE_TIMER_FIELDS:
        assert name in profile_field_names, (
            f"ProfileCounters missing required Phase 1 subphase timer: {name}"
        )


def test_subphase_timers_are_non_negative_and_at_least_one_fires() -> None:
    symbols = ["AAA", "BBB", "CCC"]
    cfg = {
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
    universe = {
        "universe_hash": "sha256:t",
        "symbols": [
            {
                "symbol": s,
                "exchange": "NASDAQ",
                "venue_code": "XNAS",
                "instrument_class": "operating_equity",
                "eligible_for_bowaka_equity_bucket": True,
            }
            for s in symbols
        ],
    }
    daily_cache = pd.DataFrame(
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
            for s in symbols
        ]
    )
    sd = dt.date(2024, 9, 4)
    bars_by_symbol = {
        s: make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5, minute_volume=10_000)
        for s in symbols
    }
    bars_supplier = lambda sym, ts: bars_by_symbol.get(sym, pd.DataFrame())  # noqa: E731

    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    ctx = build_scan_session_context(
        cfg, daily_cache, universe, [scan_ts], collect_gate_dump=False,
    )

    counters = ProfileCounters()
    with profile_counters_context(counters, enable=True):
        result = evaluate_one_scan(
            cfg=cfg,
            universe_snapshot=universe,
            daily_cache=daily_cache,
            volume_curve=None,
            state={},
            scan_ts=scan_ts,
            bars_supplier=bars_supplier,
            scan_context=ctx,
            collect_gate_dump=False,
        )

    # Every timer is non-negative.
    for name in _SUBPHASE_TIMER_FIELDS:
        value = getattr(counters, name)
        assert isinstance(value, float)
        assert value >= 0.0, f"{name} reported negative time: {value!r}"

    # On this fixture at least one timer registers a non-zero duration. We
    # don't pin which (clocks vary), only that SOMETHING actually fired.
    timer_total = sum(getattr(counters, name) for name in _SUBPHASE_TIMER_FIELDS)
    assert timer_total > 0.0, (
        "all scanner subphase timers reported 0.0 seconds — perf_counter "
        "wiring is dead or counters were not active during the scan."
    )
    # Sanity-check the scan actually ran.
    assert result.emitted, "scan emitted no candidates — fixture/cfg issue"
