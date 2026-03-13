"""Tests for order ladder construction and lifecycle."""

import numpy as np
import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.executor_model import SimConfig


def _make_rules(price_tick=0.01, amount_step=0.00001, min_notional=5.0):
    return PairRules(
        price_tick=price_tick,
        amount_step=amount_step,
        min_notional_quote=min_notional,
        min_order_size_base=0.0,
        max_order_size_base=None,
        fees=FeeConfig(0.001, 0.002),
    )


def test_buy_ladder_prices_decrease():
    """Buy prices descend from reference_price with increasing spread."""
    rules = _make_rules()
    config = SimConfig(
        buy_spreads=[1.0, 2.0, 4.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[0.5, 0.3, 0.2],
        sell_amounts_pct=[1.0],
        total_amount_quote=1000.0,
    )
    runner = CandleSimRunner(config, rules)
    orders, placed, rejected = runner._build_order_ladder(
        reference_price=100000.0, spread_multiplier=0.01, bar_idx=0,
    )
    buy_orders = [o for o in orders if o.side == "buy"]
    assert len(buy_orders) == 3
    prices = [o.price for o in buy_orders]
    assert prices[0] > prices[1] > prices[2]


def test_sell_ladder_prices_increase():
    """Sell prices ascend from reference_price with increasing spread."""
    rules = _make_rules()
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0, 2.0, 4.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[0.5, 0.3, 0.2],
        total_amount_quote=1000.0,
    )
    runner = CandleSimRunner(config, rules)
    orders, placed, rejected = runner._build_order_ladder(
        reference_price=100000.0, spread_multiplier=0.01, bar_idx=0,
    )
    sell_orders = [o for o in orders if o.side == "sell"]
    assert len(sell_orders) == 3
    prices = [o.price for o in sell_orders]
    assert prices[0] < prices[1] < prices[2]


def test_asymmetric_levels():
    """Different number of buy and sell levels."""
    rules = _make_rules()
    config = SimConfig(
        buy_spreads=[1.0, 2.0, 4.0],
        sell_spreads=[1.0, 2.0, 3.0, 4.0, 5.0],
        buy_amounts_pct=[0.5, 0.3, 0.2],
        sell_amounts_pct=[0.3, 0.25, 0.2, 0.15, 0.1],
        total_amount_quote=1000.0,
    )
    runner = CandleSimRunner(config, rules)
    orders, placed, rejected = runner._build_order_ladder(
        reference_price=100000.0, spread_multiplier=0.01, bar_idx=0,
    )
    buy_orders = [o for o in orders if o.side == "buy"]
    sell_orders = [o for o in orders if o.side == "sell"]
    assert len(buy_orders) == 3
    assert len(sell_orders) == 5


def test_amount_allocation_buy_side_weight():
    """buy_side_weight=0.7 allocates ~70% to buys, ~30% to sells."""
    rules = _make_rules()
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        buy_side_weight=0.7,
        total_amount_quote=100.0,
    )
    runner = CandleSimRunner(config, rules)
    orders, _, _ = runner._build_order_ladder(
        reference_price=100000.0, spread_multiplier=0.001, bar_idx=0,
    )
    buy_orders = [o for o in orders if o.side == "buy"]
    sell_orders = [o for o in orders if o.side == "sell"]

    buy_quote = sum(o.quantity * o.price for o in buy_orders)
    sell_quote = sum(o.quantity * 100000.0 for o in sell_orders)  # approximate

    # Buy side should get ~70 quote, sell ~30 quote
    assert buy_quote > sell_quote


def test_prices_are_exchange_rounded():
    """All order prices are multiples of price_tick; quantities of amount_step."""
    from decimal import Decimal
    rules = _make_rules(price_tick=0.01, amount_step=0.00001)
    config = SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.6, 0.4],
        sell_amounts_pct=[0.6, 0.4],
        total_amount_quote=1000.0,
    )
    runner = CandleSimRunner(config, rules)
    orders, _, _ = runner._build_order_ladder(
        reference_price=100000.0, spread_multiplier=0.01, bar_idx=0,
    )
    tick = Decimal("0.01")
    step = Decimal("0.00001")
    for o in orders:
        price_d = Decimal(str(o.price))
        qty_d = Decimal(str(o.quantity))
        assert price_d % tick == 0, f"Price {o.price} not a multiple of tick {tick}"
        assert qty_d % step == 0, f"Qty {o.quantity} not a multiple of step {step}"


def test_sell_sizing_uses_order_price():
    """Sell order quantity * sell order price ≈ allocated quote amount."""
    rules = _make_rules(min_notional=1.0)
    config = SimConfig(
        buy_spreads=[1.0],
        sell_spreads=[1.0],
        buy_amounts_pct=[1.0],
        sell_amounts_pct=[1.0],
        buy_side_weight=0.5,
        total_amount_quote=100.0,
    )
    runner = CandleSimRunner(config, rules)
    orders, _, _ = runner._build_order_ladder(
        reference_price=100.0, spread_multiplier=0.02, bar_idx=0,
    )
    sell_orders = [o for o in orders if o.side == "sell"]
    assert len(sell_orders) == 1
    order = sell_orders[0]
    # sell_price = 100 * (1 + 1.0*0.02) = 102
    # quote_amount = 50 * 1.0 = 50
    # base_amount = 50 / 102 ≈ 0.49019...
    # order.quantity * order.price ≈ 50 (not order.quantity * reference_price)
    notional = order.quantity * order.price
    expected_quote = 50.0
    assert abs(notional - expected_quote) < 1.0, (
        f"notional={notional}, expected ~{expected_quote}"
    )


def test_min_notional_rejection():
    """Very small total_amount_quote causes some levels to be rejected."""
    rules = _make_rules(min_notional=5.0)
    config = SimConfig(
        buy_spreads=[1.0, 2.0, 4.0],
        sell_spreads=[1.0, 2.0, 4.0],
        buy_amounts_pct=[0.5, 0.3, 0.2],
        sell_amounts_pct=[0.5, 0.3, 0.2],
        total_amount_quote=1.0,  # very small
    )
    runner = CandleSimRunner(config, rules)
    orders, placed, rejected = runner._build_order_ladder(
        reference_price=100000.0, spread_multiplier=0.01, bar_idx=0,
    )
    assert rejected > 0
