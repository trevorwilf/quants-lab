"""
Conservative candle-based fill model.

Rules:
1. Buy limit order fills if candle_low <= order_price AND volume > 0.
2. Sell limit order fills if candle_high >= order_price AND volume > 0.
3. Fill quantity is capped by: fill_participation_rate * candle_volume.
4. Partial fills are supported — unfilled remainder stays active.
5. No fills on zero-volume candles (regardless of price).
6. Orders placed during bar t become eligible for fills starting at bar t + latency_bars.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FillResult:
    """Result of a fill attempt for one order on one candle."""
    filled: bool
    fill_price: float          # the order's limit price (conservative: no price improvement)
    fill_quantity: float       # actual quantity filled (may be partial)
    remaining_quantity: float  # unfilled remainder
    fill_type: str             # "maker" for limit fills, "taker" for market exits


def check_buy_fill(
    order_price: float,
    order_quantity: float,
    candle_low: float,
    candle_volume: float,
    fill_participation_rate: float = 0.1,
    remaining_capacity: float = float('inf'),
) -> FillResult:
    """Check if a buy limit order fills on this candle.

    A buy limit fills if candle_low <= order_price AND candle_volume > 0.
    Fill size = min(order_quantity, fill_participation_rate * candle_volume, remaining_capacity).

    Parameters
    ----------
    order_price : float
        Buy limit price.
    order_quantity : float
        Remaining order quantity.
    candle_low : float
        Candle low price.
    candle_volume : float
        Candle volume.
    fill_participation_rate : float
        Max fraction of candle volume per fill.
    remaining_capacity : float
        Max fill capacity remaining for this candle.

    Returns
    -------
    FillResult
    """
    if candle_volume <= 0 or candle_low > order_price:
        return FillResult(
            filled=False,
            fill_price=order_price,
            fill_quantity=0.0,
            remaining_quantity=order_quantity,
            fill_type="maker",
        )

    max_fill = fill_participation_rate * candle_volume
    fill_qty = min(order_quantity, max_fill, remaining_capacity)

    return FillResult(
        filled=fill_qty > 0,
        fill_price=order_price,
        fill_quantity=fill_qty,
        remaining_quantity=order_quantity - fill_qty,
        fill_type="maker",
    )


def check_sell_fill(
    order_price: float,
    order_quantity: float,
    candle_high: float,
    candle_volume: float,
    fill_participation_rate: float = 0.1,
    remaining_capacity: float = float('inf'),
) -> FillResult:
    """Check if a sell limit order fills on this candle.

    A sell limit fills if candle_high >= order_price AND candle_volume > 0.
    Fill size = min(order_quantity, fill_participation_rate * candle_volume, remaining_capacity).

    Parameters
    ----------
    order_price : float
        Sell limit price.
    order_quantity : float
        Remaining order quantity.
    candle_high : float
        Candle high price.
    candle_volume : float
        Candle volume.
    fill_participation_rate : float
        Max fraction of candle volume per fill.
    remaining_capacity : float
        Max fill capacity remaining for this candle.

    Returns
    -------
    FillResult
    """
    if candle_volume <= 0 or candle_high < order_price:
        return FillResult(
            filled=False,
            fill_price=order_price,
            fill_quantity=0.0,
            remaining_quantity=order_quantity,
            fill_type="maker",
        )

    max_fill = fill_participation_rate * candle_volume
    fill_qty = min(order_quantity, max_fill, remaining_capacity)

    return FillResult(
        filled=fill_qty > 0,
        fill_price=order_price,
        fill_quantity=fill_qty,
        remaining_quantity=order_quantity - fill_qty,
        fill_type="maker",
    )
