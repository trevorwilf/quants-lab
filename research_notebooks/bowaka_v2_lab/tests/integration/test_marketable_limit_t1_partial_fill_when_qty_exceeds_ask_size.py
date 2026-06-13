"""Audit P0-006 / realism L2 — T1 marketable-limit caps at the displayed touch.

Audit acceptance criteria (P0-006):
"Buy marketable limit with ask size below qty produces partial fill or staged
fill, not automatic full fill."

L2 fix (realism remediation 2026-06): the original T1 path filled ``ask_size`` at
the ask then walked one cent at a time up to ``limit_price`` — *re-consuming the
full displayed size at every penny level*, manufacturing depth (up to ~100x the
NBBO touch) the lab cannot actually see (it has no L2 book). T1 now fills at most
the DISPLAYED top-of-book size at the touch; the remainder is an honest partial.
The realism modes (T3 / tape_replay) supply real deeper-book depth instead.
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
    """Qty=1000, ask=10.00, ask_size=200 → fills the displayed 200 at the touch.

    L2 changelog: was ``filled_qty == 1000`` (the cent-walk re-consumed the 200
    displayed size at each of ~6 penny levels, fabricating ~1000 shares of depth).
    The honest model caps the fill at the displayed touch (200 @ 10.00) and leaves
    the remaining 800 unfilled — no book-walking without real L2 depth.
    """
    q = _quote(ask=10.00, ask_size=200)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=1000, quote=q,
        marketable_limit_slippage_pct=0.005,  # limit = 10.05 (no longer walked)
        marketable_limit_timeout_seconds=30,
        minute_bars=None, scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        cost_stress="base",
        min_order_notional=500.0,
    )
    assert fill.filled is True
    # Capped at the displayed top-of-book size — no fabricated deeper-book depth.
    assert fill.filled_qty == 200
    assert fill.is_partial is True
    # Fills at the touch (no penny-walking above the ask).
    assert fill.avg_fill_price == 10.00
    assert fill.slippage_vs_ask_bps == 0.0


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
