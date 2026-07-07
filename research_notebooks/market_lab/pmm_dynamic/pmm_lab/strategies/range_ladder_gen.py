"""Generative ladder construction for the range_ladder strategy.

Pure functions only — no I/O, no engine imports — so every constraint is
unit-testable in isolation.

The search space never exposes raw rung prices or raw weight vectors to
Optuna. Instead a fixed-dimension generative description (rung counts, band
placement, spacing curvature, weight tilt) is sampled, and every sample is
converted to a concrete ladder here. All prices are % offsets from an ANCHOR
(median of the last 3 train-window closes) and become absolute prices only
at build/export time.

Ordering convention (used consistently across kernel, export, and tests):
index 0 is the rung NEAREST the anchor on both sides. That means buys are
in DESCENDING price order and sells in ASCENDING price order — which is
exactly the live YAML convention (`buy_prices` highest→lowest,
`sell_prices` lowest→highest).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np

# Weight floor applied after max-normalisation (mirrors ladder_lab's
# min_weight_frac default).
DEFAULT_MIN_WEIGHT_FRAC = 0.10

# Dead-zone fee-floor multiplier: buy_near + sell_near >= FLOOR_MULT * (2*fee).
# Mirrors ladder_lab's min_rung_gap_mult=2.0.
DEAD_ZONE_FEE_MULT = 2.0


@dataclass(frozen=True)
class RungSet:
    """A concrete ladder: absolute tick-quantized prices + raw weights.

    buys[0] / sells[0] are the rungs nearest the anchor (see module
    docstring for the ordering convention).
    """

    buys: np.ndarray       # float64, descending (nearest → farthest below anchor)
    sells: np.ndarray      # float64, ascending (nearest → farthest above anchor)
    buy_weights: np.ndarray
    sell_weights: np.ndarray


def _param(params: Any, name: str):
    """Read a generative parameter from a mapping or an attribute object."""
    if isinstance(params, dict):
        return params[name]
    return getattr(params, name)


def quantize_price(price: float, price_tick: float, side: str) -> float:
    """Quantize a price to the tick grid.

    Buys round DOWN and sells round UP so quantization can only widen the
    dead zone, never narrow it. Decimal arithmetic avoids float-tick drift
    (same approach as pmm_lab.config.exchange_rules.round_price).
    """
    tick = Decimal(str(price_tick))
    p = Decimal(str(price))
    rounding = ROUND_DOWN if side == "buy" else ROUND_UP
    return float((p / tick).to_integral_value(rounding=rounding) * tick)


def shape_weights(n: int, k: float, min_weight_frac: float = DEFAULT_MIN_WEIGHT_FRAC) -> np.ndarray:
    """Exponential tilt weights: w_i = exp(-k * i/(n-1)), max-normalized, floored.

    k > 0 front-loads the rung nearest price; k < 0 loads the deep rungs.
    """
    if n < 2:
        raise ValueError(f"shape_weights requires n >= 2, got {n}")
    x = np.arange(n, dtype=np.float64) / (n - 1)
    w = np.exp(-k * x)
    w = w / w.max()
    return np.maximum(w, min_weight_frac)


def build_rungs(anchor: float, params: Any, price_tick: float) -> RungSet:
    """Build a concrete ladder from generative params at the given anchor.

    Parameters
    ----------
    anchor : float
        Reference price (median of last 3 train closes at tune time; the
        deploy-time median-3 close at export time).
    params : mapping or object
        Must provide n_buy, n_sell, buy_near_pct, buy_far_pct, sell_near_pct,
        sell_far_pct, buy_gamma, sell_gamma, k_buy, k_sell and optionally
        min_weight_frac.
    price_tick : float
        Pair tick size; buys round down, sells round up.

    Returns
    -------
    RungSet
        Quantized prices + raw (max-normalized, floored) weights.
    """
    if anchor <= 0:
        raise ValueError(f"anchor must be positive, got {anchor}")
    n_buy = int(_param(params, "n_buy"))
    n_sell = int(_param(params, "n_sell"))
    if n_buy < 2 or n_sell < 2:
        raise ValueError(
            f"rung counts must be >= 2 (search space minimum is 3); "
            f"got n_buy={n_buy}, n_sell={n_sell}"
        )
    try:
        mwf = float(_param(params, "min_weight_frac"))
    except (KeyError, AttributeError):
        mwf = DEFAULT_MIN_WEIGHT_FRAC

    def _offsets(n: int, near: float, far: float, gamma: float) -> np.ndarray:
        frac = (np.arange(n, dtype=np.float64) / (n - 1)) ** gamma
        return near + (far - near) * frac

    buy_off = _offsets(
        n_buy,
        float(_param(params, "buy_near_pct")),
        float(_param(params, "buy_far_pct")),
        float(_param(params, "buy_gamma")),
    )
    sell_off = _offsets(
        n_sell,
        float(_param(params, "sell_near_pct")),
        float(_param(params, "sell_far_pct")),
        float(_param(params, "sell_gamma")),
    )

    buys = np.array(
        [quantize_price(anchor * (1.0 - o), price_tick, "buy") for o in buy_off],
        dtype=np.float64,
    )
    sells = np.array(
        [quantize_price(anchor * (1.0 + o), price_tick, "sell") for o in sell_off],
        dtype=np.float64,
    )

    bw = shape_weights(n_buy, float(_param(params, "k_buy")), mwf)
    sw = shape_weights(n_sell, float(_param(params, "k_sell")), mwf)

    return RungSet(buys=buys, sells=sells, buy_weights=bw, sell_weights=sw)


def _avg_adjacent_gap_frac(prices: np.ndarray) -> float:
    """Mean adjacent gap as a fraction of the lower rung price."""
    p = np.sort(np.asarray(prices, dtype=np.float64))
    if len(p) < 2:
        return float("inf")
    gaps = (p[1:] - p[:-1]) / p[:-1]
    return float(np.mean(gaps))


def validate_rungs(
    rungs: RungSet,
    *,
    anchor: float,
    fee: float,
    price_tick: float,
    min_order_quote: float,
    fund: float,
    quote_frac: float,
    buy_near_pct: Optional[float] = None,
    buy_far_pct: Optional[float] = None,
    sell_near_pct: Optional[float] = None,
    sell_far_pct: Optional[float] = None,
) -> Tuple[bool, Optional[str]]:
    """Apply the Phase A hard constraints to a built ladder.

    Constraints (invalid → (False, reason); the objective wrapper translates
    to optuna.TrialPruned):

    1. far > near strict on each side, and adjacent rungs separated by at
       least one price tick after quantization.
    2. Dead-zone fee floor: buy_near + sell_near >= 2 * (2 * fee).
    3. Adjacent-gap fee floor: average adjacent gap on each side >= 2 * fee.
    4. Budget/compression feasibility: the smallest normalized rung weight
       on each side must fund at least min_order_quote of notional, else the
       live controller would silently compress rungs away.
    5. After quantization, max(buys) < min(sells) strictly.

    The near/far kwargs are supplied for generative ladders (constraint 2 is
    then checked on the raw offsets, matching the spec); for literal ladders
    they are None and the dead zone is checked from the quantized prices.
    """
    buys = np.asarray(rungs.buys, dtype=np.float64)
    sells = np.asarray(rungs.sells, dtype=np.float64)
    bw = np.asarray(rungs.buy_weights, dtype=np.float64)
    sw = np.asarray(rungs.sell_weights, dtype=np.float64)
    fee = float(fee)
    tick_eps = price_tick * (1.0 - 1e-9)

    # --- Constraint 1: band ordering + tick separation ---
    if buy_near_pct is not None and buy_far_pct is not None:
        if not (buy_far_pct > buy_near_pct):
            return False, (
                f"buy_far_pct ({buy_far_pct:.6f}) must be > buy_near_pct ({buy_near_pct:.6f})"
            )
    if sell_near_pct is not None and sell_far_pct is not None:
        if not (sell_far_pct > sell_near_pct):
            return False, (
                f"sell_far_pct ({sell_far_pct:.6f}) must be > sell_near_pct ({sell_near_pct:.6f})"
            )
    for label, arr in (("buy", buys), ("sell", sells)):
        s = np.sort(arr)
        if len(s) >= 2 and np.min(np.diff(s)) < tick_eps:
            return False, (
                f"adjacent {label} rungs closer than one price tick "
                f"({price_tick}) after quantization"
            )

    # --- Constraint 2: dead-zone fee floor ---
    floor = DEAD_ZONE_FEE_MULT * (2.0 * fee)
    if buy_near_pct is not None and sell_near_pct is not None:
        dead_zone = buy_near_pct + sell_near_pct
    else:
        dead_zone = (float(np.min(sells)) - float(np.max(buys))) / anchor
    if dead_zone < floor:
        return False, (
            f"dead zone {dead_zone:.6f} below fee floor {floor:.6f} "
            f"(= {DEAD_ZONE_FEE_MULT} * 2 * fee, fee={fee})"
        )

    # --- Constraint 3: adjacent-gap fee floor per side ---
    gap_floor = 2.0 * fee
    for label, arr in (("buy", buys), ("sell", sells)):
        avg_gap = _avg_adjacent_gap_frac(arr)
        if avg_gap < gap_floor:
            return False, (
                f"average adjacent {label} gap {avg_gap:.6f} below "
                f"fee floor {gap_floor:.6f} (= 2 * fee)"
            )

    # --- Constraint 4: budget/compression feasibility ---
    buy_capital = fund * quote_frac
    sell_capital = fund * (1.0 - quote_frac)
    min_buy_notional = float(bw.min() / bw.sum()) * buy_capital
    if min_buy_notional < min_order_quote:
        return False, (
            f"smallest buy rung notional {min_buy_notional:.4f} < "
            f"min_order_quote {min_order_quote} (fund={fund}, quote_frac={quote_frac})"
        )
    min_sell_notional = float(sw.min() / sw.sum()) * sell_capital
    if min_sell_notional < min_order_quote:
        return False, (
            f"smallest sell rung notional {min_sell_notional:.4f} < "
            f"min_order_quote {min_order_quote} (fund={fund}, quote_frac={quote_frac})"
        )

    # --- Constraint 5: no cross-side overlap after quantization ---
    if not (float(np.max(buys)) < float(np.min(sells))):
        return False, (
            f"cross-side overlap after quantization: max(buys)={np.max(buys)} "
            f">= min(sells)={np.min(sells)}"
        )

    return True, None


# ----------------------------------------------------------------------
# Incumbent approximation — fit generative params to a literal ladder
# ----------------------------------------------------------------------

def fit_generative_to_ladder(
    buy_prices: Sequence[float],
    buy_weights: Sequence[float],
    sell_prices: Sequence[float],
    sell_weights: Sequence[float],
    anchor: Optional[float] = None,
    min_weight_frac: float = DEFAULT_MIN_WEIGHT_FRAC,
) -> Dict[str, float]:
    """Least-squares fit of generative params to a literal (live) ladder.

    Used to `study.enqueue_trial()` a generative approximation of a live
    incumbent config — raw rung prices are not in the search space, so the
    incumbent itself cannot be an Optuna trial.

    The fit is exact for arithmetic rung spacing (gamma=1) and geometric
    weight progressions (pure exponential tilt); the live DASH/SUN ladders
    round-trip within <5% (unit-tested).

    Parameters
    ----------
    anchor : float, optional
        Anchor at which offsets are measured. Defaults to the midpoint of
        the nearest buy and nearest sell rung. The returned dict includes
        the anchor used so callers can round-trip.

    Returns
    -------
    dict
        n_buy, n_sell, buy_near_pct, buy_far_pct, sell_near_pct,
        sell_far_pct, buy_gamma, sell_gamma, k_buy, k_sell, anchor.
    """
    buys = np.sort(np.asarray(buy_prices, dtype=np.float64))[::-1]   # nearest first
    sells = np.sort(np.asarray(sell_prices, dtype=np.float64))       # nearest first
    bw = np.asarray(buy_weights, dtype=np.float64)
    sw = np.asarray(sell_weights, dtype=np.float64)
    if len(buys) != len(bw) or len(sells) != len(sw):
        raise ValueError("price and weight vectors must have matching lengths")
    if len(buys) < 2 or len(sells) < 2:
        raise ValueError("need at least 2 rungs per side to fit")

    if anchor is None:
        anchor = 0.5 * (float(buys[0]) + float(sells[0]))

    def _fit_side(prices: np.ndarray, weights: np.ndarray, side: str):
        n = len(prices)
        if side == "buy":
            offs = (anchor - prices) / anchor
        else:
            offs = (prices - anchor) / anchor
        near = float(offs[0])
        far = float(offs[-1])
        if not (far > near > 0):
            raise ValueError(
                f"{side} offsets are not monotone away from anchor "
                f"(near={near:.6f}, far={far:.6f}, anchor={anchor})"
            )
        # gamma: ln(frac_i) = gamma * ln(x_i) on interior points
        x = np.arange(n, dtype=np.float64) / (n - 1)
        frac = (offs - near) / (far - near)
        interior = (frac > 0) & (frac < 1) & (x > 0) & (x < 1)
        if interior.sum() >= 1:
            gamma = float(
                np.sum(np.log(frac[interior]) * np.log(x[interior]))
                / np.sum(np.log(x[interior]) ** 2)
            )
        else:
            gamma = 1.0
        # k: generator weights are exp(-k*x) up to normalisation → fit slope
        # of ln(w) on x (weights assumed above the floor; live ladders are).
        lw = np.log(weights / weights.max())
        slope = float(np.polyfit(x, lw, 1)[0])
        k = -slope
        return near, far, gamma, k

    b_near, b_far, b_gamma, b_k = _fit_side(buys, bw, "buy")
    s_near, s_far, s_gamma, s_k = _fit_side(sells, sw, "sell")

    def _clamp(v, lo, hi):
        return float(min(max(v, lo), hi))

    # Clamp into the Phase A search-space ranges so the fitted params can be
    # enqueued as an Optuna trial without out-of-distribution warnings.
    return {
        "n_buy": int(len(buys)),
        "n_sell": int(len(sells)),
        "buy_near_pct": _clamp(b_near, 0.005, 0.10),
        "buy_far_pct": _clamp(b_far, 0.03, 0.45),
        "sell_near_pct": _clamp(s_near, 0.005, 0.10),
        "sell_far_pct": _clamp(s_far, 0.03, 0.45),
        "buy_gamma": _clamp(b_gamma, 0.5, 2.0),
        "sell_gamma": _clamp(s_gamma, 0.5, 2.0),
        "k_buy": _clamp(b_k, -2.0, 4.0),
        "k_sell": _clamp(s_k, -2.0, 4.0),
        "anchor": float(anchor),
    }


def apply_ladder_overlay(
    rungs: RungSet,
    *,
    buy_shift_pct: float = 0.0,
    sell_shift_pct: float = 0.0,
    buy_stretch: float = 1.0,
    sell_stretch: float = 1.0,
    buy_tilt_delta: float = 0.0,
    sell_tilt_delta: float = 0.0,
    price_tick: float,
) -> RungSet:
    """Stage-1 refinement overlay on a literal ladder (Phase A.1 §3).

    Geometry-preserving transforms applied per side:
    - shift: nearest rung moves by (1+shift); the whole side follows.
    - stretch: each rung's log-distance from the (shifted) nearest rung is
      scaled — p_i' = p_near' * (p_i/p_near)**stretch — preserving the
      relative spacing pattern while widening/tightening it.
    - tilt: weight_i *= exp(delta * i/(n-1)), then max-renormalized —
      preserves the hand-built shape, re-tilts it.

    The IDENTITY overlay (shift=0, stretch=1, delta=0) reproduces the input
    bit-for-bit (unit-tested); moved prices are tick-quantized (buys down,
    sells up), untouched sides are never re-quantized so off-grid live rungs
    survive an identity pass unchanged.
    """
    def _prices(side: np.ndarray, shift: float, stretch: float, direction: str) -> np.ndarray:
        if shift == 0.0 and stretch == 1.0:
            return side.copy()
        p_near = float(side[0])
        p_near_shifted = p_near * (1.0 + shift)
        out = p_near_shifted * (side / p_near) ** stretch
        return np.array(
            [quantize_price(float(p), price_tick, direction) for p in out],
            dtype=np.float64,
        )

    def _weights(side: np.ndarray, delta: float) -> np.ndarray:
        if delta == 0.0:
            return side.copy()
        n = len(side)
        x = np.arange(n, dtype=np.float64) / (n - 1) if n > 1 else np.zeros(1)
        w = side * np.exp(delta * x)
        return w / w.max()

    return RungSet(
        buys=_prices(np.asarray(rungs.buys, dtype=np.float64), buy_shift_pct, buy_stretch, "buy"),
        sells=_prices(np.asarray(rungs.sells, dtype=np.float64), sell_shift_pct, sell_stretch, "sell"),
        buy_weights=_weights(np.asarray(rungs.buy_weights, dtype=np.float64), buy_tilt_delta),
        sell_weights=_weights(np.asarray(rungs.sell_weights, dtype=np.float64), sell_tilt_delta),
    )


def apply_per_rung_nudge(
    rungs: RungSet,
    buy_price_mults,
    sell_price_mults,
    buy_weight_mults,
    sell_weight_mults,
    *,
    price_tick: float,
) -> RungSet:
    """Stage-2 per-rung nudge around a stage-1 winner (Phase A.1 §3).

    Each rung gets its own price multiplier (CMA-ES box [0.98, 1.02]) and
    weight multiplier ([0.75, 1.25]). Identity multipliers reproduce the
    input bit-for-bit; moved prices are tick-quantized.
    """
    def _prices(side: np.ndarray, mults, direction: str) -> np.ndarray:
        mults = np.asarray(mults, dtype=np.float64)
        if len(mults) != len(side):
            raise ValueError(
                f"{direction} price multipliers ({len(mults)}) must match "
                f"rung count ({len(side)})"
            )
        out = side.copy()
        for i, m in enumerate(mults):
            if m != 1.0:
                out[i] = quantize_price(float(side[i] * m), price_tick, direction)
        return out

    def _weights(side: np.ndarray, mults) -> np.ndarray:
        mults = np.asarray(mults, dtype=np.float64)
        if len(mults) != len(side):
            raise ValueError(
                f"weight multipliers ({len(mults)}) must match rung count ({len(side)})"
            )
        if np.all(mults == 1.0):
            return side.copy()
        w = side * mults
        return w / w.max()

    return RungSet(
        buys=_prices(np.asarray(rungs.buys, dtype=np.float64), buy_price_mults, "buy"),
        sells=_prices(np.asarray(rungs.sells, dtype=np.float64), sell_price_mults, "sell"),
        buy_weights=_weights(np.asarray(rungs.buy_weights, dtype=np.float64), buy_weight_mults),
        sell_weights=_weights(np.asarray(rungs.sell_weights, dtype=np.float64), sell_weight_mults),
    )


def count_rung_touches(
    high: np.ndarray,
    low: np.ndarray,
    rung_prices: np.ndarray,
) -> np.ndarray:
    """Per-rung touch counts over a bar window (Phase A.2 §3a).

    A bar touches a rung iff ``low <= rung <= high`` (boundary inclusive).
    Vectorized: O(bars × rungs) boolean reduction.
    """
    high = np.asarray(high, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    rungs = np.asarray(rung_prices, dtype=np.float64)
    if len(high) == 0 or len(rungs) == 0:
        return np.zeros(len(rungs), dtype=np.int64)
    touched = (low[:, None] <= rungs[None, :]) & (rungs[None, :] <= high[:, None])
    return touched.sum(axis=0).astype(np.int64)


def ladder_round_trip_error(
    buy_prices: Sequence[float],
    buy_weights: Sequence[float],
    sell_prices: Sequence[float],
    sell_weights: Sequence[float],
    price_tick: float,
    min_weight_frac: float = DEFAULT_MIN_WEIGHT_FRAC,
) -> float:
    """Max relative error of the generative fit vs the literal ladder.

    Rebuilds rungs from the fitted params at the same anchor and returns the
    worst relative error across rung prices and normalized weights. The unit
    tests assert < 5% for the live DASH and SUN incumbents.
    """
    fit = fit_generative_to_ladder(
        buy_prices, buy_weights, sell_prices, sell_weights,
        min_weight_frac=min_weight_frac,
    )
    params = dict(fit)
    anchor = params.pop("anchor")
    params["min_weight_frac"] = min_weight_frac
    rebuilt = build_rungs(anchor, params, price_tick)

    buys = np.sort(np.asarray(buy_prices, dtype=np.float64))[::-1]
    sells = np.sort(np.asarray(sell_prices, dtype=np.float64))
    bw = np.asarray(buy_weights, dtype=np.float64)
    sw = np.asarray(sell_weights, dtype=np.float64)

    errs = [
        np.max(np.abs(rebuilt.buys - buys) / buys),
        np.max(np.abs(rebuilt.sells - sells) / sells),
        np.max(np.abs(
            rebuilt.buy_weights / rebuilt.buy_weights.sum() - bw / bw.sum()
        ) / (bw / bw.sum())),
        np.max(np.abs(
            rebuilt.sell_weights / rebuilt.sell_weights.sum() - sw / sw.sum()
        ) / (sw / sw.sum())),
    ]
    return float(max(errs))
