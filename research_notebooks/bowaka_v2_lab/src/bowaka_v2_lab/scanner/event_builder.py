"""Pure ``build_candidate_event`` (extracted from
``bowaka_intraday_scanner.py`` lines 217-298).

This function has no I/O. Identical inputs produce a byte-identical event
dict (modulo dict-key insertion order; downstream JSON serialisation should
use ``sort_keys=True`` for byte-equality).
"""
from __future__ import annotations

import datetime as _dt
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import pandas as pd

from ..schemas.events import CANDIDATE_EVENT_SCHEMA_VERSION, make_event_id


def _iso_utc(t: Any) -> str:
    ts = pd.Timestamp(t)
    if ts.tzinfo is None:
        # Reject naive — see [Report §8.5]. The event_builder is pure and may
        # be called from tests, but the scanner caller passes tz-aware values.
        raise ValueError("build_candidate_event: scan_ts must be tz-aware")
    return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_date_et(t: Any) -> str:
    ts = pd.Timestamp(t)
    if ts.tzinfo is None:
        raise ValueError("build_candidate_event: scan_ts must be tz-aware")
    return ts.tz_convert("America/New_York").date().isoformat()


def build_candidate_event(
    *,
    symbol: str,
    universe_meta: Mapping[str, Any],
    cfg: Mapping[str, Any],
    universe_hash: str,
    config_hash_v: str,
    session_bar: Mapping[str, Any],
    prior_baselines: Mapping[str, Any],
    forming_feats: Mapping[str, Any],
    volume_curve_fraction: float,
    gate_results: Mapping[str, bool],
    candidate_rank: int,
    scan_ts: Any,
    signal_strength: float,
    generated_at: Any | None = None,
) -> dict[str, Any]:
    """Materialise the schema-v3 candidate_signal event."""
    scan_iso = _iso_utc(scan_ts)
    session_date = _session_date_et(scan_ts)
    scanner_cfg = (cfg.get("scanner") or {})
    expiry_s = int(scanner_cfg.get("signal_expiry_seconds", 600))
    scan_ts_obj = pd.Timestamp(scan_ts)
    expiry_ts = scan_ts_obj + pd.Timedelta(seconds=expiry_s)
    expiry_iso = expiry_ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")

    if generated_at is None:
        generated_at_iso = scan_iso
    else:
        generated_at_iso = _iso_utc(generated_at)

    data_cfg = (cfg.get("data") or cfg.get("market_data") or {})

    return {
        "schema_version": CANDIDATE_EVENT_SCHEMA_VERSION,
        "strategy": "bowaka_v2",
        "event_type": "candidate_signal",
        "event_id": make_event_id("bowaka_v2", session_date, symbol, scan_iso),
        "generated_at": generated_at_iso,
        "session_date": session_date,
        "scan_timestamp": scan_iso,
        "provider": data_cfg.get("provider", data_cfg.get("minute_bar_source", "alpaca")),
        "data_feed": data_cfg.get("feed", "iex"),
        "bar_interval": data_cfg.get("intraday_timeframe", "1m"),
        "config_hash": config_hash_v,
        "universe_hash": universe_hash,
        "symbol": symbol,
        "exchange": universe_meta.get("exchange"),
        "venue_code": universe_meta.get("venue_code") or "XNAS",
        "instrument_class": universe_meta.get("instrument_class"),
        "eligible_for_bowaka_equity_bucket":
            universe_meta.get("eligible_for_bowaka_equity_bucket", True),
        "prior_daily_baselines": {
            "prior_close":            prior_baselines.get("prior_close"),
            "avg_volume_20d":         prior_baselines.get("avg_volume_20d"),
            "avg_dollar_volume_20d":  prior_baselines.get("avg_dollar_volume_20d"),
            "prior_atr_14d":          prior_baselines.get("prior_atr_14d"),
            "prior_atr_pct":          prior_baselines.get("prior_atr_pct"),
            "ema_10_prior":           prior_baselines.get("ema_10_prior"),
            "ema_10_lag_3":           prior_baselines.get("ema_10_lag_3"),
            "ema_slope_prior":        prior_baselines.get("ema_slope_prior"),
        },
        "forming_session_bar": dict(session_bar),
        "intraday_volume_context": {
            "volume_curve_fraction": volume_curve_fraction,
            "expected_volume_until_scan": forming_feats.get("expected_volume_until_scan"),
            "rvol_so_far": forming_feats.get("rvol_so_far"),
            "projected_full_day_rvol": forming_feats.get("projected_full_day_rvol"),
        },
        "features": {
            "gap_pct": forming_feats.get("gap_pct"),
            "current_return_pct": forming_feats.get("current_return_pct"),
            "range_expansion_so_far": forming_feats.get("range_expansion_so_far"),
            "close_location_so_far": forming_feats.get("close_location_so_far"),
            "ema_distance": forming_feats.get("ema_distance"),
            "ema_slope": prior_baselines.get("ema_slope_prior"),
            "signal_strength": signal_strength,
        },
        "gate_results": dict(gate_results),
        "candidate_rank": candidate_rank,
        "signal_expiry_timestamp": expiry_iso,
    }
