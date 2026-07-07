"""range_ladder YAML export + mirror-validator tests (incl. kraken XMR-USD)."""

from pathlib import Path

import numpy as np
import pytest
import yaml

from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.export.hb_yaml_range_ladder import (
    RangeLadderExportParams,
    export_range_ladder_yaml,
    incumbent_yaml_path,
    load_range_ladder_incumbent,
    weights_to_pct,
)
from pmm_lab.export.validate_export import validate_yaml_file
from pmm_lab.strategies.range_ladder import RangeLadderConfig

YAML_PATH = Path(__file__).resolve().parents[2] / "configs" / "exchange_rules.yaml"
INCUMBENTS_DIR = Path(__file__).resolve().parents[2] / "configs" / "incumbents"


def _config(**overrides):
    base = dict(
        n_buy=5, n_sell=5,
        buy_near_pct=0.02, buy_far_pct=0.15,
        sell_near_pct=0.02, sell_far_pct=0.15,
        buy_gamma=1.0, sell_gamma=1.0, k_buy=1.0, k_sell=-0.5,
        fund_quote=1000.0, fee=0.002,
    )
    base.update(overrides)
    return RangeLadderConfig(**base)


def _rules(maker=0.002, tick=0.01):
    return PairRules(
        price_tick=tick, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=maker, taker_fee=maker),
    )


def _export(tmp_path, config=None, rules=None, connector="nonkyc",
            pair="XMR-USDT", anchor=400.0, **kw):
    config = config or _config()
    rules = rules or _rules()
    out = tmp_path / f"{pair}_1h_screening_best.yml"
    export_range_ladder_yaml(
        config, anchor, rules,
        RangeLadderExportParams(connector_name=connector, trading_pair=pair),
        out, **kw,
    )
    return out


def test_export_schema_and_ordering(tmp_path):
    out = _export(tmp_path)
    with open(out) as f:
        d = yaml.safe_load(f)
    assert d["id"]
    assert d["controller_name"] == "range_inventory_ladder"
    assert d["controller_type"] == "market_making"
    assert d["connector_name"] == "nonkyc"
    assert d["trading_pair"] == "XMR-USDT"
    buys, sells = d["buy_prices"], d["sell_prices"]
    assert all(buys[i] > buys[i + 1] for i in range(len(buys) - 1)), "buys highest→lowest"
    assert all(sells[i] < sells[i + 1] for i in range(len(sells) - 1)), "sells lowest→highest"
    assert max(buys) < min(sells)
    # tick-quantized absolute prices
    for p in buys + sells:
        assert abs(p / 0.01 - round(p / 0.01)) < 1e-6
    # frozen Phase A timing, integer-typed
    assert d["executor_refresh_time"] == 43200
    assert d["buy_cooldown_time"] == 3600
    assert d["sell_cooldown_time"] == 3600
    for k in ("executor_refresh_time", "buy_cooldown_time", "sell_cooldown_time"):
        assert isinstance(d[k], int)
    assert d["fee_rate"] == 0.002
    assert d["min_order_quote"] == 1.0
    assert d["allow_partial_levels"] is True
    assert d["passive_order_placement"] is True
    assert d["event_refresh_enabled"] is True


def test_export_weights_sum_exactly_100(tmp_path):
    out = _export(tmp_path)
    with open(out) as f:
        d = yaml.safe_load(f)
    assert sum(d["buy_amounts_pct"]) == pytest.approx(100.0, abs=1e-9)
    assert sum(d["sell_amounts_pct"]) == pytest.approx(100.0, abs=1e-9)
    for p in d["buy_amounts_pct"] + d["sell_amounts_pct"]:
        assert p == round(p, 1)


def test_weights_to_pct_residual_adjustment():
    # Three equal weights → 33.3 each = 99.9; the largest absorbs the +0.1
    pct = weights_to_pct(np.array([1.0, 1.0, 1.0]))
    assert sum(pct) == pytest.approx(100.0, abs=1e-9)


def test_export_validates_with_mirror_validator(tmp_path):
    out = _export(tmp_path)
    vr = validate_yaml_file(str(out), price_tick=0.01)
    assert vr.valid, vr.errors
    assert vr.mode == "mirror"


def test_export_kraken_xmr_usd(tmp_path):
    """Addendum §3: a USD-quoted Kraken pair exports and validates cleanly."""
    rules_db = load_exchange_rules(yaml_path=YAML_PATH)
    kraken_rules = resolve_pair_rules(rules_db, "kraken", "XMR-USD")
    config = _config(fee=kraken_rules.fees.maker_fee, fund_quote=2000.0)
    out = _export(
        tmp_path, config=config, rules=kraken_rules,
        connector="kraken", pair="XMR-USD", anchor=350.0,
    )
    with open(out) as f:
        d = yaml.safe_load(f)
    assert d["connector_name"] == "kraken"
    assert d["trading_pair"] == "XMR-USD"
    assert d["fee_rate"] == 0.0025
    assert d["min_order_quote"] == 0.5
    vr = validate_yaml_file(str(out), price_tick=kraken_rules.price_tick)
    assert vr.valid, vr.errors


def test_export_literal_ladder(tmp_path):
    config = RangeLadderConfig(
        fund_quote=1000.0, fee=0.002,
        literal_buy_prices=(32.851, 32.112, 31.3395, 30.6005, 29.8615),
        literal_buy_weights=(7.6, 11.4, 17.1, 25.6, 38.4),
        literal_sell_prices=(36.1764, 38.7965, 41.3829, 43.9693, 46.5893),
        literal_sell_weights=(39.9, 25.8, 16.6, 10.7, 6.9),
    )
    out = _export(tmp_path, config=config, pair="DASH-USDT", anchor=34.0)
    with open(out) as f:
        d = yaml.safe_load(f)
    assert d["buy_prices"][0] == 32.851
    assert d["sell_prices"][0] == 36.1764


# ----------------------------------------------------------------------
# Validator failure paths
# ----------------------------------------------------------------------

def _tamper(tmp_path, mutate):
    out = _export(tmp_path)
    with open(out) as f:
        d = yaml.safe_load(f)
    mutate(d)
    with open(out, "w") as f:
        yaml.safe_dump(d, f, sort_keys=False)
    return validate_yaml_file(str(out), price_tick=0.01)


def test_validator_rejects_bad_weight_sum(tmp_path):
    vr = _tamper(tmp_path, lambda d: d["buy_amounts_pct"].__setitem__(0, 50.0))
    assert not vr.valid
    assert any("sums to" in e for e in vr.errors)


def test_validator_rejects_cross_side_overlap(tmp_path):
    vr = _tamper(tmp_path, lambda d: d["buy_prices"].__setitem__(0, d["sell_prices"][0] + 1))
    assert not vr.valid
    assert any("overlap" in e for e in vr.errors)


def test_validator_rejects_unsorted_buys(tmp_path):
    def flip(d):
        d["buy_prices"] = list(sorted(d["buy_prices"]))
    vr = _tamper(tmp_path, flip)
    assert not vr.valid
    assert any("descending" in e for e in vr.errors)


def test_validator_rejects_non_int_cooldown(tmp_path):
    vr = _tamper(tmp_path, lambda d: d.__setitem__("buy_cooldown_time", 3600.0))
    assert not vr.valid
    assert any("buy_cooldown_time" in e for e in vr.errors)


def test_validator_rejects_sub_min_rung_notional(tmp_path):
    vr = _tamper(tmp_path, lambda d: d.__setitem__("total_amount_quote", 10.0))
    assert not vr.valid
    assert any("min_order_quote" in e for e in vr.errors)


def test_validator_rejects_off_tick_price(tmp_path):
    vr = _tamper(tmp_path, lambda d: d["buy_prices"].__setitem__(1, d["buy_prices"][1] + 0.001))
    assert not vr.valid
    assert any("not quantized" in e for e in vr.errors)


def test_validator_rejects_missing_key(tmp_path):
    vr = _tamper(tmp_path, lambda d: d.pop("id"))
    assert not vr.valid
    assert any("Missing required key: id" in e for e in vr.errors)


# ----------------------------------------------------------------------
# Incumbent loader
# ----------------------------------------------------------------------

def test_incumbent_path_convention():
    p = incumbent_yaml_path(INCUMBENTS_DIR, "nonkyc", "DASH-USDT")
    assert p.name == "nonkyc__DASH-USDT.yml"


def test_load_seeded_dash_incumbent():
    inc = load_range_ladder_incumbent(
        incumbent_yaml_path(INCUMBENTS_DIR, "nonkyc", "DASH-USDT")
    )
    assert inc is not None
    assert inc["buy_prices"] == [32.851, 32.112, 31.3395, 30.6005, 29.8615]
    assert inc["buy_weights"] == [7.6, 11.4, 17.1, 25.6, 38.4]
    assert inc["sell_prices"] == [36.1764, 38.7965, 41.3829, 43.9693, 46.5893]
    assert inc["sell_weights"] == [39.9, 25.8, 16.6, 10.7, 6.9]


def test_load_seeded_sun_incumbent():
    inc = load_range_ladder_incumbent(
        incumbent_yaml_path(INCUMBENTS_DIR, "nonkyc", "SUN-USDT")
    )
    assert inc is not None
    assert len(inc["buy_prices"]) == 5 and len(inc["sell_prices"]) == 5


def test_missing_incumbent_returns_none():
    """Addendum §3: the incumbent machinery must degrade gracefully."""
    inc = load_range_ladder_incumbent(
        incumbent_yaml_path(INCUMBENTS_DIR, "kraken", "XMR-USDT")
    )
    assert inc is None
