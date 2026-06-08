"""T3_NBBO_DEPTH real fill model (audit §10f, Phase 1).

The T3 tier fills the REAL displayed top-of-book size always; beyond it, up to
``participation_cap`` of the scan minute's share volume (no fabricated depth).
The fill price pays the real half-spread plus a sqrt/linear market-impact term
scaled by the order's participation in the minute volume.

These tests exercise the new ``_t3_depth_impact_fill`` helper via both routing
paths (``simulate_marketable_limit_fill`` with ``has_nbbo_depth=True`` and
``simulate_market_fill`` with ``has_nbbo_depth=True``) and confirm the
default-off market path is byte-identical to today.
"""
from __future__ import annotations

import math

import pandas as pd

from bowaka_v2_lab.sim.cost_model import get_params
from bowaka_v2_lab.sim.fills import (
    COST_STRESS_SLIPPAGE_MULT,
    ExecutionTier,
    simulate_market_fill,
    simulate_marketable_limit_fill,
)
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot


def _quote(*, ask: float = 100.10, ask_size: float = 500.0,
           bid: float = 100.00, bid_size: float = 500.0) -> QuoteSnapshot:
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source="historical", bid_size=bid_size, ask_size=ask_size,
    )


def _minute_bars(*, volume: float, ts: str = "2024-09-04T14:00:00Z") -> pd.DataFrame:
    return pd.DataFrame(
        [{"timestamp": ts, "open": 100.0, "high": 100.2, "low": 99.9,
          "close": 100.05, "volume": volume}]
    )


SCAN_TS = "2024-09-04T14:00:00Z"


# ---------------------------------------------------------------------------
# (1) Touch-only fill: participation_cap * minute_vol < touch_size.
# ---------------------------------------------------------------------------
def test_touch_only_fill_when_cap_below_touch():
    # touch_size=500; minute_vol=1000 shares -> cap_shares=0.10*1000=100 < 500.
    # max(touch, cap)=500, so a 300-share buy is fully filled at the touch model.
    q = _quote(ask=100.10, ask_size=500.0)
    bars = _minute_bars(volume=1000.0)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=300, quote=q,
        minute_bars=bars, scan_ts=SCAN_TS,
        cost_stress="base", min_order_notional=0.0,
        has_nbbo_depth=True, minute_volume_participation_frac=0.10,
        market_impact_coef_bps=10.0, market_impact_model="sqrt",
    )
    assert fill.filled is True
    assert fill.is_partial is False
    assert fill.filled_qty == 300
    assert fill.execution_tier == ExecutionTier.T3_NBBO_DEPTH.value

    participation = 300 / 1000.0
    frac = math.sqrt(participation)
    impact_bps = 10.0 * frac * COST_STRESS_SLIPPAGE_MULT["base"]
    half_spread_bps = get_params("base").half_spread_bps
    total_bps = half_spread_bps + impact_bps
    expected_price = round(q.ask * (1.0 + total_bps / 1e4), 4)
    assert fill.avg_fill_price == expected_price
    assert fill.slippage_bps_total == round(total_bps, 4)
    assert fill.liquidity_participation_frac == round(participation, 6)


# ---------------------------------------------------------------------------
# (2) Participation cap binds -> partial fill.
# ---------------------------------------------------------------------------
def test_participation_cap_binds_partial():
    # touch_size=100; minute_vol=10000 -> cap_shares=0.10*10000=1000.
    # max(touch=100, cap=1000)=1000 < requested 5000 -> partial fillable=1000.
    q = _quote(ask=100.10, ask_size=100.0)
    bars = _minute_bars(volume=10_000.0)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=5000, quote=q,
        minute_bars=bars, scan_ts=SCAN_TS,
        cost_stress="base", min_order_notional=0.0,
        has_nbbo_depth=True, minute_volume_participation_frac=0.10,
        market_impact_coef_bps=10.0, market_impact_model="sqrt",
    )
    assert fill.filled is True
    assert fill.is_partial is True
    assert fill.filled_qty == 1000
    assert fill.reason == "partial_fill"
    assert fill.execution_tier == ExecutionTier.T3_NBBO_DEPTH.value
    assert fill.liquidity_participation_frac == round(1000 / 10_000.0, 6)


# ---------------------------------------------------------------------------
# (3) sqrt vs linear impact_bps differ.
# ---------------------------------------------------------------------------
def test_sqrt_vs_linear_impact():
    q = _quote(ask=100.10, ask_size=500.0)
    bars = _minute_bars(volume=1000.0)
    common = dict(
        side="buy", requested_qty=300, quote=q,
        minute_bars=bars, scan_ts=SCAN_TS,
        cost_stress="base", min_order_notional=0.0,
        has_nbbo_depth=True, minute_volume_participation_frac=0.10,
        market_impact_coef_bps=10.0,
    )
    f_sqrt = simulate_marketable_limit_fill(market_impact_model="sqrt", **common)
    f_lin = simulate_marketable_limit_fill(market_impact_model="linear", **common)

    participation = 300 / 1000.0  # 0.3
    half_spread_bps = get_params("base").half_spread_bps
    sqrt_bps = half_spread_bps + 10.0 * math.sqrt(participation)
    lin_bps = half_spread_bps + 10.0 * participation
    assert f_sqrt.slippage_bps_total == round(sqrt_bps, 4)
    assert f_lin.slippage_bps_total == round(lin_bps, 4)
    # sqrt(0.3) > 0.3, so sqrt impact is strictly larger here.
    assert f_sqrt.slippage_bps_total > f_lin.slippage_bps_total


# ---------------------------------------------------------------------------
# (4) Partial below min_notional -> no_fill.
# ---------------------------------------------------------------------------
def test_partial_below_min_notional_no_fill():
    # touch_size=5; minute_vol=100 -> cap_shares=0.10*100=10.
    # max(touch=5, cap=10)=10 < requested 5000 -> partial fillable=10.
    # notional ~ 10 * ~100.1 ~= 1001 < min_order_notional=100000 -> no_fill.
    q = _quote(ask=100.10, ask_size=5.0)
    bars = _minute_bars(volume=100.0)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=5000, quote=q,
        minute_bars=bars, scan_ts=SCAN_TS,
        cost_stress="base", min_order_notional=100_000.0,
        has_nbbo_depth=True, minute_volume_participation_frac=0.10,
        market_impact_coef_bps=10.0, market_impact_model="sqrt",
    )
    assert fill.filled is False
    assert fill.reason == "partial_below_min"
    assert fill.execution_tier == ExecutionTier.T3_NBBO_DEPTH.value


# ---------------------------------------------------------------------------
# (5) Byte-identical: simulate_market_fill(has_nbbo_depth=False) == today.
# ---------------------------------------------------------------------------
def test_market_fill_default_off_byte_identical():
    q = _quote(ask=100.10, ask_size=10_000.0)
    bars = _minute_bars(volume=50_000.0)

    # Today's call: no new kwargs at all (pre-Phase-1 signature surface).
    baseline = simulate_market_fill(
        side="buy", requested_qty=100, quote=q,
        liquidity_proxy_shares=10_000, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=500.0,
        commission_per_share=0.0, regulatory_fee_bps=0.0,
    )
    # Same call with the new kwargs supplied but has_nbbo_depth=False (default).
    with_kwargs_default_off = simulate_market_fill(
        side="buy", requested_qty=100, quote=q,
        liquidity_proxy_shares=10_000, cost_stress="base",
        adv_participation_frac=0.001, min_order_notional=500.0,
        commission_per_share=0.0, regulatory_fee_bps=0.0,
        has_nbbo_depth=False, minute_bars=bars, scan_ts=SCAN_TS,
        participation_cap=0.10, market_impact_coef_bps=10.0,
        market_impact_model="sqrt",
    )
    assert with_kwargs_default_off == baseline
    # And it is NOT the T3 path (the default proxy path never sets T3).
    assert baseline.execution_tier != ExecutionTier.T3_NBBO_DEPTH.value


def test_market_fill_nbbo_depth_on_routes_t3():
    # has_nbbo_depth=True on the market path routes T3 with the touch model.
    q = _quote(ask=100.10, ask_size=200.0)
    bars = _minute_bars(volume=5000.0)
    fill = simulate_market_fill(
        side="buy", requested_qty=300, quote=q,
        cost_stress="base", min_order_notional=0.0,
        has_nbbo_depth=True, minute_bars=bars, scan_ts=SCAN_TS,
        participation_cap=0.10, market_impact_coef_bps=10.0,
        market_impact_model="sqrt",
    )
    assert fill.filled is True
    assert fill.order_style == "market"
    assert fill.execution_tier == ExecutionTier.T3_NBBO_DEPTH.value
    # cap_shares=0.10*5000=500; max(touch=200, cap=500)=500 >= 300 -> full fill.
    assert fill.filled_qty == 300
    assert fill.is_partial is False


def test_sell_side_uses_bid_touch():
    # Mirror logic: a sell fills against bid/bid_size and prices DOWN.
    q = _quote(ask=100.10, ask_size=500.0, bid=100.00, bid_size=400.0)
    bars = _minute_bars(volume=1000.0)
    fill = simulate_marketable_limit_fill(
        side="sell", requested_qty=300, quote=q,
        minute_bars=bars, scan_ts=SCAN_TS,
        cost_stress="base", min_order_notional=0.0,
        has_nbbo_depth=True, minute_volume_participation_frac=0.10,
        market_impact_coef_bps=10.0, market_impact_model="sqrt",
    )
    assert fill.filled is True
    assert fill.filled_qty == 300
    participation = 300 / 1000.0
    half_spread_bps = get_params("base").half_spread_bps
    total_bps = half_spread_bps + 10.0 * math.sqrt(participation)
    expected_price = round(q.bid * (1.0 - total_bps / 1e4), 4)
    assert fill.avg_fill_price == expected_price
    # Sell prices below the bid (worse for the seller).
    assert fill.avg_fill_price < q.bid
