"""Default config values mirroring ``configs/bowaka_v2_research_iex_plumbing.yml``.

These are the in-code defaults applied when a section is omitted or used during
synthetic-test setup. The YAML configs always win when present.
"""
from __future__ import annotations

from typing import Any


DEFAULTS: dict[str, Any] = {
    "strategy_id": "bowaka_v2",
    "strategy_version": "0.1.0",
    "market_data": {
        "feed": "iex",
        "allow_non_sip_for_research_only": True,
        "max_bar_age_seconds": 90,
        "minute_bar_source": "alpaca",
        "daily_bar_source": "alpaca",
        "quote_source": "alpaca",
        "assume_naive_timezone": False,
        "shared_root": None,
    },
    "session": {
        "calendar": "XNYS",
        "scan_window_local_start": "09:30",
        "scan_window_local_end": "15:55",
        "scan_interval_seconds": 60,
    },
    "universe": {
        "asset_classes": ["operating_equity"],
        "min_price": 1.0,
        "max_price": 1000.0,
        "min_adv_dollars": 1_000_000,
        "exclude_pattern_class": True,
    },
    "scanner": {
        "max_candidates_per_scan": 10,
        "max_entries_per_scan": 3,
        "min_signal_strength": 0.5,
    },
    "signals": {
        "allow_unknown_instrument_class_for_research": False,
    },
    "execution": {
        "order_type": "marketable_limit",
        "limit_offset_bps": 5,
        "max_quote_age_seconds": 5,
        "max_spread_bps": 50,
    },
    "sizing": {
        "method": "fixed_dollar",
        "dollars_per_position": 5000,
        "max_position_dollars": 25_000,
    },
    "risk": {
        "max_concurrent_positions": 5,
        "max_total_entries_per_day": 12,
        "max_gross_exposure_pct": 0.50,
        "daily_loss_pct": 0.02,
        "strategy_slice_loss_pct": 0.05,
        "max_stopouts_per_day": 4,
        "stop_trading_after_consecutive_stopouts": 3,
        "adv_tier_caps": [],
    },
    "exits": {
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.06,
        "max_hold_days": 5,
        "signal_fade_mode": "telemetry_only",
    },
    "backtest": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "cost_stress": "base",
        "entry_delay_minutes": 0,
    },
    "artifacts": {
        "write_parquet": True,
        "write_jsonl": True,
    },
    "run": {
        "kind": "backtest",
        "seed": 1337,
    },
    "paths": {
        "lab_root": "research_notebooks/bowaka_v2_lab",
        "data_root": "research_notebooks/bowaka_v2_lab/data",
        "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
    },
}
