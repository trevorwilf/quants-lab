"""Phase 6 — a partial fill below min_order_notional → no position (partial_below_min).

When liquidity caps the fill so small that the filled notional falls below
``min_order_notional``, the fill is downgraded to a no-fill with reason
``partial_below_min`` — too small a lot to be worth opening a position.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_market_fill, simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot  # noqa: F401 — used below


def _quote(ask: float) -> QuoteSnapshot:
    bid = ask - 0.02
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source="historical", bid_size=100, ask_size=100,
    )


def test_market_partial_below_min_is_no_fill():
    # Liquidity caps the fill at ~10 shares of a $10 stock = ~$100 notional,
    # well below a $500 min_order_notional.
    q = _quote(ask=10.0)
    fill = simulate_market_fill(
        side="buy", requested_qty=1_000, quote=q,
        liquidity_proxy_shares=10, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=500.0,
    )
    assert fill.filled is False
    assert fill.reason == "partial_below_min"
    assert fill.filled_qty == 0


def test_marketable_limit_partial_below_min_is_no_fill():
    # Realism remediation 2 Phase 5 (audit P0-006): T1 walks the book one cent
    # at a time. A 5-share ``ask_size`` at $10 leaves the order partial-filled
    # at well below ``min_order_notional`` → no-fill.
    q = QuoteSnapshot(
        bid=9.98, ask=10.0, mid=9.99, spread_pct=0.002,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source="historical", bid_size=5, ask_size=5,
    )
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=1_000, quote=q,
        marketable_limit_slippage_pct=0.0001,  # limit = 10.001, leaves no room
        marketable_limit_timeout_seconds=30,
        minute_bars=None, scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        liquidity_proxy_shares=10, cost_stress="base",
        min_order_notional=500.0,
    )
    assert fill.filled is False
    assert fill.reason == "partial_below_min"


def test_partial_above_min_still_fills():
    """A partial whose notional clears min_order_notional still fills."""
    q = _quote(ask=10.0)
    # 300 shares * ~$10 = ~$3000 notional, above the $500 min.
    fill = simulate_market_fill(
        side="buy", requested_qty=1_000, quote=q,
        liquidity_proxy_shares=300, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=500.0,
    )
    assert fill.filled is True
    assert fill.is_partial is True
    assert fill.filled_qty == 300
