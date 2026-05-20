"""Fill model — partial fills when size > liquidity, latency from scan to fill."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .cost_model import slippage_bps
from .quote_model import QuoteSnapshot


@dataclass
class FillResult:
    filled_qty: int
    avg_fill_price: float
    slippage_bps_total: float
    is_partial: bool
    notional: float


def simulate_fill(
    *,
    side: str,
    requested_qty: int,
    quote: QuoteSnapshot,
    available_liquidity: Optional[int] = None,
    stress_level: str = "conservative",
    adv_participation_frac: float = 0.001,
) -> FillResult:
    """Simulate a fill against a quote.

    - When ``requested_qty > available_liquidity`` (if supplied), the fill is partial.
    - The fill price is the quote's ask (buy) or bid (sell) adjusted by slippage bps.
    """
    if requested_qty <= 0:
        return FillResult(filled_qty=0, avg_fill_price=0.0, slippage_bps_total=0.0, is_partial=False, notional=0.0)

    side_l = side.lower()
    if available_liquidity is not None and requested_qty > available_liquidity:
        filled = max(0, int(available_liquidity))
        is_partial = filled < requested_qty
    else:
        filled = requested_qty
        is_partial = False

    bp = slippage_bps(stress_level=stress_level, adv_participation_frac=adv_participation_frac)
    bps_factor = bp / 10_000.0
    if side_l == "buy":
        price = quote.ask * (1.0 + bps_factor)
    else:
        price = quote.bid * (1.0 - bps_factor)
    notional = filled * price
    return FillResult(
        filled_qty=filled,
        avg_fill_price=round(price, 4),
        slippage_bps_total=bp,
        is_partial=is_partial,
        notional=notional,
    )
