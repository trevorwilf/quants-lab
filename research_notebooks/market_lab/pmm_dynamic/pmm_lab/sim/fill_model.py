"""
Candle-based fill model with configurable realism.

v2 adds:
- Touch-through: price must pass through order level, not just touch it
- Entry spread: half-spread adverse cost on maker entries
- Maker fill probability: not all price-eligible fills actually execute

All v2 features default to v1 behavior when disabled.
"""

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class FillResult:
    """Result of a fill attempt for one order on one candle."""
    filled: bool
    fill_price: float          # adjusted price (includes entry spread if any)
    fill_quantity: float       # actual quantity filled
    remaining_quantity: float  # unfilled remainder
    fill_type: str             # "maker" for limit fills


def _deterministic_random(seed_bytes: bytes) -> float:
    """Deterministic pseudo-random float in [0, 1) from seed bytes.

    Uses SHA-256 hash truncated to 8 bytes -> float.
    This ensures reproducibility without needing global RNG state.
    """
    h = hashlib.sha256(seed_bytes).digest()[:8]
    # Convert to integer and normalize to [0, 1)
    val = int.from_bytes(h, "big")
    return val / (2**64)


def check_buy_fill(
    order_price: float,
    order_quantity: float,
    candle_low: float,
    candle_volume: float,
    fill_participation_rate: float = 0.1,
    remaining_capacity: float = float('inf'),
    touch_through: bool = False,
    entry_spread_bps: float = 0.0,
    maker_fill_probability: float = 1.0,
    fill_seed: int = 0,
    taker_probability: float = 0.0,
) -> FillResult:
    """Check if a buy limit order fills on this candle.

    Parameters
    ----------
    order_price : float
        Buy limit price.
    order_quantity : float
        Remaining order quantity.
    candle_low : float
        Candle low price.
    candle_volume : float
        Candle volume (base units).
    fill_participation_rate : float
        Max fraction of candle volume per fill.
    remaining_capacity : float
        Shared capacity remaining for this bar.
    touch_through : bool
        If True, require candle_low < order_price (strict through).
        If False, require candle_low <= order_price (v1 touch behavior).
    entry_spread_bps : float
        Half-spread adverse cost in basis points. Buy fills at slightly HIGHER price.
    maker_fill_probability : float
        Probability that an eligible fill actually executes (1.0 = always).
    fill_seed : int
        Deterministic seed for maker fill probability check.

    Returns
    -------
    FillResult
    """
    no_fill = FillResult(
        filled=False, fill_price=order_price,
        fill_quantity=0.0, remaining_quantity=order_quantity, fill_type="maker",
    )

    if candle_volume <= 0:
        return no_fill

    # Touch vs touch-through
    if touch_through:
        if candle_low >= order_price:  # strict: low must be BELOW order price
            return no_fill
    else:
        if candle_low > order_price:   # v1: low can equal order price
            return no_fill

    # Maker fill probability check (deterministic)
    if maker_fill_probability < 1.0:
        seed_bytes = f"buy:{fill_seed}:{order_price:.8f}".encode()
        if _deterministic_random(seed_bytes) >= maker_fill_probability:
            return no_fill

    # Volume cap
    max_fill = fill_participation_rate * candle_volume
    fill_qty = min(order_quantity, max_fill, remaining_capacity)
    if fill_qty <= 0:
        return no_fill

    # Entry spread: buy fills at slightly worse (higher) price
    adjusted_price = order_price * (1.0 + entry_spread_bps / 20000.0)

    # Taker probability check (deterministic, after fill eligibility)
    fill_type = "maker"
    if taker_probability > 0.0:
        if taker_probability >= 1.0:
            fill_type = "taker"
        else:
            seed_bytes = f"taker_check:buy:{fill_seed}:{order_price:.8f}".encode()
            if _deterministic_random(seed_bytes) < taker_probability:
                fill_type = "taker"

    return FillResult(
        filled=True,
        fill_price=adjusted_price,
        fill_quantity=fill_qty,
        remaining_quantity=order_quantity - fill_qty,
        fill_type=fill_type,
    )


def check_sell_fill(
    order_price: float,
    order_quantity: float,
    candle_high: float,
    candle_volume: float,
    fill_participation_rate: float = 0.1,
    remaining_capacity: float = float('inf'),
    touch_through: bool = False,
    entry_spread_bps: float = 0.0,
    maker_fill_probability: float = 1.0,
    fill_seed: int = 0,
    taker_probability: float = 0.0,
) -> FillResult:
    """Check if a sell limit order fills on this candle.

    Parameters
    ----------
    order_price : float
        Sell limit price.
    order_quantity : float
        Remaining order quantity.
    candle_high : float
        Candle high price.
    candle_volume : float
        Candle volume (base units).
    fill_participation_rate : float
        Max fraction of candle volume per fill.
    remaining_capacity : float
        Shared capacity remaining for this bar.
    touch_through : bool
        If True, require candle_high > order_price (strict through).
        If False, require candle_high >= order_price (v1 touch behavior).
    entry_spread_bps : float
        Half-spread adverse cost in basis points. Sell fills at slightly LOWER price.
    maker_fill_probability : float
        Probability that an eligible fill actually executes (1.0 = always).
    fill_seed : int
        Deterministic seed for maker fill probability check.

    Returns
    -------
    FillResult
    """
    no_fill = FillResult(
        filled=False, fill_price=order_price,
        fill_quantity=0.0, remaining_quantity=order_quantity, fill_type="maker",
    )

    if candle_volume <= 0:
        return no_fill

    # Touch vs touch-through
    if touch_through:
        if candle_high <= order_price:  # strict: high must be ABOVE order price
            return no_fill
    else:
        if candle_high < order_price:   # v1: high can equal order price
            return no_fill

    # Maker fill probability check (deterministic)
    if maker_fill_probability < 1.0:
        seed_bytes = f"sell:{fill_seed}:{order_price:.8f}".encode()
        if _deterministic_random(seed_bytes) >= maker_fill_probability:
            return no_fill

    # Volume cap
    max_fill = fill_participation_rate * candle_volume
    fill_qty = min(order_quantity, max_fill, remaining_capacity)
    if fill_qty <= 0:
        return no_fill

    # Entry spread: sell fills at slightly worse (lower) price
    adjusted_price = order_price * (1.0 - entry_spread_bps / 20000.0)

    # Taker probability check (deterministic, after fill eligibility)
    fill_type = "maker"
    if taker_probability > 0.0:
        if taker_probability >= 1.0:
            fill_type = "taker"
        else:
            seed_bytes = f"taker_check:sell:{fill_seed}:{order_price:.8f}".encode()
            if _deterministic_random(seed_bytes) < taker_probability:
                fill_type = "taker"

    return FillResult(
        filled=True,
        fill_price=adjusted_price,
        fill_quantity=fill_qty,
        remaining_quantity=order_quantity - fill_qty,
        fill_type=fill_type,
    )
