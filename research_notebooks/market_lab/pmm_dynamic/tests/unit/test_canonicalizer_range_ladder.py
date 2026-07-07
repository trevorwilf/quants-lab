"""range_ladder canonicalizer tests — including the Kraken addendum's
fee-parametric constraint scaling (floors read from exchange rules, never a
hardcoded 0.002)."""

from pathlib import Path

import pytest

from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.canonicalizer_range_ladder import (
    canonicalize_range_ladder_params,
    effective_min_order_quote,
)

YAML_PATH = Path(__file__).resolve().parents[2] / "configs" / "exchange_rules.yaml"


@pytest.fixture(scope="module")
def rules_db():
    return load_exchange_rules(yaml_path=YAML_PATH)


def _valid_params(**overrides):
    p = dict(
        n_buy=5, n_sell=5,
        buy_near_pct=0.02, buy_far_pct=0.20,
        sell_near_pct=0.02, sell_far_pct=0.20,
        buy_gamma=1.0, sell_gamma=1.0,
        k_buy=1.0, k_sell=1.0,
        fund_quote=1000.0, quote_frac=0.5,
        cooldown_time=3600, executor_refresh_time=43200,
    )
    p.update(overrides)
    return p


def _rules(maker=0.002, tick=0.01, min_notional=1.0, min_base=0.0):
    return PairRules(
        price_tick=tick, amount_step=0.001, min_notional_quote=min_notional,
        min_order_size_base=min_base,
        fees=FeeConfig(maker_fee=maker, taker_fee=maker),
    )


def test_valid_params_build_bundle():
    bundle, reason = canonicalize_range_ladder_params(
        _valid_params(), _rules(), 100.0, bar_interval_seconds=3600,
    )
    assert bundle is not None, reason
    cfg = bundle.strategy_config
    assert cfg.fee == 0.002                # from pair_rules, not hardcoded
    assert cfg.cooldown_bars == 1          # 3600 s cooldown at 1h bars
    assert cfg.fund_quote == 1000.0
    assert bundle.export_meta["controller_name"] == "range_inventory_ladder"
    assert bundle.engine_config.total_amount_quote == 1000.0
    assert bundle.engine_config.cooldown_time == 3600.0


def test_cooldown_bars_scale_with_interval():
    bundle, _ = canonicalize_range_ladder_params(
        _valid_params(), _rules(), 100.0, bar_interval_seconds=300,
    )
    assert bundle.strategy_config.cooldown_bars == 12  # 3600 / 300


def test_far_not_greater_than_near_rejected():
    bundle, reason = canonicalize_range_ladder_params(
        _valid_params(buy_far_pct=0.01), _rules(), 100.0,
    )
    assert bundle is None and "buy_far_pct" in reason
    bundle2, reason2 = canonicalize_range_ladder_params(
        _valid_params(sell_far_pct=0.01), _rules(), 100.0,
    )
    assert bundle2 is None and "sell_far_pct" in reason2


def test_rung_count_below_minimum_rejected():
    bundle, reason = canonicalize_range_ladder_params(
        _valid_params(n_buy=2), _rules(), 100.0,
    )
    assert bundle is None and "n_buy" in reason


def test_nonpositive_reference_price_rejected():
    bundle, reason = canonicalize_range_ladder_params(
        _valid_params(), _rules(), 0.0,
    )
    assert bundle is None and "reference_price" in reason


def test_dead_zone_floor_scales_with_connector_fee(rules_db):
    """Addendum §2: nonkyc (fee 0.002) floor 0.008; kraken (0.0025) floor 0.010.

    A dead zone of 0.009 passes nonkyc and fails kraken — using the REAL
    exchange_rules.yaml for both connectors.
    """
    params = _valid_params(buy_near_pct=0.0045, sell_near_pct=0.0045)
    nonkyc = resolve_pair_rules(rules_db, "nonkyc", "XMR-USDT")
    kraken = resolve_pair_rules(rules_db, "kraken", "XMR-USDT")
    assert nonkyc.fees.maker_fee == 0.002
    assert kraken.fees.maker_fee == 0.0025

    ok_bundle, ok_reason = canonicalize_range_ladder_params(
        params, nonkyc, 400.0, bar_interval_seconds=3600,
    )
    assert ok_bundle is not None, ok_reason

    ko_bundle, ko_reason = canonicalize_range_ladder_params(
        params, kraken, 400.0, bar_interval_seconds=3600,
    )
    assert ko_bundle is None
    assert "dead zone" in ko_reason


def test_min_order_quote_scales_with_connector(rules_db):
    """Addendum §2: kraken min-notional feasibility comes from Kraken's pair
    rules (ordermin 0.015 XMR ≈ $6 at $400), not nonkyc's 1 USDT."""
    nonkyc = resolve_pair_rules(rules_db, "nonkyc", "XMR-USDT")
    kraken = resolve_pair_rules(rules_db, "kraken", "XMR-USDT")
    assert effective_min_order_quote(nonkyc, 400.0) == 1.0
    assert effective_min_order_quote(kraken, 400.0) == pytest.approx(6.0)

    # A skewed 10-rung ladder is feasible at nonkyc's floor but not kraken's:
    # min normalized buy weight ≈ 0.0334 → 16.7 quote at fund 1000/quote 0.5;
    # at fund 300 that rung is 5.0 — above 1.0 (nonkyc), below 6.0 (kraken).
    params = _valid_params(n_buy=10, k_buy=4.0, fund_quote=300.0)
    ok_bundle, ok_reason = canonicalize_range_ladder_params(
        params, nonkyc, 400.0, bar_interval_seconds=3600,
    )
    assert ok_bundle is not None, ok_reason
    ko_bundle, ko_reason = canonicalize_range_ladder_params(
        params, kraken, 400.0, bar_interval_seconds=3600,
    )
    assert ko_bundle is None and "min_order_quote" in ko_reason


def test_effective_min_order_quote_uses_larger_bound():
    rules = _rules(min_notional=1.0, min_base=0.015)
    assert effective_min_order_quote(rules, 400.0) == pytest.approx(6.0)
    assert effective_min_order_quote(rules, 10.0) == 1.0  # notional floor binds
