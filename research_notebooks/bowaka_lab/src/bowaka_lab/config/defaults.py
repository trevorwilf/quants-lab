"""Default config dict matching ``configs/bowaka_research_variant.yml``."""

from __future__ import annotations

from datetime import date
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "project": {
        "name": "bowaka_lab",
        "mode": "research",
        "run_label": "bowaka_iex_exploratory_v1",
    },
    "storage": {
        "mongo_database": "quants_lab",
        "write_mongo": True,
        "write_parquet": True,
    },
    "data": {
        "vendor": "alpaca",
        "feed": "iex",
        "adjustment": "raw",
        "allow_feed_fallback": False,
        "rate_limit_requests_per_minute": 180,
        "start_date": date(2025, 1, 1),
        "end_date": date(2026, 5, 15),
    },
    "calendar": {"exchange": "XNYS", "timezone": "America/New_York", "session": "regular"},
    "universe": {
        "mode": "alpaca_current_assets",
        "allowed_exchanges": ["NASDAQ", "NYSE", "ARCA", "AMEX", "BATS"],
        "exclude_otc": True,
        "exclude_leveraged_etp": True,
        "exclude_inverse_etp": True,
        "exclude_etn": True,
        "ticker_blocklist": ["TSLL", "CONL", "SMCX"],
    },
    "prefilter": {
        "lookback_days": 20,
        "atr_days": 14,
        "ema_days": 10,
        "ema_slope_lookback": 3,
        "price_min": 1.0,
        "price_max": 20.0,
        "avg_dollar_volume_min": 200_000,
        "rvol_min": 1.5,
        "atr_pct_min": 0.06,
        "range_expansion_min": 1.25,
        "close_location_min": 0.60,
        "ema_distance_min": 0.0,
        "ema_slope_min": 0.0,
    },
    "entry": {
        "default_rule": "fixed_time_0945",
        "fixed_times": ["09:35", "09:40", "09:45", "10:00"],
        "fill_model": "next_minute_open_plus_slippage",
        "slippage_bps": 25.0,
        "use_quotes_if_available": True,
    },
    "exits": {
        "stop_pct": 0.08,
        "target_pct": 0.15,
        "max_hold_days": 3,
        "ambiguous_bar_policy": "stop_first",
        "stop_gap_policy": "next_available_open",
        "target_fill_policy": "limit_touch",
    },
    "signal_fade": {
        "enabled": True,
        "rth_eval_time": "15:45",
        "after_close_eval_time": "16:05",
        "after_close_action": "log_only",
        "execute_threshold": 8,
        "shadow_thresholds": [4, 5, 6, 7, 8, 9],
    },
    "portfolio": {
        "mode": "paper_data_collection",
        "sizing_mode": "equal_slice",
        "per_trade_notional": 5_000.0,
        "max_concurrent_positions": 18,
        "max_total_entries_per_day": 25,
        "max_gross_exposure_pct": 2.0,
    },
}
