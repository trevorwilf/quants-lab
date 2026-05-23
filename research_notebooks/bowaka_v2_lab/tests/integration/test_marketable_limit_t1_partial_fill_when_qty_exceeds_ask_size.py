"""Audit P0-006 — T1 marketable-limit walks the book past ask when qty > ask_size.

Audit acceptance criteria:
"Buy marketable limit with ask size below qty produces partial fill or staged
fill, not automatic full fill."

T1 behavior: fill ``ask_size`` at the ask, then walk one cent at a time up to
``limit_price``. With ``ask_size = 200`` and a sufficient limit-offset, the
remainder of a 1000-share order fills over multiple price levels.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot, SOURCE_HISTORICAL


def _quote(ask: float, ask_size: float) -> QuoteSnapshot:
    bid = ask - 0.02
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source=SOURCE_HISTORICAL, bid_size=ask_size, ask_size=ask_size,
    )


def test_t1_partial_fill_when_qty_exceeds_ask_size() -> None:
    """Qty=1000, ask=10.00, ask_size=200, limit=10.05 → partial-fill walks the book."""
    q = _quote(ask=10.00, ask_size=200)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=1000, quote=q,
        marketable_limit_slippage_pct=0.005,  # limit = 10.05 → walks 5 cents
        marketable_limit_timeout_seconds=30,
        minute_bars=None, scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        cost_stress="base",
        min_order_notional=500.0,
    )
    assert fill.filled is True
    # 200 at 10.00, then 200 each at 10.01, 10.02, 10.03, 10.04, 10.05 — at
    # most ~1200 over 6 levels. Capped at requested 1000.
    assert fill.filled_qty == 1000
    # Avg price is strictly above the ask (we walked levels).
    assert fill.avg_fill_price > 10.00
    # Slippage vs ask is positive (paid above the ask).
    assert fill.slippage_vs_ask_bps > 0


def test_t1_partial_when_book_too_thin_to_fill_full_qty() -> None:
    """Qty=1000, ask_size=50, limit=10.001 → small partial."""
    q = _quote(ask=10.00, ask_size=50)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=1000, quote=q,
        marketable_limit_slippage_pct=0.0001,  # limit ~ 10.001 — almost zero room
        marketable_limit_timeout_seconds=30,
        minute_bars=None, scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        cost_stress="base",
        min_order_notional=100.0,
    )
    assert fill.filled is True
    assert fill.filled_qty < 1000
    assert fill.is_partial is True
