"""Tests for XMR-USDT exchange rules overrides (Phase 1B).

XMR-USDT has a different min_notional_quote (1.0) than the connector
defaults (5.0) on both MEXC and NonKYC. This override must actually
take effect — silent fallback to the default would cause under-rejection
at backtest time.

Values pre-verified against live exchange APIs:
  - MEXC exchangeInfo: quotePrecision=2, baseAssetPrecision=3,
    baseSizePrecision="0.001", quoteAmountPrecision="1"
  - NonKYC /market/getlist: priceDecimals=2, quantityDecimals=3,
    minQuote=1 with isMinQuoteActive=true
"""

import math

import pytest

from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules


REL_TOL = 1e-12


class TestXMRUSDTPairOverrides:
    def test_mexc_xmr_usdt_rules(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "mexc", "XMR-USDT")
        assert math.isclose(pair.price_tick, 0.01, rel_tol=REL_TOL)
        assert math.isclose(pair.amount_step, 0.001, rel_tol=REL_TOL)
        assert math.isclose(pair.min_notional_quote, 1.0, rel_tol=REL_TOL)

    def test_nonkyc_xmr_usdt_rules(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "nonkyc", "XMR-USDT")
        assert math.isclose(pair.price_tick, 0.01, rel_tol=REL_TOL)
        assert math.isclose(pair.amount_step, 0.001, rel_tol=REL_TOL)
        assert math.isclose(pair.min_notional_quote, 1.0, rel_tol=REL_TOL)

    def test_min_notional_override_actually_overrides_mexc(self):
        """If the YAML override silently failed, the value would fall back to
        the mexc connector default of 5.0. That must not happen."""
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "mexc", "XMR-USDT")
        assert not math.isclose(pair.min_notional_quote, 5.0, rel_tol=REL_TOL), (
            "XMR-USDT min_notional on mexc fell back to default 5.0 — override silently failed."
        )

    def test_min_notional_override_actually_overrides_nonkyc(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "nonkyc", "XMR-USDT")
        assert not math.isclose(pair.min_notional_quote, 5.0, rel_tol=REL_TOL), (
            "XMR-USDT min_notional on nonkyc fell back to default 5.0 — override silently failed."
        )


class TestExistingPairsRegression:
    """Regression: the Phase 1B additions must not break existing pair overrides."""

    def test_mexc_btc_usdt_still_resolves(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "mexc", "BTC-USDT")
        assert math.isclose(pair.price_tick, 0.01, rel_tol=REL_TOL)
        assert math.isclose(pair.amount_step, 0.00001, rel_tol=REL_TOL)

    def test_nonkyc_btc_usdt_still_resolves(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "nonkyc", "BTC-USDT")
        assert math.isclose(pair.price_tick, 0.01, rel_tol=REL_TOL)
        assert math.isclose(pair.amount_step, 0.000001, rel_tol=REL_TOL)

    def test_mexc_eth_usdt_still_resolves(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "mexc", "ETH-USDT")
        assert math.isclose(pair.price_tick, 0.01, rel_tol=REL_TOL)
        assert math.isclose(pair.amount_step, 0.0001, rel_tol=REL_TOL)

    def test_nonkyc_sal_usdt_still_resolves(self):
        rules_data = load_exchange_rules()
        pair = resolve_pair_rules(rules_data, "nonkyc", "SAL-USDT")
        assert math.isclose(pair.amount_step, 0.01, rel_tol=REL_TOL)
