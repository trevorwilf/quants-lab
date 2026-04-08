"""Tests for supports_post_only on PairRules and exchange_rules (Fix 3)."""

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules


class TestPairRulesSupportsPostOnly:
    def test_default_is_true(self):
        rules = PairRules(price_tick=0.01, amount_step=0.001, min_notional_quote=5.0)
        assert rules.supports_post_only is True

    def test_explicit_false(self):
        rules = PairRules(
            price_tick=0.01, amount_step=0.001, min_notional_quote=5.0,
            supports_post_only=False,
        )
        assert rules.supports_post_only is False


class TestExchangeRulesYaml:
    def test_nonkyc_does_not_support_post_only(self):
        rules_data = load_exchange_rules()
        pair_rules = resolve_pair_rules(rules_data, "nonkyc", "XMR-USDT")
        assert pair_rules.supports_post_only is False

    def test_mexc_supports_post_only(self):
        rules_data = load_exchange_rules()
        pair_rules = resolve_pair_rules(rules_data, "mexc", "BTC-USDT")
        assert pair_rules.supports_post_only is True
