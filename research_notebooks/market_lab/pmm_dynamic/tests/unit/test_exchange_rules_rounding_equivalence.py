"""Tests that cached rounding produces identical results to uncached Decimal rounding."""

import pytest
from decimal import Decimal, ROUND_DOWN, ROUND_UP

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.config.exchange_rules import round_price, round_price_up, round_amount, _decimal_quantizers


def _make_rules(price_tick: float, amount_step: float) -> PairRules:
    return PairRules(
        price_tick=price_tick,
        amount_step=amount_step,
        min_notional_quote=5.0,
        min_order_size_base=0.0,
        max_order_size_base=None,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _reference_round_price(price: float, tick: float) -> float:
    """Reference implementation without caching."""
    t = Decimal(str(tick))
    p = Decimal(str(price))
    return float((p / t).to_integral_value(rounding=ROUND_DOWN) * t)


def _reference_round_price_up(price: float, tick: float) -> float:
    t = Decimal(str(tick))
    p = Decimal(str(price))
    return float((p / t).to_integral_value(rounding=ROUND_UP) * t)


def _reference_round_amount(amount: float, step: float) -> float:
    s = Decimal(str(step))
    a = Decimal(str(amount))
    return float((a / s).to_integral_value(rounding=ROUND_DOWN) * s)


class TestRoundingEquivalence:
    """Cached rounding must produce identical results to uncached reference."""

    @pytest.mark.parametrize("price,tick,step", [
        (123.456789, 0.01, 0.001),
        (0.00345678, 0.0001, 0.01),
        (99999.99, 1.0, 0.1),
        (1.0, 0.005, 0.01),
        (0.1, 0.0001, 0.0001),
    ])
    def test_round_price_equivalence(self, price, tick, step):
        rules = _make_rules(tick, step)
        cached = round_price(price, rules)
        reference = _reference_round_price(price, tick)
        assert cached == reference, f"round_price({price}, tick={tick}): {cached} != {reference}"

    @pytest.mark.parametrize("price,tick,step", [
        (123.456789, 0.01, 0.001),
        (0.00345678, 0.0001, 0.01),
        (99999.99, 1.0, 0.1),
        (1.0, 0.005, 0.01),
        (0.1, 0.0001, 0.0001),
    ])
    def test_round_price_up_equivalence(self, price, tick, step):
        rules = _make_rules(tick, step)
        cached = round_price_up(price, rules)
        reference = _reference_round_price_up(price, tick)
        assert cached == reference, f"round_price_up({price}, tick={tick}): {cached} != {reference}"

    @pytest.mark.parametrize("amount,tick,step", [
        (1.23456, 0.01, 0.001),
        (0.999, 0.01, 0.01),
        (100.0, 0.01, 0.1),
        (0.0055, 0.01, 0.001),
    ])
    def test_round_amount_equivalence(self, amount, tick, step):
        rules = _make_rules(tick, step)
        cached = round_amount(amount, rules)
        reference = _reference_round_amount(amount, step)
        assert cached == reference, f"round_amount({amount}, step={step}): {cached} != {reference}"

    def test_cache_is_populated(self):
        """_decimal_quantizers must use lru_cache."""
        # Clear cache
        _decimal_quantizers.cache_clear()

        rules = _make_rules(0.01, 0.001)
        round_price(100.0, rules)

        info = _decimal_quantizers.cache_info()
        assert info.misses >= 1, "Cache should have at least one miss on first call"

        # Second call with same rules should hit cache
        round_price(200.0, rules)
        info2 = _decimal_quantizers.cache_info()
        assert info2.hits >= 1, "Cache should have at least one hit on repeated call"
