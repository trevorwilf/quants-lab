"""Side-aware price rounding tests."""
from pmm_lab.config.exchange_rules import round_price, round_price_up
from pmm_lab.config.params import PairRules, FeeConfig


def _rules(price_tick=0.01):
    return PairRules(price_tick=price_tick, amount_step=0.001,
                     min_notional_quote=1.0,
                     fees=FeeConfig(maker_fee=0.001, taker_fee=0.002))


class TestRoundPriceDown:
    def test_exact_tick(self):
        assert round_price(100.01, _rules()) == 100.01

    def test_rounds_down(self):
        assert round_price(100.015, _rules()) == 100.01

    def test_rounds_down_large_tick(self):
        assert round_price(100.7, _rules(price_tick=1.0)) == 100.0


class TestRoundPriceUp:
    def test_exact_tick(self):
        assert round_price_up(100.01, _rules()) == 100.01

    def test_rounds_up(self):
        assert round_price_up(100.011, _rules()) == 100.02

    def test_rounds_up_large_tick(self):
        assert round_price_up(100.1, _rules(price_tick=1.0)) == 101.0


class TestSideAwareness:
    def test_buy_down_sell_up(self):
        """Buy rounds down (favorable), sell rounds up (preserves spread)."""
        rules = _rules(price_tick=0.01)
        price = 100.015
        assert round_price(price, rules) == 100.01     # buy: down
        assert round_price_up(price, rules) == 100.02   # sell: up

    def test_spread_not_narrowed(self):
        """After rounding, sell price >= buy price when starting from same mid."""
        rules = _rules(price_tick=0.5)
        mid = 100.0
        buy = mid - 0.3   # 99.7
        sell = mid + 0.3   # 100.3
        rounded_buy = round_price(buy, rules)      # 99.5
        rounded_sell = round_price_up(sell, rules)  # 100.5
        assert rounded_sell > rounded_buy
        assert rounded_sell - rounded_buy >= 1.0  # at least 2 ticks spread
