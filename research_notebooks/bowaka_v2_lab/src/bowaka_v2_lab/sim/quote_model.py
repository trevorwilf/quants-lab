"""Quote model — historical quote loader + conservative synthetic fallback.

Per [Report §9.8]: when historical quotes are unavailable for ``(symbol, t)``,
the simulator falls back to a synthetic quote with explicit identification
fields so downstream readers can tell real from synthetic.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from ..utils.time import require_aware_timestamp


@dataclass
class QuoteSnapshot:
    bid: float
    ask: float
    mid: float
    spread_pct: float
    quote_timestamp: str
    quote_age_seconds: float
    source: str
    calibration_dataset_hash: Optional[str] = None
    stress_level: Optional[str] = None


def synthesize_quote(
    *,
    last_price: float,
    at: Any,
    stress_level: str = "conservative",
    calibration_dataset_hash: Optional[str] = None,
) -> QuoteSnapshot:
    """Conservative synthetic quote — wider spread than historical.

    Per [Report §9.8] fields:
    - ``source = "synthetic_quote_model_v1"``
    - includes ``calibration_dataset_hash`` and ``stress_level``
    - ``quote_age_seconds`` = 0 by construction (synthesised at ``at``)
    """
    if last_price is None or last_price <= 0:
        raise ValueError("synthesize_quote: last_price must be > 0")
    at_ts = require_aware_timestamp(at, label="synthesize_quote.at")
    # Half-spread by stress level.
    half_spread_bps = {"base": 5.0, "conservative": 15.0, "severe": 50.0}.get(stress_level, 15.0)
    half = last_price * half_spread_bps / 10_000.0
    bid = round(last_price - half, 4)
    ask = round(last_price + half, 4)
    mid = round((bid + ask) / 2.0, 4)
    spread_pct = (ask - bid) / mid if mid > 0 else 0.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=spread_pct,
        quote_timestamp=at_ts.isoformat(),
        quote_age_seconds=0.0,
        source="synthetic_quote_model_v1",
        calibration_dataset_hash=calibration_dataset_hash,
        stress_level=stress_level,
    )


def get_quote(
    *,
    symbol: str,
    at: Any,
    last_price: float,
    historical_quote: Optional[dict] = None,
    stress_level: str = "conservative",
    calibration_dataset_hash: Optional[str] = None,
) -> QuoteSnapshot:
    """Return a quote, preferring historical when available, else synthetic."""
    if historical_quote:
        bid = float(historical_quote.get("bid", 0.0))
        ask = float(historical_quote.get("ask", 0.0))
        mid = float(historical_quote.get("mid", (bid + ask) / 2.0))
        spread_pct = float(historical_quote.get("spread_pct", (ask - bid) / mid if mid > 0 else 0.0))
        return QuoteSnapshot(
            bid=bid, ask=ask, mid=mid, spread_pct=spread_pct,
            quote_timestamp=str(historical_quote.get("quote_timestamp", "")),
            quote_age_seconds=float(historical_quote.get("quote_age_seconds", 0.0)),
            source=str(historical_quote.get("source", "historical")),
        )
    return synthesize_quote(
        last_price=last_price, at=at,
        stress_level=stress_level,
        calibration_dataset_hash=calibration_dataset_hash,
    )
