"""Fill model (Phase 6) — realistic fill prices, quantities, rejects and fees.

Two parent-order styles, mirroring the live strategy:

- ``market`` — fill at ``quote.ask + slippage`` (a buy). Full quantity when the
  order notional fits the liquidity proxy; otherwise a partial fill. A partial
  whose filled notional is below ``min_order_notional`` is downgraded to a
  no-fill with reason ``partial_below_min`` — too small a lot to bother.
- ``marketable_limit`` — limit ``= quote.ask * (1 + marketable_limit_slippage_pct)``.
  The order fills only if the quote does not chase past the limit within
  ``marketable_limit_timeout_seconds`` (walked over the minute-bar path forward
  from ``scan_ts``); otherwise it times out with no position.

Every fill records commissions and regulatory fees (defaults $0, config-
overridable). ``cost_stress`` scales slippage by ``{base:1.0, conservative:2.0,
severe:3.5}`` and tightens the fill-rate cap.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

from .cost_model import slippage_bps
from .quote_model import QuoteSnapshot

#: Cost-stress slippage multipliers (Phase 6 Task 6). ``base`` is the lab's
#: nominal model; ``conservative`` doubles it; ``severe`` is 3.5x.
COST_STRESS_SLIPPAGE_MULT: dict[str, float] = {
    "base": 1.0,
    "conservative": 2.0,
    "severe": 3.5,
}

#: Cost-stress fill-rate caps — the fraction of the liquidity proxy a single
#: order may consume before it is forced partial. Severe stress assumes a
#: thinner book.
COST_STRESS_FILL_RATE_CAP: dict[str, float] = {
    "base": 1.0,
    "conservative": 0.85,
    "severe": 0.60,
}


def stress_slippage_multiplier(cost_stress: str) -> float:
    """Slippage multiplier for ``cost_stress`` (``base`` / ``conservative`` / ``severe``)."""
    return COST_STRESS_SLIPPAGE_MULT.get(str(cost_stress), COST_STRESS_SLIPPAGE_MULT["conservative"])


def stress_fill_rate_cap(cost_stress: str) -> float:
    """Fill-rate cap for ``cost_stress`` — fraction of the liquidity proxy usable."""
    return COST_STRESS_FILL_RATE_CAP.get(str(cost_stress), COST_STRESS_FILL_RATE_CAP["conservative"])


@dataclass
class FillResult:
    """Outcome of a simulated parent-order fill.

    ``filled`` is ``False`` for a reject / timeout / below-min partial — in which
    case ``reason`` names the cause and no position is created.
    """

    filled: bool
    filled_qty: int
    avg_fill_price: float
    slippage_bps_total: float
    notional: float
    commission: float = 0.0
    regulatory_fees: float = 0.0
    is_partial: bool = False
    reason: Optional[str] = None
    order_style: str = "market"
    liquidity_participation_frac: float = 0.0

    @property
    def total_fees(self) -> float:
        return self.commission + self.regulatory_fees


def _no_fill(reason: str, *, order_style: str) -> FillResult:
    return FillResult(
        filled=False, filled_qty=0, avg_fill_price=0.0, slippage_bps_total=0.0,
        notional=0.0, commission=0.0, regulatory_fees=0.0, is_partial=False,
        reason=reason, order_style=order_style, liquidity_participation_frac=0.0,
    )


def _fees(notional: float, *, commission_per_share: float, qty: int,
          regulatory_bps: float) -> tuple[float, float]:
    """``(commission, regulatory_fees)`` for a fill of ``qty`` at ``notional``."""
    commission = float(commission_per_share) * max(0, int(qty))
    regulatory = float(regulatory_bps) / 10_000.0 * max(0.0, float(notional))
    return round(commission, 6), round(regulatory, 6)


def simulate_market_fill(
    *,
    side: str,
    requested_qty: int,
    quote: QuoteSnapshot,
    liquidity_proxy_shares: Optional[float] = None,
    cost_stress: str = "conservative",
    adv_participation_frac: float = 0.001,
    min_order_notional: float = 0.0,
    commission_per_share: float = 0.0,
    regulatory_fee_bps: float = 0.0,
) -> FillResult:
    """Simulate a **market** parent-order fill.

    Fill price (buy) is ``quote.ask`` plus stress-scaled slippage. Full quantity
    when ``requested_qty <= liquidity_proxy_shares * fill_rate_cap``; otherwise a
    partial fill capped at that liquidity. A partial whose filled notional falls
    below ``min_order_notional`` becomes a no-fill with reason
    ``partial_below_min``.
    """
    if requested_qty <= 0:
        return _no_fill("zero_qty", order_style="market")

    side_l = side.lower()
    cap = stress_fill_rate_cap(cost_stress)
    if liquidity_proxy_shares is not None:
        usable = max(0, int(float(liquidity_proxy_shares) * cap))
        filled = min(int(requested_qty), usable)
        is_partial = filled < requested_qty
    else:
        filled = int(requested_qty)
        is_partial = False

    if filled <= 0:
        return _no_fill("no_liquidity", order_style="market")

    bp = slippage_bps(stress_level="base", adv_participation_frac=adv_participation_frac)
    bp *= stress_slippage_multiplier(cost_stress)
    bps_factor = bp / 10_000.0
    if side_l == "buy":
        price = quote.ask * (1.0 + bps_factor)
    else:
        price = quote.bid * (1.0 - bps_factor)
    price = round(price, 4)
    notional = filled * price

    # A partial fill too small to be worth a lot is rejected outright.
    if is_partial and notional < float(min_order_notional):
        return _no_fill("partial_below_min", order_style="market")

    commission, regulatory = _fees(
        notional, commission_per_share=commission_per_share,
        qty=filled, regulatory_bps=regulatory_fee_bps,
    )
    participation = (
        filled / float(liquidity_proxy_shares)
        if liquidity_proxy_shares
        else 0.0
    )
    return FillResult(
        filled=True, filled_qty=filled, avg_fill_price=price,
        slippage_bps_total=round(bp, 4), notional=round(notional, 4),
        commission=commission, regulatory_fees=regulatory,
        is_partial=is_partial, reason="partial_fill" if is_partial else None,
        order_style="market", liquidity_participation_frac=round(participation, 6),
    )


def _ask_path_from_bars(minute_bars: Optional[pd.DataFrame], scan_ts: Any) -> list[float]:
    """The forward minute-bar high path from ``scan_ts`` — proxy for the ask chasing."""
    if minute_bars is None or len(minute_bars) == 0 or "timestamp" not in minute_bars.columns:
        return []
    df = minute_bars.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    cut = pd.Timestamp(scan_ts)
    cut = cut.tz_localize("UTC") if cut.tzinfo is None else cut.tz_convert("UTC")
    fwd = df[df["timestamp"] >= cut].sort_values("timestamp")
    col = "high" if "high" in fwd.columns else ("close" if "close" in fwd.columns else None)
    if col is None:
        return []
    return [float(x) for x in fwd[col].tolist()]


def simulate_marketable_limit_fill(
    *,
    side: str,
    requested_qty: int,
    quote: QuoteSnapshot,
    marketable_limit_slippage_pct: float = 0.005,
    marketable_limit_timeout_seconds: int = 30,
    minute_bars: Optional[pd.DataFrame] = None,
    scan_ts: Any = None,
    liquidity_proxy_shares: Optional[float] = None,
    cost_stress: str = "conservative",
    adv_participation_frac: float = 0.001,
    min_order_notional: float = 0.0,
    commission_per_share: float = 0.0,
    regulatory_fee_bps: float = 0.0,
) -> FillResult:
    """Simulate a **marketable_limit** parent-order fill.

    Limit (buy) ``= quote.ask * (1 + marketable_limit_slippage_pct)``. The order
    fills if the quote does not chase past the limit within
    ``marketable_limit_timeout_seconds`` — modelled by walking the forward
    minute-bar highs from ``scan_ts`` over the timeout window. If the first
    in-window bar's high already exceeds the limit the quote has "run away" and
    the order times out with no position; otherwise it fills at the limit price
    (a conservative marketable-limit assumption — one full offset of slippage).
    """
    if requested_qty <= 0:
        return _no_fill("zero_qty", order_style="marketable_limit")

    side_l = side.lower()
    offset = float(marketable_limit_slippage_pct)
    if side_l == "buy":
        limit_price = round(quote.ask * (1.0 + offset), 4)
    else:
        limit_price = round(quote.bid * (1.0 - offset), 4)

    # Walk the forward minute path within the timeout window. The number of
    # bars considered is the timeout in whole minutes (>=1).
    timeout_minutes = max(1, int(round(float(marketable_limit_timeout_seconds) / 60.0)))
    path = _ask_path_from_bars(minute_bars, scan_ts)[:timeout_minutes]
    if path:
        # The quote chased past the limit within the window → no fill.
        if side_l == "buy" and min(path) > limit_price:
            return _no_fill("marketable_limit_timeout", order_style="marketable_limit")
        if side_l == "sell" and max(path) < limit_price:
            return _no_fill("marketable_limit_timeout", order_style="marketable_limit")

    cap = stress_fill_rate_cap(cost_stress)
    if liquidity_proxy_shares is not None:
        usable = max(0, int(float(liquidity_proxy_shares) * cap))
        filled = min(int(requested_qty), usable)
        is_partial = filled < requested_qty
    else:
        filled = int(requested_qty)
        is_partial = False

    if filled <= 0:
        return _no_fill("no_liquidity", order_style="marketable_limit")

    # Marketable-limit slippage in bps = the limit offset, scaled by stress.
    bp = offset * 10_000.0 * stress_slippage_multiplier(cost_stress)
    notional = filled * limit_price
    if is_partial and notional < float(min_order_notional):
        return _no_fill("partial_below_min", order_style="marketable_limit")

    commission, regulatory = _fees(
        notional, commission_per_share=commission_per_share,
        qty=filled, regulatory_bps=regulatory_fee_bps,
    )
    participation = (
        filled / float(liquidity_proxy_shares) if liquidity_proxy_shares else 0.0
    )
    return FillResult(
        filled=True, filled_qty=filled, avg_fill_price=limit_price,
        slippage_bps_total=round(bp, 4), notional=round(notional, 4),
        commission=commission, regulatory_fees=regulatory,
        is_partial=is_partial, reason="partial_fill" if is_partial else None,
        order_style="marketable_limit",
        liquidity_participation_frac=round(participation, 6),
    )


def simulate_fill(
    *,
    side: str,
    requested_qty: int,
    quote: QuoteSnapshot,
    available_liquidity: Optional[int] = None,
    stress_level: str = "conservative",
    adv_participation_frac: float = 0.001,
) -> FillResult:
    """Back-compat shim — a market fill keyed by the legacy parameter names.

    Pre-Phase-6 callers (and a few unit tests) used ``available_liquidity`` /
    ``stress_level`` and read ``FillResult.filled_qty`` / ``.is_partial``.
    Legacy semantics are preserved exactly: ``stress_level`` selects the cost
    model directly (not a stress multiplier), and exceeding / lacking liquidity
    yields a partial fill (``is_partial=True``) — including a 0-qty no-liquidity
    partial.
    """
    if requested_qty <= 0:
        return FillResult(
            filled=False, filled_qty=0, avg_fill_price=0.0, slippage_bps_total=0.0,
            notional=0.0, is_partial=False, order_style="market",
        )
    side_l = side.lower()
    if available_liquidity is not None and requested_qty > available_liquidity:
        filled = max(0, int(available_liquidity))
        is_partial = True
    else:
        filled = int(requested_qty)
        is_partial = False
    bp = slippage_bps(stress_level=stress_level, adv_participation_frac=adv_participation_frac)
    bps_factor = bp / 10_000.0
    if side_l == "buy":
        price = round(quote.ask * (1.0 + bps_factor), 4)
    else:
        price = round(quote.bid * (1.0 - bps_factor), 4)
    notional = filled * price
    return FillResult(
        filled=filled > 0, filled_qty=filled, avg_fill_price=price,
        slippage_bps_total=round(bp, 4), notional=round(notional, 4),
        is_partial=is_partial, reason="partial_fill" if is_partial else None,
        order_style="market",
    )
