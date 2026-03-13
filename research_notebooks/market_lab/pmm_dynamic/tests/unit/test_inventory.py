"""Tests for inventory tracking."""

import pytest
from pmm_lab.sim.inventory import Inventory


def test_buy_updates_balances():
    """Buy: quote decreases, base increases."""
    inv = Inventory(base_balance=0.0, quote_balance=2000.0)
    result = inv.buy(quantity=0.01, price=100000.0, fee_quote=1.0)
    assert result is True
    assert inv.base_balance == pytest.approx(0.01)
    assert inv.quote_balance == pytest.approx(2000.0 - 0.01 * 100000.0 - 1.0)


def test_sell_updates_balances():
    """Sell: base decreases, quote increases."""
    inv = Inventory(base_balance=0.01, quote_balance=0.0)
    inv.sell(quantity=0.01, price=100000.0, fee_quote=1.0)
    assert inv.base_balance == pytest.approx(0.0)
    assert inv.quote_balance == pytest.approx(0.01 * 100000.0 - 1.0)


def test_equity_calculation():
    """Equity = quote + base * mid_price."""
    inv = Inventory(base_balance=0.5, quote_balance=50000.0)
    assert inv.equity(100000.0) == pytest.approx(100000.0)


def test_no_negative_base_spot_mode():
    """With 0 base and spot constraints, sell returns False and base stays 0."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    result = inv.sell(1.0, 50000.0, 0.0)
    assert result is False
    assert inv.base_balance == 0.0
    assert inv.quote_balance == 100.0


def test_fee_deducted_from_quote():
    """Fee is deducted from quote balance on buy."""
    inv = Inventory(base_balance=0.0, quote_balance=1000.0)
    fee = 5.0
    result = inv.buy(quantity=0.001, price=100000.0, fee_quote=fee)
    assert result is True
    # quote = 1000 - (0.001 * 100000 + 5) = 1000 - 105 = 895
    assert inv.quote_balance == pytest.approx(895.0)


def test_buy_rejects_when_insufficient_quote():
    """Cannot buy more than quote balance allows."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    # Try to buy 1 BTC at $50000 -- costs $50000 + fees
    result = inv.buy(1.0, 50000.0, 0.0)
    assert result is False
    assert inv.base_balance == 0.0
    assert inv.quote_balance == 100.0


def test_buy_succeeds_when_sufficient_quote():
    """Can buy when quote balance covers cost."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    result = inv.buy(0.001, 50000.0, 0.1)  # cost = 50.0 + 0.1 = 50.1
    assert result is True
    assert abs(inv.base_balance - 0.001) < 1e-10
    assert abs(inv.quote_balance - 49.9) < 1e-10


def test_sell_rejects_when_insufficient_base():
    """Cannot sell base you don't have."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    result = inv.sell(1.0, 50000.0, 0.0)
    assert result is False
    assert inv.base_balance == 0.0


def test_available_quote_for_buy():
    """available_quote_for_buy returns current quote balance."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    assert inv.available_quote_for_buy() == 100.0
    inv.quote_balance = 0.0
    assert inv.available_quote_for_buy() == 0.0
    inv.quote_balance = -10.0  # shouldn't happen, but test safety
    assert inv.available_quote_for_buy() == 0.0


def test_max_buy_quantity():
    """max_buy_quantity computes correct affordable amount."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    # At price=50000, fee_rate=0.001: qty = 100 / (50000 * 1.001) = ~0.001998
    qty = inv.max_buy_quantity(50000.0, 0.001)
    assert qty > 0
    assert qty * 50000.0 * 1.001 <= 100.0 + 1e-10


def test_constraints_disabled_allows_negative():
    """With enforce_spot_constraints=False, balances can go negative."""
    inv = Inventory(base_balance=0.0, quote_balance=0.0, enforce_spot_constraints=False)
    result = inv.buy(1.0, 50000.0, 0.0)
    assert result is True
    assert inv.quote_balance == -50000.0
    result = inv.sell(2.0, 50000.0, 0.0)
    assert result is True
    assert inv.base_balance == -1.0


def test_no_negative_equity_spot_mode():
    """In spot mode, a full buy-then-sell cycle should not produce deeply negative equity."""
    inv = Inventory(base_balance=0.0, quote_balance=100.0, enforce_spot_constraints=True)
    # Buy as much as we can
    inv.buy(0.001, 50000.0, 0.1)  # spend 50.1
    # Sell it back
    inv.sell(0.001, 49000.0, 0.1)  # receive 49.0 - 0.1 = 48.9
    # Small loss from spread + fees, but equity should be ~98.8, never negative
    equity = inv.equity(49000.0)
    assert equity > 0, f"Equity should be positive, got {equity}"
