"""P8 #5 / §4 — the contract universe FILTERS are mapped into the lab config.

The contract→config mapper omitted allowed_exchanges / exclude_otc /
ticker_blocklist / exclude_etf / exclude_etn, so the PIT builder fell back to
hard-coded defaults and config_diff (which only diffs SHARED keys) was blind to
the omission — the parity gate could not catch a lab/prod universe-filter drift.
These pin that the filters now round-trip the contract and validate.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.config.models import UniverseConfig
from bowaka_v2_lab.reference import contract_available, load_actual_contract
from bowaka_v2_lab.reference.import_config import build_config_from_contract

_FILTERS = ("allowed_exchanges", "exclude_otc", "ticker_blocklist",
            "exclude_etf", "exclude_etn")


def test_universe_config_accepts_filter_fields() -> None:
    u = UniverseConfig.model_validate({
        "allowed_exchanges": ["NASDAQ", "NYSE"], "exclude_otc": True,
        "ticker_blocklist": ["TSLL"], "exclude_etf": True, "exclude_etn": True,
    })
    assert u.allowed_exchanges == ["NASDAQ", "NYSE"]
    assert u.ticker_blocklist == ["TSLL"]
    assert u.exclude_otc and u.exclude_etf and u.exclude_etn


def test_universe_config_defaults_preserve_builder_fallbacks() -> None:
    u = UniverseConfig()
    assert u.allowed_exchanges is None      # builder falls back to DEFAULT_ALLOWED_EXCHANGES
    assert u.exclude_otc is True
    assert u.ticker_blocklist == []
    assert u.exclude_etf is True and u.exclude_etn is True


@pytest.mark.skipif(not contract_available(), reason="frozen contract not present")
def test_contract_universe_filters_are_mapped_and_diff_visible() -> None:
    contract = load_actual_contract()
    cfg = build_config_from_contract(contract, feed="sip", mode="intended_realism")
    u = cfg["universe"]
    c_u = contract.get("universe") or {}
    mapped_any = False
    for key in _FILTERS:
        if key in c_u:
            assert key in u, f"{key} not mapped -> config_diff is blind to it"
            assert u[key] == c_u[key]
            mapped_any = True
    assert mapped_any, "the frozen contract carries no universe filters to map"
    # The mapped universe round-trips through the (extra='forbid') schema.
    UniverseConfig.model_validate(u)
