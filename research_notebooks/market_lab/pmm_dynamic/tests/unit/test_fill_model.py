"""Tests for the conservative fill model."""

import pytest
from pmm_lab.sim.fill_model import check_buy_fill, check_sell_fill


def test_buy_fill_price_below_low():
    """Buy order price above candle low -> fills."""
    result = check_buy_fill(
        order_price=100.0, order_quantity=1.0,
        candle_low=99.0, candle_volume=10.0,
    )
    assert result.filled is True


def test_buy_no_fill_price_above_low():
    """Buy order price below candle low -> no fill."""
    result = check_buy_fill(
        order_price=98.0, order_quantity=1.0,
        candle_low=99.0, candle_volume=10.0,
    )
    assert result.filled is False


def test_sell_fill_price_above_high():
    """Sell order price below candle high -> fills."""
    result = check_sell_fill(
        order_price=100.0, order_quantity=1.0,
        candle_high=101.0, candle_volume=10.0,
    )
    assert result.filled is True


def test_sell_no_fill_price_below_high():
    """Sell order price above candle high -> no fill."""
    result = check_sell_fill(
        order_price=102.0, order_quantity=1.0,
        candle_high=101.0, candle_volume=10.0,
    )
    assert result.filled is False


def test_no_fill_zero_volume():
    """Zero volume candle -> no fill even if price eligible."""
    result = check_buy_fill(
        order_price=100.0, order_quantity=1.0,
        candle_low=99.0, candle_volume=0.0,
    )
    assert result.filled is False


def test_partial_fill_volume_cap():
    """Fill quantity capped by participation rate * volume."""
    result = check_buy_fill(
        order_price=100.0, order_quantity=1.0,
        candle_low=99.0, candle_volume=0.5,
        fill_participation_rate=0.1,
    )
    assert result.filled is True
    assert result.fill_quantity == pytest.approx(0.05)
    assert result.remaining_quantity == pytest.approx(0.95)


def test_full_fill_sufficient_volume():
    """Small order fully filled with large volume."""
    result = check_buy_fill(
        order_price=100.0, order_quantity=0.01,
        candle_low=99.0, candle_volume=10.0,
        fill_participation_rate=0.1,
    )
    assert result.filled is True
    assert result.fill_quantity == pytest.approx(0.01)
    assert result.remaining_quantity == pytest.approx(0.0)


def test_fill_type_is_maker():
    """All limit fills return fill_type == 'maker'."""
    result = check_buy_fill(
        order_price=100.0, order_quantity=1.0,
        candle_low=99.0, candle_volume=10.0,
    )
    assert result.fill_type == "maker"

    result2 = check_sell_fill(
        order_price=100.0, order_quantity=1.0,
        candle_high=101.0, candle_volume=10.0,
    )
    assert result2.fill_type == "maker"


def test_shared_fill_capacity():
    """5 buy orders, each for 1.0 qty, total fills <= participation * volume."""
    total_filled = 0.0
    capacity = 0.1 * 2.0  # 0.2
    for _ in range(5):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=2.0,
            fill_participation_rate=0.1,
            remaining_capacity=capacity,
        )
        if result.filled:
            total_filled += result.fill_quantity
            capacity -= result.fill_quantity
    assert total_filled <= 0.2 + 1e-10, f"Total filled {total_filled} exceeds capacity 0.2"
    assert total_filled > 0  # at least some fills


def test_remaining_quantity_correct():
    """After partial fill, remaining = original - filled."""
    result = check_buy_fill(
        order_price=100.0, order_quantity=1.0,
        candle_low=99.0, candle_volume=2.0,
        fill_participation_rate=0.1,
    )
    assert result.fill_quantity + result.remaining_quantity == pytest.approx(1.0)
