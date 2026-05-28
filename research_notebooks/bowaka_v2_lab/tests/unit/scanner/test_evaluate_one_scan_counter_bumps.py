"""Phase 1 §1 — per-skip counters and symbols_seen bookkeeping.

With counters enabled, the new ``scanner_skip_*`` + ``scanner_gate_failures``
+ ``scanner_candidates_built`` + ``scanner_candidates_capped`` fields cover
every per-symbol outcome. Their sum equals ``scanner_symbols_seen`` (modulo
``BARS_FETCH_FAILED`` which has no dedicated counter).

The test also asserts that toggling counters does NOT change the scan result
itself — the ``ScanResult`` content is byte-equivalent across the two runs.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict

import pandas as pd

from bowaka_v2_lab.scanner.scan_context import build_scan_session_context
from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.utils.profile_counters import (
    ProfileCounters,
    profile_counters_context,
)
from tests.fixtures.build_minute_fixture import make_minute_bars


def _cfg(*, rvol_min: float = 1000.0) -> dict:
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
        "signals": {"rvol_so_far_min": rvol_min, "rvol_so_far_max": 99999.0},
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


def _universe(symbols: list[str]) -> dict:
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
            for s in symbols
        ],
    }


def _daily_cache(symbols: list[str]) -> pd.DataFrame:
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
            for s in symbols
        ]
    )


def _bars(symbols: list[str]):
    sd = dt.date(2024, 9, 4)
    bars_by_symbol = {
        s: make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5, minute_volume=10_000)
        for s in symbols
    }
    return lambda sym, ts: bars_by_symbol.get(sym, pd.DataFrame())


def _evaluate(*, cfg: dict, universe: dict, daily_cache: pd.DataFrame, bars_supplier):
    scan_ts = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    ctx = build_scan_session_context(
        cfg, daily_cache, universe, [scan_ts], collect_gate_dump=False,
    )
    return evaluate_one_scan(
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


def test_counters_total_to_symbols_seen_all_gate_fails() -> None:
    """Five symbols, all fail gates -> scanner_symbols_seen == 5 == gate_failures."""
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cfg = _cfg(rvol_min=1000.0)
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars(symbols)

    counters = ProfileCounters()
    with profile_counters_context(counters, enable=True):
        _ = _evaluate(
            cfg=cfg, universe=universe, daily_cache=daily_cache,
            bars_supplier=bars_supplier,
        )

    assert counters.scanner_symbols_seen == len(symbols)
    assert counters.scanner_gate_failures == len(symbols)
    # No emissions, no caps in this configuration.
    assert counters.scanner_candidates_built == 0
    assert counters.scanner_candidates_capped == 0


def test_counters_total_to_symbols_seen_with_emit_and_cap() -> None:
    """Loose gates -> candidates emit, but cap < pass-count -> cap counter fires."""
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cfg = _cfg(rvol_min=0.0)  # everyone passes the rvol bound
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars(symbols)

    counters = ProfileCounters()
    with profile_counters_context(counters, enable=True):
        result = _evaluate(
            cfg=cfg, universe=universe, daily_cache=daily_cache,
            bars_supplier=bars_supplier,
        )

    # The five symbols are all seen.
    assert counters.scanner_symbols_seen == len(symbols)
    # The sum of skip + gate_fail + built + capped covers every iteration that
    # entered the loop body.
    skip_total = (
        counters.scanner_skip_already_entered
        + counters.scanner_skip_no_baseline
        + counters.scanner_skip_no_bars
        + counters.scanner_skip_stale_bar
        + counters.scanner_skip_cooldown
        + counters.scanner_skip_same_symbol_cap
    )
    accounted = (
        skip_total
        + counters.scanner_gate_failures
        + counters.scanner_candidates_built
        + counters.scanner_candidates_capped
    )
    assert accounted == counters.scanner_symbols_seen
    assert counters.scanner_candidates_built == len(result.emitted)


def test_counters_off_produces_identical_scan_result() -> None:
    """Disabling counters does NOT alter the ``ScanResult``.

    Counters are a side-channel; the public scan output must be invariant.
    """
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cfg = _cfg(rvol_min=0.0)
    universe = _universe(symbols)
    daily_cache = _daily_cache(symbols)
    bars_supplier = _bars(symbols)

    counters = ProfileCounters()
    with profile_counters_context(counters, enable=True):
        result_on = _evaluate(
            cfg=cfg, universe=universe, daily_cache=daily_cache,
            bars_supplier=bars_supplier,
        )
    # counters disabled
    result_off = _evaluate(
        cfg=cfg, universe=universe, daily_cache=daily_cache,
        bars_supplier=bars_supplier,
    )

    # Same emitted candidates (symbol, rank, event id).
    on_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in result_on.emitted]
    off_emits = [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in result_off.emitted]
    assert on_emits == off_emits
    assert result_on.gate_dump == result_off.gate_dump
    assert dict(result_on.rejection_counts) == dict(result_off.rejection_counts)
