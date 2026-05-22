"""Phase 6 — market order fills at quote.ask + slippage; full fill within liquidity.

A market parent order fills the full requested quantity when the order notional
is within the liquidity proxy, at ``quote.ask`` plus stress-scaled slippage.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_market_fill


def _ask_quote(ask: float):
    """A QuoteSnapshot with an explicit ask (a small positive spread)."""
    from bowaka_v2_lab.sim.quote_model import QuoteSnapshot

    bid = ask - 0.04
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source="historical", bid_size=10_000, ask_size=10_000,
    )


def test_market_full_fill_within_liquidity():
    q = _ask_quote(ask=100.04)
    fill = simulate_market_fill(
        side="buy", requested_qty=100, quote=q,
        liquidity_proxy_shares=10_000, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=500.0,
    )
    assert fill.filled is True
    assert fill.filled_qty == 100
    assert fill.is_partial is False
    # Fill price is quote.ask + a positive slippage premium.
    assert fill.avg_fill_price > 100.04
    assert fill.slippage_bps_total > 0.0
    assert abs(fill.notional - fill.filled_qty * fill.avg_fill_price) < 1e-6


def test_market_fill_records_commission_and_fees():
    q = _ask_quote(ask=20.0)
    fill = simulate_market_fill(
        side="buy", requested_qty=200, quote=q,
        liquidity_proxy_shares=100_000, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=100.0,
        commission_per_share=0.005, regulatory_fee_bps=0.2,
    )
    assert fill.filled is True
    assert fill.commission == round(0.005 * 200, 6)
    assert fill.regulatory_fees > 0.0
    assert fill.total_fees == fill.commission + fill.regulatory_fees


def test_market_fill_zero_fees_by_default():
    q = _ask_quote(ask=15.0)
    fill = simulate_market_fill(
        side="buy", requested_qty=50, quote=q,
        liquidity_proxy_shares=100_000, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=10.0,
    )
    assert fill.commission == 0.0
    assert fill.regulatory_fees == 0.0


def test_market_partial_fill_when_notional_exceeds_liquidity():
    """When requested qty exceeds the liquidity proxy the fill is partial."""
    q = _ask_quote(ask=10.0)
    fill = simulate_market_fill(
        side="buy", requested_qty=10_000, quote=q,
        liquidity_proxy_shares=3_000, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=100.0,
    )
    assert fill.filled is True
    assert fill.is_partial is True
    assert fill.filled_qty == 3_000  # capped at the liquidity proxy
