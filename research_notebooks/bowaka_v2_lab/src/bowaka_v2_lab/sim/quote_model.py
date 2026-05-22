"""Quote model — historical quote loader + policy-driven fallback (Phase 6).

When a historical quote is unavailable for ``(symbol, t)`` the simulator falls
back per ``simulation.quote_fallback_policy``:

- ``zero_spread`` — parity with the live code (``bowaka_v2_strategy.py:743-748``):
  ``Quote(bid=ask=mid=signal_price, spread=0, age=0,
  source="synthetic_zero_spread")``.
- ``synthetic_calibrated`` — derive a spread from a per-symbol/day spread model
  calibrated to ADV / price / volatility; ``quote_age`` random in
  ``[1, max_quote_age_seconds]``; ``mid = signal_price``;
  ``source="synthetic_calibrated"``.
- ``require_real`` — no synthetic quote at all: the caller must reject the
  candidate with ``missing_quote``.

Every fallback quote carries an explicit ``source`` so downstream readers can
tell real from synthetic and tell the two synthetic flavours apart.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Optional

from ..utils.time import require_aware_timestamp

#: Quote ``source`` values the model produces.
SOURCE_HISTORICAL = "historical"
SOURCE_SYNTHETIC_ZERO_SPREAD = "synthetic_zero_spread"
SOURCE_SYNTHETIC_CALIBRATED = "synthetic_calibrated"
#: Legacy synthetic source (kept so pre-Phase-6 tests / artifacts still resolve).
SOURCE_SYNTHETIC_V1 = "synthetic_quote_model_v1"


@dataclass
class QuoteSnapshot:
    bid: float
    ask: float
    mid: float
    spread_pct: float
    quote_timestamp: str
    quote_age_seconds: float
    source: str
    bid_size: float = 0.0
    ask_size: float = 0.0
    calibration_dataset_hash: Optional[str] = None
    stress_level: Optional[str] = None

    @property
    def is_historical(self) -> bool:
        return self.source == SOURCE_HISTORICAL

    @property
    def is_synthetic(self) -> bool:
        return not self.is_historical


# --------------------------------------------------------------------------
# Calibrated synthetic spread model
# --------------------------------------------------------------------------
def calibrated_half_spread_bps(
    *,
    price: float,
    adv_dollars: float,
    volatility_pct: float,
    stress_level: str = "conservative",
) -> float:
    """Half-spread (bps) for a per-symbol/day calibrated synthetic quote.

    The spread widens for cheaper names, thinner ADV and higher volatility — the
    structural drivers of real equity spreads. The stress level scales the whole
    estimate. The result is a deterministic function of its inputs (a per-symbol
    spread model, not a random draw), floored / capped at sane bounds.
    """
    # Price term — a $1 stock spends far more bps crossing one cent than a $50.
    price_term = 6.0 / max(0.5, float(price)) * 5.0
    # Liquidity term — thin ADV pays up; reference ADV $5M.
    adv = max(1.0, float(adv_dollars))
    liquidity_term = 4.0 * (5_000_000.0 / adv) ** 0.25
    # Volatility term — vol in pct (0.02 == 2%).
    vol_term = 60.0 * max(0.0, float(volatility_pct))
    base = price_term + liquidity_term + vol_term
    stress_mult = {"base": 1.0, "conservative": 1.5, "severe": 3.0}.get(stress_level, 1.5)
    half = base * stress_mult
    return float(min(250.0, max(1.0, half)))


def synthesize_calibrated_quote(
    *,
    signal_price: float,
    at: Any,
    adv_dollars: float = 5_000_000.0,
    volatility_pct: float = 0.02,
    max_quote_age_seconds: int = 5,
    stress_level: str = "conservative",
    rng: Optional[random.Random] = None,
    calibration_dataset_hash: Optional[str] = None,
) -> QuoteSnapshot:
    """A calibrated synthetic quote (smoke path).

    ``mid = signal_price``; the spread comes from
    :func:`calibrated_half_spread_bps`; ``quote_age`` is a random integer in
    ``[1, max_quote_age_seconds]``. ``source = synthetic_calibrated``.
    """
    if signal_price is None or signal_price <= 0:
        raise ValueError("synthesize_calibrated_quote: signal_price must be > 0")
    at_ts = require_aware_timestamp(at, label="synthesize_calibrated_quote.at")
    r = rng if rng is not None else random.Random(0)
    half_bps = calibrated_half_spread_bps(
        price=signal_price, adv_dollars=adv_dollars,
        volatility_pct=volatility_pct, stress_level=stress_level,
    )
    half = signal_price * half_bps / 10_000.0
    bid = round(signal_price - half, 4)
    ask = round(signal_price + half, 4)
    mid = round(signal_price, 4)
    spread_pct = (ask - bid) / mid if mid > 0 else 0.0
    age = float(r.randint(1, max(1, int(max_quote_age_seconds))))
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=spread_pct,
        quote_timestamp=at_ts.isoformat(),
        quote_age_seconds=age,
        source=SOURCE_SYNTHETIC_CALIBRATED,
        bid_size=10_000.0, ask_size=10_000.0,
        calibration_dataset_hash=calibration_dataset_hash,
        stress_level=stress_level,
    )


def synthesize_zero_spread_quote(*, signal_price: float, at: Any) -> QuoteSnapshot:
    """A zero-spread synthetic quote — parity with live ``bowaka_v2_strategy.py:743-748``.

    ``bid == ask == mid == signal_price``, ``spread_pct == 0``, ``age == 0``,
    ``source == synthetic_zero_spread``.
    """
    if signal_price is None or signal_price <= 0:
        raise ValueError("synthesize_zero_spread_quote: signal_price must be > 0")
    at_ts = require_aware_timestamp(at, label="synthesize_zero_spread_quote.at")
    px = round(float(signal_price), 4)
    return QuoteSnapshot(
        bid=px, ask=px, mid=px, spread_pct=0.0,
        quote_timestamp=at_ts.isoformat(),
        quote_age_seconds=0.0,
        source=SOURCE_SYNTHETIC_ZERO_SPREAD,
        bid_size=0.0, ask_size=0.0,
    )


def synthesize_quote(
    *,
    last_price: float,
    at: Any,
    stress_level: str = "conservative",
    calibration_dataset_hash: Optional[str] = None,
) -> QuoteSnapshot:
    """Legacy conservative synthetic quote (pre-Phase-6).

    Retained so existing tests / artifacts that import ``synthesize_quote``
    keep working. New code should call :func:`resolve_quote` so the
    ``quote_fallback_policy`` is honoured.
    """
    if last_price is None or last_price <= 0:
        raise ValueError("synthesize_quote: last_price must be > 0")
    at_ts = require_aware_timestamp(at, label="synthesize_quote.at")
    half_spread_bps = {"base": 5.0, "conservative": 15.0, "severe": 50.0}.get(stress_level, 15.0)
    half = last_price * half_spread_bps / 10_000.0
    bid = round(last_price - half, 4)
    ask = round(last_price + half, 4)
    mid = round((bid + ask) / 2.0, 4)
    spread_pct = (ask - bid) / mid if mid > 0 else 0.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=spread_pct,
        quote_timestamp=at_ts.isoformat(),
        quote_age_seconds=0.0,
        source=SOURCE_SYNTHETIC_V1,
        bid_size=10_000.0, ask_size=10_000.0,
        calibration_dataset_hash=calibration_dataset_hash,
        stress_level=stress_level,
    )


def _quote_from_historical(historical_quote: dict) -> QuoteSnapshot:
    bid = float(historical_quote.get("bid", 0.0) or 0.0)
    ask = float(historical_quote.get("ask", 0.0) or 0.0)
    mid = float(historical_quote.get("mid", (bid + ask) / 2.0) or 0.0)
    spread_pct = float(
        historical_quote.get("spread_pct", (ask - bid) / mid if mid > 0 else 0.0) or 0.0
    )
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=spread_pct,
        quote_timestamp=str(historical_quote.get("quote_timestamp", "")),
        quote_age_seconds=float(historical_quote.get("quote_age_seconds", 0.0) or 0.0),
        source=str(historical_quote.get("source", SOURCE_HISTORICAL)),
        bid_size=float(historical_quote.get("bid_size", 0.0) or 0.0),
        ask_size=float(historical_quote.get("ask_size", 0.0) or 0.0),
    )


@dataclass
class QuoteResolution:
    """Result of :func:`resolve_quote` — a quote plus how it was sourced.

    ``quote`` is ``None`` only for the ``require_real`` policy with no historical
    quote; in that case ``missing_quote`` is ``True`` and the caller must reject
    the candidate.
    """

    quote: Optional[QuoteSnapshot]
    missing_quote: bool = False

    @property
    def is_historical(self) -> bool:
        return self.quote is not None and self.quote.is_historical


def resolve_quote(
    *,
    symbol: str,
    at: Any,
    signal_price: float,
    historical_quote: Optional[dict] = None,
    quote_fallback_policy: str = "zero_spread",
    adv_dollars: float = 5_000_000.0,
    volatility_pct: float = 0.02,
    max_quote_age_seconds: int = 5,
    stress_level: str = "conservative",
    rng: Optional[random.Random] = None,
    calibration_dataset_hash: Optional[str] = None,
) -> QuoteResolution:
    """Resolve a quote for ``(symbol, at)``, honouring ``quote_fallback_policy``.

    A historical quote always wins. Otherwise the policy decides:

    - ``zero_spread`` → :func:`synthesize_zero_spread_quote`.
    - ``synthetic_calibrated`` → :func:`synthesize_calibrated_quote`.
    - ``require_real`` → ``QuoteResolution(quote=None, missing_quote=True)``.
    """
    if historical_quote:
        return QuoteResolution(quote=_quote_from_historical(historical_quote))

    policy = str(quote_fallback_policy or "zero_spread")
    if policy == "require_real":
        return QuoteResolution(quote=None, missing_quote=True)
    if policy == "synthetic_calibrated":
        q = synthesize_calibrated_quote(
            signal_price=signal_price, at=at,
            adv_dollars=adv_dollars, volatility_pct=volatility_pct,
            max_quote_age_seconds=max_quote_age_seconds,
            stress_level=stress_level, rng=rng,
            calibration_dataset_hash=calibration_dataset_hash,
        )
        return QuoteResolution(quote=q)
    # zero_spread (parity) — the default.
    return QuoteResolution(quote=synthesize_zero_spread_quote(signal_price=signal_price, at=at))


def get_quote(
    *,
    symbol: str,
    at: Any,
    last_price: float,
    historical_quote: Optional[dict] = None,
    stress_level: str = "conservative",
    calibration_dataset_hash: Optional[str] = None,
) -> QuoteSnapshot:
    """Legacy entry point — historical when available, else legacy synthetic.

    Kept for back-compat. New code calls :func:`resolve_quote` so the
    ``quote_fallback_policy`` is respected.
    """
    if historical_quote:
        return _quote_from_historical(historical_quote)
    return synthesize_quote(
        last_price=last_price, at=at,
        stress_level=stress_level,
        calibration_dataset_hash=calibration_dataset_hash,
    )
