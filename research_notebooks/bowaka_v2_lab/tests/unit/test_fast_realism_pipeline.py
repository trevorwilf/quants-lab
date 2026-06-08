"""§10i Path 3 — the search→validate pipeline:
- ``derive_validation_config`` flips a fast_realism SEARCH config into an
  intended_realism VALIDATION config (mode + mode-coupled policy fields).
- the ``research_only`` suitability cap keeps a fast_realism result from deploying
  without re-validation under intended_realism.
"""
from __future__ import annotations

from bowaka_v2_lab.config.models import SimulationConfig
from bowaka_v2_lab.optuna.autoconfig import derive_validation_config
from bowaka_v2_lab.promotion.suitability import (
    SIMULATION_CONTRACTS, simulation_contract_of, tier_for_simulation_contract,
)


def test_fast_realism_capped_at_research_only():
    assert "fast_realism" in SIMULATION_CONTRACTS
    # search-only: a fast_realism result cannot promote past research...
    assert tier_for_simulation_contract("fast_realism") == "research_only"
    # ...the intended_realism validation gate is the one that can go higher.
    assert tier_for_simulation_contract("intended_realism") == "backtesting_only"
    assert simulation_contract_of({"simulation": {"mode": "fast_realism"}}) == "fast_realism"


def test_derive_validation_config_flips_mode_and_policies():
    search = {"simulation": {"mode": "fast_realism", "min_quote_coverage_pct": 80.0}}
    val = derive_validation_config(search)
    assert val["simulation"]["mode"] == "intended_realism"
    # operator's own knobs (the honest small-cap quote floor) carry over.
    assert val["simulation"]["min_quote_coverage_pct"] == 80.0
    # the dropped policy fields re-resolve to intended_realism's BLOCKING values.
    s_val = SimulationConfig.model_validate(val["simulation"])
    assert s_val.quote_fallback_policy == "require_real"
    assert s_val.unknown_instrument_class_policy == "fail_closed"
    # vs the search config, which resolves to the non-blocking fast_realism policies.
    s_search = SimulationConfig.model_validate(search["simulation"])
    assert s_search.quote_fallback_policy == "zero_spread"
    assert s_search.unknown_instrument_class_policy == "fail_open"


def test_derive_validation_config_custom_mode_and_no_input_mutation():
    search = {"simulation": {"mode": "fast_realism"}, "backtest": {"start_date": "2025-08-01"}}
    val = derive_validation_config(search, validation_mode="current_code_parity")
    assert val["simulation"]["mode"] == "current_code_parity"
    assert val["backtest"]["start_date"] == "2025-08-01"  # rest of the config preserved
    # the input dict is not mutated (deep-copied).
    assert search["simulation"]["mode"] == "fast_realism"
