"""Tests for exchange rules parser and resolver."""

from pathlib import Path

import pytest

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.config.exchange_rules import (
    load_exchange_rules,
    resolve_pair_rules,
    round_price,
    round_amount,
    check_min_notional,
    check_order_size,
)

YAML_PATH = Path(__file__).resolve().parents[2] / "configs" / "exchange_rules.yaml"


@pytest.fixture
def rules_data():
    return load_exchange_rules(yaml_path=YAML_PATH)


def test_load_yaml_file(rules_data):
    """Both mexc and nonkyc connectors are present."""
    assert "mexc" in rules_data["connectors"]
    assert "nonkyc" in rules_data["connectors"]


def test_resolve_pair_specific_override(rules_data):
    """SAL-USDT on mexc gets pair-specific price_tick."""
    rules = resolve_pair_rules(rules_data, "mexc", "SAL-USDT")
    assert rules.price_tick == 0.00001


def test_resolve_falls_back_to_default(rules_data):
    """Unknown pair on nonkyc falls back to connector defaults."""
    rules = resolve_pair_rules(rules_data, "nonkyc", "UNKNOWN-USDT")
    assert rules.price_tick == 0.0001  # nonkyc default
    assert rules.amount_step == 0.000001  # nonkyc default


def test_resolve_unknown_connector_raises(rules_data):
    """Unknown connector raises KeyError."""
    with pytest.raises(KeyError, match="binance"):
        resolve_pair_rules(rules_data, "binance", "BTC-USDT")


def test_round_price_down():
    """Price is rounded DOWN to nearest tick."""
    rules = PairRules(price_tick=0.01, amount_step=0.01, min_notional_quote=5.0)
    assert round_price(100.0567, rules) == 100.05


def test_round_price_exact():
    """Exact price is unchanged."""
    rules = PairRules(price_tick=0.01, amount_step=0.01, min_notional_quote=5.0)
    assert round_price(100.05, rules) == 100.05


def test_round_price_small_tick():
    """Small tick rounds correctly."""
    rules = PairRules(price_tick=0.00001, amount_step=0.01, min_notional_quote=5.0)
    assert round_price(0.123456, rules) == 0.12345


def test_round_amount_down():
    """Amount is rounded DOWN to nearest step."""
    rules = PairRules(price_tick=0.01, amount_step=0.01, min_notional_quote=5.0)
    assert round_amount(1.5678, rules) == 1.56


def test_round_amount_integer_step():
    """Integer step rounds down to whole number."""
    rules = PairRules(price_tick=0.01, amount_step=1.0, min_notional_quote=5.0)
    assert round_amount(123.7, rules) == 123.0


def test_check_min_notional_pass():
    """Notional above minimum passes."""
    rules = PairRules(price_tick=0.01, amount_step=0.01, min_notional_quote=5.0)
    assert check_min_notional(100, 0.1, rules) is True


def test_check_min_notional_fail():
    """Notional below minimum fails."""
    rules = PairRules(price_tick=0.01, amount_step=0.01, min_notional_quote=5.0)
    assert check_min_notional(100, 0.01, rules) is False


def test_check_order_size_clamp_min():
    """Amount below min is clamped up."""
    rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=5.0,
        min_order_size_base=0.001,
    )
    clamped, reason = check_order_size(0.0001, rules)
    assert clamped == 0.001
    assert reason is None


def test_check_order_size_clamp_max():
    """Amount above max is clamped down."""
    rules = PairRules(
        price_tick=0.01, amount_step=0.01, min_notional_quote=5.0,
        min_order_size_base=0.0, max_order_size_base=500.0,
    )
    clamped, reason = check_order_size(1000, rules)
    assert clamped == 500.0
    assert reason is None


def test_check_order_size_below_min_after_step():
    """Amount that rounds below min after step → rejection."""
    rules = PairRules(
        price_tick=0.01, amount_step=1.0, min_notional_quote=5.0,
        min_order_size_base=1.0,
    )
    # Amount 0.5 → clamp up to 1.0 → round down to 1.0 step = 1.0, passes
    # Amount 0.0001 → clamp up to 1.0 → round to 1.0, OK
    # Let's use a case where min=2.0 and amount=1.5 → clamp to 2.0 → round to step=1.0 → 2.0 OK
    # Better: min=2.0, step=5.0, amount=0.1 → clamp to 2.0 → round to step 5.0 → 0.0 → below min
    rules2 = PairRules(
        price_tick=0.01, amount_step=5.0, min_notional_quote=5.0,
        min_order_size_base=2.0,
    )
    clamped, reason = check_order_size(0.1, rules2)
    assert reason is not None
    assert "below" in reason.lower()


def test_static_fee_resolution(rules_data):
    """Nonkyc static fees resolve correctly.

    Changelog (range_ladder Phase A): maker updated 0.0010 → 0.0020 — the
    old YAML value was wrong; 0.0020 was verified from live account trades
    (BUY fills hold notional + fee: totalWithFee = price*qty*1.002).
    """
    rules = resolve_pair_rules(rules_data, "nonkyc", "BTC-USDT")
    assert rules.fees.maker_fee == 0.002
    assert rules.fees.taker_fee == 0.002


def test_kraken_block_parses(rules_data):
    """Kraken connector block exists and pairs resolve (Kraken addendum)."""
    assert "kraken" in rules_data["connectors"]
    rules = resolve_pair_rules(rules_data, "kraken", "XMR-USDT")
    assert rules.price_tick == 0.01
    assert rules.amount_step == 0.00000001
    assert rules.min_notional_quote == 0.5
    assert rules.min_order_size_base == 0.015
    assert rules.supports_post_only is True


def test_kraken_base_tier_when_volume_unknown(rules_data):
    """Tiered resolution returns base-tier maker when no tier is given."""
    rules = resolve_pair_rules(rules_data, "kraken", "XMR-USDT")
    assert rules.fees.maker_fee == 0.0025
    assert rules.fees.taker_fee == 0.0040


def test_kraken_named_tier_resolution(rules_data):
    """A named Kraken tier resolves its own fees."""
    rules = resolve_pair_rules(rules_data, "kraken", "XMR-USDT", tier="tier_250k")
    assert rules.fees.maker_fee == 0.0010
    assert rules.fees.taker_fee == 0.0020


def test_kraken_xmr_usd_pair_override(rules_data):
    """The USD-quoted Kraken pair resolves the same AssetPairs-derived rules."""
    rules = resolve_pair_rules(rules_data, "kraken", "XMR-USD")
    assert rules.price_tick == 0.01
    assert rules.min_notional_quote == 0.5
    assert rules.min_order_size_base == 0.015
    assert rules.fees.maker_fee == 0.0025


def test_tiered_fee_resolution_by_name(rules_data):
    """Mexc vip0 tier fees resolve correctly."""
    rules = resolve_pair_rules(rules_data, "mexc", "BTC-USDT", tier="vip0")
    assert rules.fees.maker_fee == 0.0002


def test_tiered_fee_resolution_vip1(rules_data):
    """Mexc vip1 tier fees resolve correctly."""
    rules = resolve_pair_rules(rules_data, "mexc", "BTC-USDT", tier="vip1")
    assert rules.fees.maker_fee == 0.00018


def test_pair_level_fee_override():
    """If a pair has its own fee block, it takes precedence."""
    # Create a custom YAML-like structure with pair-level fees
    rules_data = {
        "connectors": {
            "test_exchange": {
                "default": {
                    "price_tick": 0.01,
                    "amount_step": 0.01,
                    "min_notional_quote": 5.0,
                    "min_order_size_base": 0.0,
                    "max_order_size_base": None,
                    "fees": {
                        "mode": "static",
                        "maker_fee": 0.001,
                        "taker_fee": 0.002,
                    },
                },
                "pairs": {
                    "BTC-USDT": {
                        "price_tick": 0.01,
                        "amount_step": 0.001,
                        "min_notional_quote": 5.0,
                        "fees": {
                            "mode": "static",
                            "maker_fee": 0.0005,
                            "taker_fee": 0.0010,
                        },
                    },
                },
            }
        }
    }
    rules = resolve_pair_rules(rules_data, "test_exchange", "BTC-USDT")
    assert rules.fees.maker_fee == 0.0005
    assert rules.fees.taker_fee == 0.0010
