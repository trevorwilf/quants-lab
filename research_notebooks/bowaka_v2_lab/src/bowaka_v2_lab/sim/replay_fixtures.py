"""Deterministic fixture loaders used by tests."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import pandas as pd


def synthetic_daily_cache(symbols: list[str], *, base_adv: float = 5_000_000) -> pd.DataFrame:
    rows = []
    for sym in symbols:
        rows.append({
            "symbol": sym,
            "prior_close": 100.0,
            "avg_volume_20d": 100_000,
            "avg_dollar_volume_20d": base_adv,
            "prior_atr_14d": 1.5,
            "prior_atr_pct": 0.015,
            "ema_10_prior": 99.5,
            "ema_10_lag_3": 99.0,
            "ema_slope_prior": 0.01,
        })
    return pd.DataFrame(rows)


def synthetic_universe(symbols: list[str]) -> dict[str, Any]:
    return {
        "universe_hash": "sha256:synthetic",
        "symbols": [
            {
                "symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                "instrument_class": "operating_equity",
                "eligible_for_bowaka_equity_bucket": True,
            }
            for s in symbols
        ],
    }
