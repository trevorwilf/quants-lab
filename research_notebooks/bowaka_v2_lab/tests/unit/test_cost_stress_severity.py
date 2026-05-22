"""Phase 6 — base / conservative / severe cost stress → monotonically worse slippage.

The cost-stress mode multiplies fill slippage by ``{base:1.0, conservative:2.0,
severe:3.5}`` and tightens the fill-rate cap, so a buy fills at a strictly worse
(higher) price as the stress level rises.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import (
    simulate_market_fill,
    stress_fill_rate_cap,
    stress_slippage_multiplier,
)
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot


def _quote(ask: float = 100.0) -> QuoteSnapshot:
    bid = ask - 0.04
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source="historical", bid_size=10_000, ask_size=10_000,
    )


def test_slippage_multiplier_is_monotone():
    b = stress_slippage_multiplier("base")
    c = stress_slippage_multiplier("conservative")
    s = stress_slippage_multiplier("severe")
    assert b < c < s
    assert (b, c, s) == (1.0, 2.0, 3.5)


def test_fill_rate_cap_tightens_with_stress():
    b = stress_fill_rate_cap("base")
    c = stress_fill_rate_cap("conservative")
    s = stress_fill_rate_cap("severe")
    # Severe stress assumes a thinner book — a strictly tighter cap.
    assert b >= c >= s
    assert s < b


def test_buy_fill_price_worsens_with_stress():
    q = _quote(ask=100.0)
    prices = []
    for stress in ("base", "conservative", "severe"):
        fill = simulate_market_fill(
            side="buy", requested_qty=100, quote=q,
            liquidity_proxy_shares=1_000_000, cost_stress=stress,
            adv_participation_frac=0.01, min_order_notional=100.0,
        )
        assert fill.filled is True
        prices.append(fill.avg_fill_price)
    # A buy pays more as the cost stress rises — strictly monotone.
    assert prices[0] < prices[1] < prices[2]


def test_slippage_bps_worsens_with_stress():
    q = _quote(ask=100.0)
    slippages = []
    for stress in ("base", "conservative", "severe"):
        fill = simulate_market_fill(
            side="buy", requested_qty=100, quote=q,
            liquidity_proxy_shares=1_000_000, cost_stress=stress,
            adv_participation_frac=0.01, min_order_notional=100.0,
        )
        slippages.append(fill.slippage_bps_total)
    assert slippages[0] < slippages[1] < slippages[2]
