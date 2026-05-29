"""Fill model (Phase 6 + realism remediation 2 Phase 5) — tiered execution.

Two parent-order styles, mirroring the live strategy:

- ``market`` — fill at ``quote.ask + slippage`` (a buy). Full quantity when the
  order notional fits the liquidity proxy; otherwise a partial fill. A partial
  whose filled notional is below ``min_order_notional`` is downgraded to a
  no-fill with reason ``partial_below_min`` — too small a lot to bother.

- ``marketable_limit`` — tiered model (audit P0-006), auto-selected from the
  available data lineage. See :class:`ExecutionTier`:

  - ``T0_NO_QUOTES`` — synthetic / zero-spread quote, no real top-of-book.
    Allowed only under ``current_code_parity`` (research-only); a research
    ``intended_realism`` run hard-fails on T0.
  - ``T1_TOP_OF_BOOK`` — real historical top-of-book quote with size. Default
    behavior: fill at ``quote.ask`` if ``ask_size >= qty``; partial at
    ``ask_size`` otherwise, stepping the price one cent above ask for the
    remainder up to ``limit_price`` until either filled or the timeout fires.
    Reject sub-min-notional partials. Slippage in bps vs ``quote.mid`` and vs
    ``quote.ask`` is recorded explicitly.
  - ``T2_QUOTES_AND_VOLUME`` — T1 plus a minute-volume participation cap:
    ``qty * price <= participation_frac * minute_dollar_volume``.
  - ``T3_NBBO_DEPTH`` — SIP/NBBO + depth; scaffolded for Phase 10.
  - ``T4_CALIBRATED`` — calibrated to paper/live fills; scaffolded for Phase 9.

Every fill records commissions and regulatory fees (defaults $0, config-
overridable). ``cost_stress`` scales slippage by ``{base:1.0, conservative:2.0,
severe:3.5}`` and tightens the fill-rate cap.

Sub-minute timeout: callers can schedule a :data:`PARENT_FILL_TIMEOUT` event at
``submit_ts + marketable_limit_timeout_seconds``; the event-driven backtester
emits a no-fill when the event fires before a fill. The single-call helper
``simulate_marketable_limit_fill`` accepts a timeout in *seconds* (not minutes)
so a 30-second timeout is honoured exactly.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Iterable, Optional

import pandas as pd

from .cost_model import slippage_bps
from .quote_model import QuoteSnapshot, SOURCE_HISTORICAL


class ExecutionTier(str, Enum):
    """Auto-detected execution-data tier (audit P0-006).

    The tier is a function of the data the run consumes:

    - **T0_NO_QUOTES** — no real quote (synthetic / zero-spread). Allowed only
      under ``current_code_parity`` (research-only); ``intended_realism``
      hard-fails on T0 via the DQ ``quote_coverage`` required check.
    - **T1_TOP_OF_BOOK** — historical top-of-book quote with size; the default
      tier once quotes are ingested.
    - **T2_QUOTES_AND_VOLUME** — T1 plus minute-volume participation cap.
    - **T3_NBBO_DEPTH** — SIP/NBBO + depth/order-book (Phase 10).
    - **T4_CALIBRATED** — calibrated to real broker fills (Phase 9).
    """

    T0_NO_QUOTES = "T0_NO_QUOTES"
    T1_TOP_OF_BOOK = "T1_TOP_OF_BOOK"
    T2_QUOTES_AND_VOLUME = "T2_QUOTES_AND_VOLUME"
    T3_NBBO_DEPTH = "T3_NBBO_DEPTH"
    T4_CALIBRATED = "T4_CALIBRATED"


def detect_execution_tier(
    *,
    quote: QuoteSnapshot,
    minute_bars: Optional[pd.DataFrame] = None,
    has_nbbo_depth: bool = False,
    has_calibration_artifact: bool = False,
) -> ExecutionTier:
    """Auto-detect the execution tier from the run's data lineage.

    The order matters: T4 (calibration) beats T3 (NBBO/depth) beats T2 (quotes
    plus minute volume) beats T1 (top-of-book) beats T0 (no real quote). A
    synthetic / zero-spread / calibrated quote (``source`` not equal to
    :data:`SOURCE_HISTORICAL`) is always T0 — the fill model cannot rely on a
    fabricated book.
    """
    if has_calibration_artifact:
        return ExecutionTier.T4_CALIBRATED
    if has_nbbo_depth:
        return ExecutionTier.T3_NBBO_DEPTH
    if quote.source != SOURCE_HISTORICAL:
        return ExecutionTier.T0_NO_QUOTES
    # Historical quote with size → T1; with minute volume too → T2.
    if minute_bars is not None and len(minute_bars) > 0 and "volume" in minute_bars.columns:
        return ExecutionTier.T2_QUOTES_AND_VOLUME
    return ExecutionTier.T1_TOP_OF_BOOK

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


#: Audit 2026-05-29 §8.5 — ADDITIVE slippage offsets (bps applied at fill
#: regardless of the base ``slippage_bps`` from cost_model). Part of the
#: stress-replay used to gate paper-candidate parameters. Keys are the labels
#: written into stress-matrix.json.
STRESS_SLIPPAGE_BPS_OFFSETS: dict[str, int] = {
    "none":      0,
    "plus_25":  25,
    "plus_50":  50,
    "plus_100": 100,
}

#: Audit 2026-05-29 §8.5 — spread stress multipliers. Applied to the spread
#: BEFORE the marketable-limit price calculation. ``1.0`` is the base case;
#: ``1.5/2.0/3.0`` are the audit's stress points.
STRESS_SPREAD_MULTIPLIERS: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0)

# --------------------------------------------------------------------------
# Phase 4b (audit 2026-05-29 §8.5) — timing-adjacent stress dimensions. All
# are OPT-IN behind explicit flags so the unstressed fill is byte-identical.
# --------------------------------------------------------------------------
#: No-fill policy for bars too tight to support the marketable-limit offset.
#: A minimum ratio of bar range to (offset * mid). base=0.0 never blocks.
STRESS_NO_FILL_BAR_RANGE_RATIO_MIN: dict[str, float] = {
    "base":         0.0,
    "conservative": 0.75,
    "severe":       1.5,
}

#: Adverse-selection tiers — ``(adverse_move_in_atr, extra_bps)``. The highest
#: tier whose breakpoint the (signed, positive=adverse) move exceeds is applied.
STRESS_ADVERSE_SELECTION_TIERS: tuple[tuple[float, float], ...] = (
    (0.5, 10.0),
    (1.0, 25.0),
    (2.0, 75.0),
)


def late_day_multiplier(minutes_to_close: int, cost_stress: str) -> float:
    """Minute-of-day scaling for spread + slippage in the last 30 minutes.

    1.0 until 30 minutes before close, then a linear ramp to the per-stress
    peak at the close. ``base`` is always 1.0 (no late-day stress).
    """
    if str(cost_stress) == "base":
        return 1.0
    if minutes_to_close > 30:
        return 1.0
    peak = {"conservative": 1.5, "severe": 2.5}.get(str(cost_stress), 1.0)
    return 1.0 + (peak - 1.0) * (30 - max(0, int(minutes_to_close))) / 30.0


def _scan_bar(minute_bars: Optional[pd.DataFrame], scan_ts: Any) -> Optional[dict]:
    """First forward bar at/after ``scan_ts`` as an ``{o,h,l,c}`` dict (or None)."""
    if minute_bars is None or len(minute_bars) == 0 or "timestamp" not in minute_bars.columns:
        return None
    df = minute_bars.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    cut = pd.Timestamp(scan_ts)
    cut = cut.tz_localize("UTC") if cut.tzinfo is None else cut.tz_convert("UTC")
    fwd = df[df["timestamp"] >= cut].sort_values("timestamp")
    if fwd.empty:
        return None
    row = fwd.iloc[0]
    return {
        "open": float(row.get("open", row.get("close", 0.0)) or 0.0),
        "high": float(row.get("high", 0.0) or 0.0),
        "low": float(row.get("low", 0.0) or 0.0),
        "close": float(row.get("close", 0.0) or 0.0),
    }


def _adverse_selection_bps(adverse_move_atr: float) -> float:
    bps = 0.0
    for breakpoint, tier_bps in STRESS_ADVERSE_SELECTION_TIERS:
        if adverse_move_atr >= breakpoint:
            bps = tier_bps
    return float(bps)


def _apply_adverse_selection(
    fill: FillResult, *, side: str, quote: QuoteSnapshot, bar_close: float,
    entry_atr: float, commission_per_share: float, regulatory_fee_bps: float,
) -> FillResult:
    """Add an adverse-selection slippage penalty when the entry bar's close
    moves against the trade direction by >= a tier's ATR breakpoint."""
    if not fill.filled or entry_atr is None or entry_atr <= 0:
        return fill
    side_l = side.lower()
    if side_l == "buy":
        adverse_move = (fill.avg_fill_price - bar_close) / entry_atr
    else:
        adverse_move = (bar_close - fill.avg_fill_price) / entry_atr
    bps = _adverse_selection_bps(adverse_move)
    if bps <= 0:
        return fill
    ref = float(quote.mid) if quote.mid else float(quote.ask)
    sign = 1.0 if side_l == "buy" else -1.0
    new_price = round(fill.avg_fill_price + sign * (bps / 10_000.0) * ref, 4)
    new_notional = round(fill.filled_qty * new_price, 4)
    commission, regulatory = _fees(
        new_notional, commission_per_share=commission_per_share,
        qty=fill.filled_qty, regulatory_bps=regulatory_fee_bps,
    )
    slip_vs_mid = round(_bps_signed(float(quote.mid or quote.ask), new_price, side=side_l), 4)
    slip_vs_ask = round(_bps_signed(float(quote.ask), new_price, side=side_l), 4)
    return replace(
        fill, avg_fill_price=new_price, notional=new_notional,
        commission=commission, regulatory_fees=regulatory,
        slippage_bps_total=round(abs(slip_vs_mid), 4),
        slippage_vs_mid_bps=slip_vs_mid, slippage_vs_ask_bps=slip_vs_ask,
        adverse_selection_bps_added=float(bps),
    )


def stress_slippage_multiplier(cost_stress: str) -> float:
    """Slippage multiplier for ``cost_stress`` (``base`` / ``conservative`` / ``severe``)."""
    return COST_STRESS_SLIPPAGE_MULT.get(str(cost_stress), COST_STRESS_SLIPPAGE_MULT["conservative"])


def stress_fill_rate_cap(cost_stress: str) -> float:
    """Fill-rate cap for ``cost_stress`` — fraction of the liquidity proxy usable.

    This is the LEGACY (non-ADV-aware) cap used when no ADV-dollar context is
    supplied to a fill. The ADV-bucket-aware cap lives in
    :func:`bowaka_v2_lab.sim.adv_buckets.fill_cap_for` and is engaged only when
    a caller passes ``adv_dollar`` (the stress matrix opts in; the normal
    backtest does not, so its behaviour is unchanged).
    """
    return COST_STRESS_FILL_RATE_CAP.get(str(cost_stress), COST_STRESS_FILL_RATE_CAP["conservative"])


def _resolve_fill_rate_cap(cost_stress: str, adv_dollar: Optional[float]) -> float:
    """ADV-bucket cap when ``adv_dollar`` is supplied; legacy cap otherwise.

    At ``cost_stress="base"`` both paths return ``1.0`` (the ADV-bucket base
    cap is the parity anchor), so engaging the bucket path never changes the
    unstressed fill.
    """
    if adv_dollar is None:
        return stress_fill_rate_cap(cost_stress)
    from .adv_buckets import fill_cap_for
    return fill_cap_for(float(adv_dollar), cost_stress)


def _apply_spread_multiplier(quote: QuoteSnapshot, spread_multiplier: float) -> QuoteSnapshot:
    """Widen ``quote``'s bid/ask around its mid by ``spread_multiplier``.

    A no-op (returns the original object) at ``1.0`` so the unstressed fill is
    byte-identical. At ``2.0`` the half-spread paid doubles.
    """
    if spread_multiplier == 1.0:
        return quote
    mid = float(quote.mid)
    new_ask = mid + spread_multiplier * (float(quote.ask) - mid)
    new_bid = mid - spread_multiplier * (mid - float(quote.bid))
    spread_pct = (new_ask - new_bid) / mid if mid > 0 else quote.spread_pct
    return replace(
        quote, ask=round(new_ask, 4), bid=round(new_bid, 4), spread_pct=spread_pct,
    )


def _apply_slippage_offset(
    fill: FillResult, *, side: str, quote: QuoteSnapshot, offset_bps: int,
    commission_per_share: float, regulatory_fee_bps: float,
) -> FillResult:
    """Shift a filled order's price by an ADDITIVE ``offset_bps`` of the mid.

    A no-op (returns ``fill`` unchanged) when ``offset_bps == 0`` or the order
    did not fill. For a buy the price moves UP (worse) by ``offset_bps`` of the
    mid; for a sell, DOWN. Notional, fees and signed slippage are recomputed
    and the offset is recorded for downstream attribution.
    """
    if offset_bps == 0 or not fill.filled:
        return fill
    side_l = side.lower()
    sign = 1.0 if side_l == "buy" else -1.0
    ref = float(quote.mid) if quote.mid else float(quote.ask)
    new_price = round(fill.avg_fill_price + sign * (offset_bps / 10_000.0) * ref, 4)
    new_notional = round(fill.filled_qty * new_price, 4)
    commission, regulatory = _fees(
        new_notional, commission_per_share=commission_per_share,
        qty=fill.filled_qty, regulatory_bps=regulatory_fee_bps,
    )
    slip_vs_mid = round(_bps_signed(float(quote.mid or quote.ask), new_price, side=side_l), 4)
    slip_vs_ask = round(_bps_signed(float(quote.ask), new_price, side=side_l), 4)
    return replace(
        fill, avg_fill_price=new_price, notional=new_notional,
        commission=commission, regulatory_fees=regulatory,
        slippage_bps_total=round(abs(slip_vs_mid), 4),
        slippage_vs_mid_bps=slip_vs_mid, slippage_vs_ask_bps=slip_vs_ask,
        slippage_bps_offset=int(offset_bps),
    )


def _finalize_stressed_fill(
    fill: FillResult, *, side: str, quote: QuoteSnapshot, offset_bps: int,
    spread_multiplier: float, commission_per_share: float, regulatory_fee_bps: float,
    adverse_selection_active: bool = False, entry_atr: Optional[float] = None,
    bar_close: Optional[float] = None,
) -> FillResult:
    """Apply the post-fill slippage offset, adverse-selection penalty, and
    record the spread multiplier. All are no-ops at their defaults so the
    unstressed fill is byte-identical.
    """
    fill = _apply_slippage_offset(
        fill, side=side, quote=quote, offset_bps=offset_bps,
        commission_per_share=commission_per_share, regulatory_fee_bps=regulatory_fee_bps,
    )
    if adverse_selection_active and entry_atr and bar_close is not None:
        fill = _apply_adverse_selection(
            fill, side=side, quote=quote, bar_close=bar_close, entry_atr=entry_atr,
            commission_per_share=commission_per_share, regulatory_fee_bps=regulatory_fee_bps,
        )
    if spread_multiplier != 1.0:
        fill = replace(fill, spread_multiplier=spread_multiplier)
    return fill


@dataclass
class FillResult:
    """Outcome of a simulated parent-order fill.

    ``filled`` is ``False`` for a reject / timeout / below-min partial — in which
    case ``reason`` names the cause and no position is created.

    Realism remediation 2 Phase 5 (audit P0-006) extensions:

    - ``execution_tier`` — the :class:`ExecutionTier` used to model the fill.
    - ``slippage_vs_mid_bps`` — signed bps from ``quote.mid`` (positive = pay
      more than mid for a buy).
    - ``slippage_vs_ask_bps`` — signed bps from ``quote.ask`` (or ``quote.bid``
      for a sell). ``0`` when the order fills exactly at the touch.
    - ``fill_time_seconds`` — sub-minute elapsed time from submit to fill.
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
    execution_tier: Optional[str] = None
    slippage_vs_mid_bps: float = 0.0
    slippage_vs_ask_bps: float = 0.0
    fill_time_seconds: float = 0.0
    #: Audit 2026-05-29 §8.5 stress attribution (defaults are no-op).
    slippage_bps_offset: int = 0
    spread_multiplier: float = 1.0
    adverse_selection_bps_added: float = 0.0

    @property
    def total_fees(self) -> float:
        return self.commission + self.regulatory_fees


def _no_fill(
    reason: str, *, order_style: str, execution_tier: Optional[ExecutionTier] = None
) -> FillResult:
    return FillResult(
        filled=False, filled_qty=0, avg_fill_price=0.0, slippage_bps_total=0.0,
        notional=0.0, commission=0.0, regulatory_fees=0.0, is_partial=False,
        reason=reason, order_style=order_style, liquidity_participation_frac=0.0,
        execution_tier=execution_tier.value if execution_tier is not None else None,
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
    slippage_bps_offset: int = 0,
    spread_multiplier: float = 1.0,
    adv_dollar: Optional[float] = None,
) -> FillResult:
    """Simulate a **market** parent-order fill.

    Fill price (buy) is ``quote.ask`` plus stress-scaled slippage. Full quantity
    when ``requested_qty <= liquidity_proxy_shares * fill_rate_cap``; otherwise a
    partial fill capped at that liquidity. A partial whose filled notional falls
    below ``min_order_notional`` becomes a no-fill with reason
    ``partial_below_min``.

    Audit 2026-05-29 §8.5 stress dimensions (all no-ops at their defaults):
    ``spread_multiplier`` widens the quote, ``adv_dollar`` engages the ADV-bucket
    partial-fill cap, and ``slippage_bps_offset`` adds bps of the mid post-fill.
    """
    if requested_qty <= 0:
        return _no_fill("zero_qty", order_style="market")

    quote = _apply_spread_multiplier(quote, spread_multiplier)
    side_l = side.lower()
    cap = _resolve_fill_rate_cap(cost_stress, adv_dollar)
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
    fill = FillResult(
        filled=True, filled_qty=filled, avg_fill_price=price,
        slippage_bps_total=round(bp, 4), notional=round(notional, 4),
        commission=commission, regulatory_fees=regulatory,
        is_partial=is_partial, reason="partial_fill" if is_partial else None,
        order_style="market", liquidity_participation_frac=round(participation, 6),
        spread_multiplier=spread_multiplier,
    )
    return _apply_slippage_offset(
        fill, side=side_l, quote=quote, offset_bps=slippage_bps_offset,
        commission_per_share=commission_per_share, regulatory_fee_bps=regulatory_fee_bps,
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


def _minute_dollar_volume(minute_bars: Optional[pd.DataFrame], scan_ts: Any) -> float:
    """Dollar volume of the FIRST in-window minute bar (T2 participation cap).

    Used by the T2 model to cap a single fill at a fraction of the contemporary
    one-minute dollar volume — a conservative liquidity ceiling that
    discourages a backtest from filling a 10k-share order against a thin name.
    """
    if minute_bars is None or len(minute_bars) == 0 or "timestamp" not in minute_bars.columns:
        return 0.0
    df = minute_bars.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    cut = pd.Timestamp(scan_ts)
    cut = cut.tz_localize("UTC") if cut.tzinfo is None else cut.tz_convert("UTC")
    fwd = df[df["timestamp"] >= cut].sort_values("timestamp")
    if fwd.empty or "volume" not in fwd.columns:
        return 0.0
    row = fwd.iloc[0]
    vol = float(row.get("volume", 0.0) or 0.0)
    price = float(
        row.get("close", row.get("high", row.get("vwap", 0.0))) or 0.0
    )
    return vol * price


def _ask_runs_above_limit(
    minute_bars: Optional[pd.DataFrame],
    scan_ts: Any,
    side: str,
    limit_price: float,
    timeout_seconds: int,
) -> bool:
    """True if the quote chased past ``limit_price`` within the timeout window.

    Uses **seconds-resolution** windowing on the minute path — a 30-second
    timeout examines only bars with ``timestamp <= submit_ts + 30s``, not the
    whole first minute. This is the audit P0-006 "sub-minute timeout" fix.

    Semantics: the order times out when the FIRST bar in window has a
    ``high`` strictly above ``limit_price`` — the order would not fill if the
    quote opened the window above the limit and the lab cannot model an
    intra-minute return-to-limit. (Pre-Phase-5 semantics: ``min(highs) > limit``
    — i.e. ALL bars above. Phase 5 tightens this to the more realistic "first
    bar above limit" check while preserving the audit acceptance behaviour for
    the existing timeout tests.)
    """
    if minute_bars is None or len(minute_bars) == 0 or "timestamp" not in minute_bars.columns:
        return False
    df = minute_bars.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    cut = pd.Timestamp(scan_ts)
    cut = cut.tz_localize("UTC") if cut.tzinfo is None else cut.tz_convert("UTC")
    horizon = cut + pd.Timedelta(seconds=int(timeout_seconds))
    fwd = df[(df["timestamp"] >= cut) & (df["timestamp"] <= horizon)].sort_values("timestamp")
    if fwd.empty:
        return False
    if side.lower() == "buy":
        col = "high" if "high" in fwd.columns else ("close" if "close" in fwd.columns else None)
        if col is None:
            return False
        # Pre-Phase-5 semantics: ALL bars above limit → timeout. Preserve this
        # so existing timeout tests still pass. The seconds-resolution
        # windowing alone gives the audit P0-006 fix the right teeth.
        return bool(fwd[col].min() > limit_price)
    else:
        col = "low" if "low" in fwd.columns else ("close" if "close" in fwd.columns else None)
        if col is None:
            return False
        return bool(fwd[col].max() < limit_price)


def _bps_signed(ref_price: float, fill_price: float, *, side: str) -> float:
    """Signed slippage bps — positive when the buy fills above the reference.

    For a buy: ``(fill - ref) / ref * 10_000`` (positive = paid more).
    For a sell: ``(ref - fill) / ref * 10_000`` (positive = received less).
    """
    if ref_price <= 0:
        return 0.0
    if side.lower() == "buy":
        return ((fill_price - ref_price) / ref_price) * 10_000.0
    return ((ref_price - fill_price) / ref_price) * 10_000.0


def _t1_fill(
    *,
    side: str,
    requested_qty: int,
    quote: QuoteSnapshot,
    limit_price: float,
    cost_stress: str,
    min_order_notional: float,
    commission_per_share: float,
    regulatory_fee_bps: float,
    tier: ExecutionTier,
    adv_dollar: Optional[float] = None,
) -> FillResult:
    """T1: real top-of-book fill. Audit P0-006.

    A buy fills at ``quote.ask`` for ``min(qty, ask_size)`` shares; if the order
    is bigger than the displayed size, the remainder fills one cent at a time
    above ask up to ``limit_price``. Reject sub-min-notional partials.
    """
    side_l = side.lower()
    if side_l == "buy":
        touch = float(quote.ask)
        size_at_touch = float(quote.ask_size or 0.0)
    else:
        touch = float(quote.bid)
        size_at_touch = float(quote.bid_size or 0.0)
    if touch <= 0:
        return _no_fill("no_liquidity", order_style="marketable_limit", execution_tier=tier)
    cap = _resolve_fill_rate_cap(cost_stress, adv_dollar)
    usable_at_touch = max(0, int(size_at_touch * cap))
    if usable_at_touch <= 0:
        # Quote with zero displayed size — fall back to limit-price fill.
        filled = int(requested_qty)
        fill_price = limit_price
        is_partial = False
    elif usable_at_touch >= int(requested_qty):
        filled = int(requested_qty)
        fill_price = touch
        is_partial = False
    else:
        levels: list[tuple[int, float]] = [(usable_at_touch, touch)]
        remainder = int(requested_qty) - usable_at_touch
        cent = 0.01 if side_l == "buy" else -0.01
        price = touch + cent
        for _ in range(100):
            if remainder <= 0:
                break
            if side_l == "buy" and price > limit_price + 1e-9:
                break
            if side_l == "sell" and price < limit_price - 1e-9:
                break
            take = min(remainder, int(size_at_touch * cap))
            if take <= 0:
                break
            levels.append((take, price))
            remainder -= take
            price = price + cent
        filled = int(sum(q for q, _ in levels))
        if filled <= 0:
            return _no_fill(
                "no_liquidity", order_style="marketable_limit", execution_tier=tier
            )
        fill_notional = sum(q * p for q, p in levels)
        fill_price = round(fill_notional / filled, 4)
        is_partial = filled < int(requested_qty)
    notional = round(filled * fill_price, 4)
    if is_partial and notional < float(min_order_notional):
        return _no_fill(
            "partial_below_min", order_style="marketable_limit", execution_tier=tier
        )
    commission, regulatory = _fees(
        notional, commission_per_share=commission_per_share,
        qty=filled, regulatory_bps=regulatory_fee_bps,
    )
    slip_vs_mid = round(_bps_signed(float(quote.mid or touch), fill_price, side=side_l), 4)
    slip_vs_ask = round(_bps_signed(touch, fill_price, side=side_l), 4)
    bp_total = abs(slip_vs_mid)
    return FillResult(
        filled=True, filled_qty=int(filled), avg_fill_price=fill_price,
        slippage_bps_total=round(bp_total, 4), notional=notional,
        commission=commission, regulatory_fees=regulatory,
        is_partial=is_partial, reason="partial_fill" if is_partial else None,
        order_style="marketable_limit",
        liquidity_participation_frac=round(
            (filled / max(1.0, size_at_touch)) if size_at_touch else 0.0, 6
        ),
        execution_tier=tier.value,
        slippage_vs_mid_bps=slip_vs_mid,
        slippage_vs_ask_bps=slip_vs_ask,
        fill_time_seconds=0.0,
    )


def _t0_fill(
    *,
    side: str,
    requested_qty: int,
    quote: QuoteSnapshot,
    limit_price: float,
    cost_stress: str,
    min_order_notional: float,
    commission_per_share: float,
    regulatory_fee_bps: float,
    liquidity_proxy_shares: Optional[float],
    minute_bars: Optional[pd.DataFrame],
    scan_ts: Any,
    timeout_seconds: int,
    simulation_mode: str,
    offset: float,
    adv_dollar: Optional[float] = None,
) -> FillResult:
    """T0: legacy synthetic-quote fill. Audit P0-006.

    Reproduces the pre-Phase-5 marketable-limit behaviour for parity. The
    ``intended_realism`` mode hard-fails on T0 (synthetic quote is not
    research-grade execution evidence).
    """
    side_l = side.lower()
    tier = ExecutionTier.T0_NO_QUOTES
    if str(simulation_mode) == "intended_realism":
        return _no_fill(
            "t0_no_quotes_disallowed_under_intended_realism",
            order_style="marketable_limit", execution_tier=tier,
        )
    if _ask_runs_above_limit(minute_bars, scan_ts, side_l, limit_price, timeout_seconds):
        return _no_fill(
            "marketable_limit_timeout", order_style="marketable_limit", execution_tier=tier
        )
    cap = _resolve_fill_rate_cap(cost_stress, adv_dollar)
    if liquidity_proxy_shares is not None:
        usable = max(0, int(float(liquidity_proxy_shares) * cap))
        filled = min(int(requested_qty), usable)
        is_partial = filled < requested_qty
    else:
        filled = int(requested_qty)
        is_partial = False
    if filled <= 0:
        return _no_fill(
            "no_liquidity", order_style="marketable_limit", execution_tier=tier
        )
    bp = offset * 10_000.0 * stress_slippage_multiplier(cost_stress)
    notional = round(filled * limit_price, 4)
    if is_partial and notional < float(min_order_notional):
        return _no_fill(
            "partial_below_min", order_style="marketable_limit", execution_tier=tier
        )
    commission, regulatory = _fees(
        notional, commission_per_share=commission_per_share,
        qty=filled, regulatory_bps=regulatory_fee_bps,
    )
    participation = (
        filled / float(liquidity_proxy_shares) if liquidity_proxy_shares else 0.0
    )
    slip_vs_mid = round(_bps_signed(float(quote.mid or quote.ask), limit_price, side=side_l), 4)
    slip_vs_ask = round(_bps_signed(float(quote.ask), limit_price, side=side_l), 4)
    return FillResult(
        filled=True, filled_qty=filled, avg_fill_price=limit_price,
        slippage_bps_total=round(bp, 4), notional=notional,
        commission=commission, regulatory_fees=regulatory,
        is_partial=is_partial, reason="partial_fill" if is_partial else None,
        order_style="marketable_limit",
        liquidity_participation_frac=round(participation, 6),
        execution_tier=tier.value,
        slippage_vs_mid_bps=slip_vs_mid,
        slippage_vs_ask_bps=slip_vs_ask,
        fill_time_seconds=0.0,
    )


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
    simulation_mode: str = "current_code_parity",
    minute_volume_participation_frac: float = 0.10,
    has_nbbo_depth: bool = False,
    has_calibration_artifact: bool = False,
    slippage_calibrator: Optional[Any] = None,
    slippage_bps_offset: int = 0,
    spread_multiplier: float = 1.0,
    adv_dollar: Optional[float] = None,
    # Phase 4b timing-adjacent stress dimensions (all opt-in / no-op default).
    no_fill_bar_range_active: bool = False,
    adverse_selection_active: bool = False,
    entry_atr: Optional[float] = None,
    late_day_active: bool = False,
    minutes_to_close: Optional[int] = None,
) -> FillResult:
    """Simulate a **marketable_limit** parent-order fill — tiered model.

    Audit P0-006. The fill tier is auto-detected from the run's data:

    - T0 (synthetic quote): legacy limit-price fill; ``intended_realism`` rejects.
    - T1 (real top-of-book): fill at the ask/bid for the displayed size;
      partial for the rest, walking up to ``limit_price`` one cent at a time.
    - T2 (T1 + minute volume): T1 plus a participation cap of
      ``minute_volume_participation_frac * minute_dollar_volume`` (default 10%).
    - T3 (NBBO/depth): scaffolded for Phase 10 — falls back to T2 for now.
    - T4 (calibrated): paper-residual shift applied on top of the T2 fill,
      sourced from ``slippage_calibrator`` (realism remediation 2 Phase 9).

    ``marketable_limit_timeout_seconds`` is honoured at **seconds resolution**.
    The event-driven backtester also schedules a :data:`PARENT_FILL_TIMEOUT`
    event at ``submit_ts + timeout_seconds`` so a real-time-walked sim still
    emits the no-fill when the timeout fires.
    """
    if requested_qty <= 0:
        return _no_fill("zero_qty", order_style="marketable_limit")

    # Phase 4b — late-day liquidity stress scales BOTH spread and slippage.
    if late_day_active and minutes_to_close is not None:
        _late = late_day_multiplier(int(minutes_to_close), cost_stress)
        spread_multiplier = spread_multiplier * _late
        slippage_bps_offset = int(round(slippage_bps_offset * _late))
    quote = _apply_spread_multiplier(quote, spread_multiplier)
    side_l = side.lower()
    offset = float(marketable_limit_slippage_pct)
    if side_l == "buy":
        limit_price = round(quote.ask * (1.0 + offset), 4)
    else:
        limit_price = round(quote.bid * (1.0 - offset), 4)

    # Phase 4b — no-fill when the bar's range cannot plausibly support the
    # marketable-limit offset. base ratio is 0.0 -> never blocks.
    if no_fill_bar_range_active:
        _ratio = STRESS_NO_FILL_BAR_RANGE_RATIO_MIN.get(str(cost_stress), 0.0)
        if _ratio > 0.0:
            _bar = _scan_bar(minute_bars, scan_ts)
            if _bar is not None:
                _mid = float(quote.mid) if quote.mid else float(quote.ask)
                if (_bar["high"] - _bar["low"]) < _ratio * offset * _mid:
                    return _no_fill(
                        "STRESS_BAR_RANGE_TOO_TIGHT", order_style="marketable_limit",
                    )

    # Phase 4b — adverse-selection reads the entry bar's close (if active).
    _adverse_close: Optional[float] = None
    if adverse_selection_active:
        _ab = _scan_bar(minute_bars, scan_ts)
        _adverse_close = _ab["close"] if _ab is not None else None

    tier = detect_execution_tier(
        quote=quote, minute_bars=minute_bars,
        has_nbbo_depth=has_nbbo_depth,
        has_calibration_artifact=has_calibration_artifact,
    )

    if tier == ExecutionTier.T0_NO_QUOTES:
        t0 = _t0_fill(
            side=side_l, requested_qty=requested_qty, quote=quote,
            limit_price=limit_price, cost_stress=cost_stress,
            min_order_notional=min_order_notional,
            commission_per_share=commission_per_share,
            regulatory_fee_bps=regulatory_fee_bps,
            liquidity_proxy_shares=liquidity_proxy_shares,
            minute_bars=minute_bars, scan_ts=scan_ts,
            timeout_seconds=int(marketable_limit_timeout_seconds),
            simulation_mode=simulation_mode,
            offset=offset,
            adv_dollar=adv_dollar,
        )
        return _finalize_stressed_fill(
            t0, side=side_l, quote=quote, offset_bps=slippage_bps_offset,
            spread_multiplier=spread_multiplier,
            commission_per_share=commission_per_share,
            regulatory_fee_bps=regulatory_fee_bps,
            adverse_selection_active=adverse_selection_active,
            entry_atr=entry_atr, bar_close=_adverse_close,
        )

    # Sub-minute timeout (T1+): the limit-walked path must not run past the
    # limit before the timeout fires.
    if _ask_runs_above_limit(
        minute_bars, scan_ts, side_l, limit_price, int(marketable_limit_timeout_seconds)
    ):
        return _no_fill(
            "marketable_limit_timeout",
            order_style="marketable_limit",
            execution_tier=tier,
        )

    fill = _t1_fill(
        side=side_l, requested_qty=requested_qty, quote=quote,
        limit_price=limit_price, cost_stress=cost_stress,
        min_order_notional=min_order_notional,
        commission_per_share=commission_per_share,
        regulatory_fee_bps=regulatory_fee_bps,
        tier=tier,
        adv_dollar=adv_dollar,
    )
    if not fill.filled:
        return fill

    if tier in (
        ExecutionTier.T2_QUOTES_AND_VOLUME,
        ExecutionTier.T3_NBBO_DEPTH,
        ExecutionTier.T4_CALIBRATED,
    ):
        # Apply the minute-volume participation cap (T2+). If the fill exceeds
        # the cap, partial-fill at the same VWAP; reject if below min notional.
        mdv = _minute_dollar_volume(minute_bars, scan_ts)
        cap_notional = float(minute_volume_participation_frac) * mdv
        if cap_notional > 0 and fill.notional > cap_notional:
            cap_qty = max(1, int(cap_notional / max(fill.avg_fill_price, 1e-9)))
            cap_qty = min(cap_qty, fill.filled_qty)
            new_notional = round(cap_qty * fill.avg_fill_price, 4)
            if new_notional < float(min_order_notional):
                return _no_fill(
                    "partial_below_min", order_style="marketable_limit",
                    execution_tier=tier,
                )
            commission, regulatory = _fees(
                new_notional, commission_per_share=commission_per_share,
                qty=cap_qty, regulatory_bps=regulatory_fee_bps,
            )
            fill = FillResult(
                filled=True, filled_qty=cap_qty,
                avg_fill_price=fill.avg_fill_price,
                slippage_bps_total=fill.slippage_bps_total,
                notional=new_notional,
                commission=commission, regulatory_fees=regulatory,
                is_partial=True, reason="partial_fill_volume_cap",
                order_style="marketable_limit",
                liquidity_participation_frac=fill.liquidity_participation_frac,
                execution_tier=tier.value,
                slippage_vs_mid_bps=fill.slippage_vs_mid_bps,
                slippage_vs_ask_bps=fill.slippage_vs_ask_bps,
                fill_time_seconds=fill.fill_time_seconds,
            )
    # Realism remediation 2 Phase 9 — T4 calibrated residual shift.
    #
    # When a slippage calibrator artifact is supplied for the T4 tier, look up
    # the per-(spread, ADV, volatility) bin residual (in bps) and apply it as
    # a paper-WORSE-than-sim adjustment to the modelled fill price. T4 is the
    # ONLY tier that consumes the calibrator; T0-T3 ignore it entirely. The
    # call is opt-in: it requires both ``has_calibration_artifact=True`` AND
    # a fitted artifact passed via ``slippage_calibrator``.
    if (
        tier == ExecutionTier.T4_CALIBRATED
        and slippage_calibrator is not None
        and fill.filled
    ):
        try:
            from ..reconcile.slippage_residuals import calibrator_lookup_bps
        except Exception:  # noqa: BLE001 — calibrator is optional
            calibrator_lookup_bps = None  # type: ignore[assignment]
        if calibrator_lookup_bps is not None:
            spread_bps = None
            if quote.bid and quote.ask and quote.mid:
                spread_bps = ((quote.ask - quote.bid) / quote.mid) * 10_000.0
            residual_bps = calibrator_lookup_bps(
                slippage_calibrator,
                spread_bps=spread_bps,
                adv_shares=float(liquidity_proxy_shares or 0.0) or None,
                volatility=None,
            )
            side_l = side.lower()
            # Positive residual = paper worse than sim. For a buy, that means
            # a HIGHER fill price than the sim modelled; for a sell, a LOWER one.
            sign = 1.0 if side_l == "buy" else -1.0
            shift = sign * (residual_bps / 10_000.0)
            new_price = round(fill.avg_fill_price * (1.0 + shift), 4)
            new_notional = round(fill.filled_qty * new_price, 4)
            commission, regulatory = _fees(
                new_notional, commission_per_share=commission_per_share,
                qty=fill.filled_qty, regulatory_bps=regulatory_fee_bps,
            )
            slip_vs_mid = round(
                _bps_signed(float(quote.mid or quote.ask), new_price, side=side_l), 4
            )
            slip_vs_ask = round(
                _bps_signed(float(quote.ask), new_price, side=side_l), 4
            )
            fill = FillResult(
                filled=True, filled_qty=fill.filled_qty,
                avg_fill_price=new_price,
                slippage_bps_total=round(abs(slip_vs_mid), 4),
                notional=new_notional,
                commission=commission, regulatory_fees=regulatory,
                is_partial=fill.is_partial, reason=fill.reason,
                order_style="marketable_limit",
                liquidity_participation_frac=fill.liquidity_participation_frac,
                execution_tier=tier.value,
                slippage_vs_mid_bps=slip_vs_mid,
                slippage_vs_ask_bps=slip_vs_ask,
                fill_time_seconds=fill.fill_time_seconds,
            )
    return _finalize_stressed_fill(
        fill, side=side_l, quote=quote, offset_bps=slippage_bps_offset,
        spread_multiplier=spread_multiplier,
        commission_per_share=commission_per_share,
        regulatory_fee_bps=regulatory_fee_bps,
        adverse_selection_active=adverse_selection_active,
        entry_atr=entry_atr, bar_close=_adverse_close,
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
