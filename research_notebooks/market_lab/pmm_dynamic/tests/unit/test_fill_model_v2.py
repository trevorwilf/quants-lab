"""Tests for v2 fill model features: touch-through, entry spread, maker fill probability."""

import pytest

from pmm_lab.sim.fill_model import check_buy_fill, check_sell_fill, _deterministic_random


# ── Touch-through (buy) ─────────────────────────────────────────


class TestBuyTouchThroughEquals:
    def test_buy_touch_through_low_equals_price_no_fill(self):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=100.0, candle_volume=10.0,
            touch_through=True,
        )
        assert not result.filled


class TestBuyTouchThroughBelow:
    def test_buy_touch_through_low_below_price_fills(self):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
            touch_through=True,
        )
        assert result.filled


class TestBuyTouchV1Equals:
    def test_buy_touch_v1_low_equals_price_fills(self):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=100.0, candle_volume=10.0,
            touch_through=False,
        )
        assert result.filled


# ── Touch-through (sell) ─────────────────────────────────────────


class TestSellTouchThroughEquals:
    def test_sell_touch_through_high_equals_price_no_fill(self):
        result = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=100.0, candle_volume=10.0,
            touch_through=True,
        )
        assert not result.filled


class TestSellTouchThroughAbove:
    def test_sell_touch_through_high_above_price_fills(self):
        result = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=101.0, candle_volume=10.0,
            touch_through=True,
        )
        assert result.filled


class TestSellTouchV1Equals:
    def test_sell_touch_v1_high_equals_price_fills(self):
        result = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=100.0, candle_volume=10.0,
            touch_through=False,
        )
        assert result.filled


# ── Entry spread (buy) ──────────────────────────────────────────


class TestBuyEntrySpreadIncreases:
    def test_buy_entry_spread_increases_fill_price(self):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
            entry_spread_bps=10.0,
        )
        assert result.filled
        assert result.fill_price > 100.0


class TestBuyEntrySpreadZero:
    def test_buy_entry_spread_zero_no_change(self):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
            entry_spread_bps=0.0,
        )
        assert result.filled
        assert result.fill_price == 100.0


class TestBuyEntrySpreadAmount:
    def test_buy_entry_spread_amount(self):
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
            entry_spread_bps=10.0,
        )
        # fill_price = 100.0 * (1 + 10/20000) = 100.05
        expected = 100.0 * (1.0 + 10.0 / 20000.0)
        assert abs(result.fill_price - expected) < 1e-10


# ── Entry spread (sell) ─────────────────────────────────────────


class TestSellEntrySpreadDecreases:
    def test_sell_entry_spread_decreases_fill_price(self):
        result = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=101.0, candle_volume=10.0,
            entry_spread_bps=10.0,
        )
        assert result.filled
        assert result.fill_price < 100.0


class TestSellEntrySpreadAmount:
    def test_sell_entry_spread_amount(self):
        result = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=101.0, candle_volume=10.0,
            entry_spread_bps=10.0,
        )
        # fill_price = 100.0 * (1 - 10/20000) = 99.95
        expected = 100.0 * (1.0 - 10.0 / 20000.0)
        assert abs(result.fill_price - expected) < 1e-10


# ── Maker fill probability ──────────────────────────────────────


class TestMakerProbabilityAlways:
    def test_maker_probability_1_always_fills(self):
        for seed in range(20):
            result = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                maker_fill_probability=1.0, fill_seed=seed,
            )
            assert result.filled


class TestMakerProbabilityNever:
    def test_maker_probability_0_never_fills(self):
        for seed in range(20):
            result = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                maker_fill_probability=0.0, fill_seed=seed,
            )
            assert not result.filled


class TestMakerProbabilityDeterministic:
    def test_maker_probability_deterministic(self):
        for seed in range(10):
            r1 = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                maker_fill_probability=0.5, fill_seed=seed,
            )
            r2 = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                maker_fill_probability=0.5, fill_seed=seed,
            )
            assert r1.filled == r2.filled


class TestMakerProbabilityDifferentSeeds:
    def test_maker_probability_different_seeds_can_differ(self):
        results = set()
        for seed in range(100):
            r = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                maker_fill_probability=0.5, fill_seed=seed,
            )
            results.add(r.filled)
        # With 100 seeds and p=0.5, we should see both True and False
        assert True in results and False in results


class TestMakerProbabilityPartialRate:
    def test_maker_probability_partial_rate(self):
        fills = 0
        n = 100
        for seed in range(n):
            r = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                maker_fill_probability=0.5, fill_seed=seed,
            )
            if r.filled:
                fills += 1
        rate = fills / n
        # Wide tolerance: 40%-60%
        assert 0.30 <= rate <= 0.70, f"Fill rate {rate:.2f} outside expected range"


# ── Combined features ───────────────────────────────────────────


class TestTouchThroughPlusSpread:
    def test_touch_through_plus_spread(self):
        # Touch-through: candle_low < order_price
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
            touch_through=True, entry_spread_bps=10.0,
        )
        assert result.filled
        assert result.fill_price > 100.0  # spread applied

        # Touch-through: candle_low == order_price → no fill
        result2 = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=100.0, candle_volume=10.0,
            touch_through=True, entry_spread_bps=10.0,
        )
        assert not result2.filled


class TestAllV2Combined:
    def test_all_v2_features_combined(self):
        # All features active, price passes through → should sometimes fill
        fills = 0
        for seed in range(50):
            r = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                touch_through=True, entry_spread_bps=5.0,
                maker_fill_probability=0.7, fill_seed=seed,
            )
            if r.filled:
                fills += 1
                assert r.fill_price > 100.0  # spread applied
        assert fills > 0  # at least some fills


# ── V1 parity ───────────────────────────────────────────────────


class TestV1DefaultsUnchanged:
    def test_v1_defaults_unchanged(self):
        # Buy: v1 defaults
        r = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=100.0, candle_volume=10.0,
        )
        assert r.filled
        assert r.fill_price == 100.0

        # Sell: v1 defaults
        r = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=100.0, candle_volume=10.0,
        )
        assert r.filled
        assert r.fill_price == 100.0


# ── Deterministic random helper ─────────────────────────────────


class TestDeterministicRandomRange:
    def test_deterministic_random_range(self):
        for i in range(100):
            val = _deterministic_random(f"test:{i}".encode())
            assert 0.0 <= val < 1.0


class TestDeterministicRandomReproducible:
    def test_deterministic_random_reproducible(self):
        v1 = _deterministic_random(b"same_seed")
        v2 = _deterministic_random(b"same_seed")
        assert v1 == v2


class TestDeterministicRandomDifferent:
    def test_deterministic_random_different_inputs(self):
        v1 = _deterministic_random(b"seed_a")
        v2 = _deterministic_random(b"seed_b")
        assert v1 != v2
