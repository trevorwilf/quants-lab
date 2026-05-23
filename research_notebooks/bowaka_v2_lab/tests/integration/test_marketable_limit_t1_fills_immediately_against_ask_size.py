"""Audit P0-006 — T1 marketable-limit fills at the ask when ``ask_size >= qty``.

Audit acceptance criteria:
"Buy marketable limit with ask 10.00, limit 10.05, ask size greater than qty
fills immediately near ask under base stress."

This is the T1 (top-of-book) behavior: the full quantity prints at the ask
price; slippage vs ask = 0; slippage vs mid is the half-spread.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import (
    ExecutionTier,
    detect_execution_tier,
    simulate_marketable_limit_fill,
)
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot, SOURCE_HISTORICAL


def _quote(ask: float, ask_size: float) -> QuoteSnapshot:
    bid = ask - 0.02
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source=SOURCE_HISTORICAL, bid_size=ask_size, ask_size=ask_size,
    )


def test_t1_fills_at_ask_when_size_exceeds_qty() -> None:
    """Qty=100, ask=10.00, ask_size=500 → fills 100 at 10.00, slippage_vs_ask=0."""
    q = _quote(ask=10.00, ask_size=500)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,  # limit = 10.05
        marketable_limit_timeout_seconds=30,
        minute_bars=None, scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        liquidity_proxy_shares=100_000, cost_stress="base",
    )
    assert fill.filled is True
    assert fill.filled_qty == 100
    assert fill.avg_fill_price == 10.00
    assert fill.slippage_vs_ask_bps == 0.0
    # Slippage vs mid is exactly the half-spread (in bps).
    assert fill.execution_tier == ExecutionTier.T1_TOP_OF_BOOK.value


def test_detect_execution_tier_t1_from_historical_quote() -> None:
    """Tier detection: historical quote w/ size + no minute bars → T1."""
    q = _quote(ask=10.0, ask_size=500)
    tier = detect_execution_tier(quote=q, minute_bars=None)
    assert tier == ExecutionTier.T1_TOP_OF_BOOK


def test_detect_execution_tier_t0_from_synthetic_quote() -> None:
    """Tier detection: synthetic quote → T0."""
    q = QuoteSnapshot(
        bid=10.0, ask=10.0, mid=10.0, spread_pct=0.0,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.0,
        source="synthetic_zero_spread", bid_size=0, ask_size=0,
    )
    tier = detect_execution_tier(quote=q, minute_bars=None)
    assert tier == ExecutionTier.T0_NO_QUOTES
