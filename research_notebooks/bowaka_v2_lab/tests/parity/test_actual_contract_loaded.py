"""The frozen contract exists, parses, and matches the live Bowaka v2 config.

Realism Phase 0. Requires ``reference/actual_bowaka_v2_contract.yaml`` (generated
by ``mirror_bowaka_v2_source.ps1`` -> ``python -m bowaka_v2_lab.reference``). The
``source_sha256`` cross-check additionally needs the live source resolvable; when
it is not, that one test xfails with a clear reason rather than fabricating data.
"""
from __future__ import annotations

import hashlib

import pytest

from bowaka_v2_lab import reference

# Durable spot-check values, pinned from the live bowaka_v2_config.yaml.
# A genuine live change to one of these requires regenerating the contract
# (mirror_bowaka_v2_source.ps1) and updating this table in the same commit.
#
# CHANGELOG:
# - 2026-05-21: initial pin.
# - 2026-06-12: prod re-mirror adopting OPTUNA WINNER TRIAL #3155 (2026-06-11)
#   re-tuned signals / sizing / risk / exits. The 11 values below marked
#   "#3155" updated from the regenerated contract; session/universe/scanner +
#   sizing_mode/bankroll_fixed_dollars are unchanged. The live-only
#   sizing.compounding block was preserved by the tuning (now modeled in the lab).
_EXPECTED: dict[tuple[str, str], object] = {
    ("session", "scanner_start"): "09:45",
    ("session", "scanner_end"): "15:30",
    ("universe", "price_max"): 20.0,
    ("universe", "avg_dollar_volume_min"): 250000,
    ("scanner", "max_candidates_per_scan"): 25,
    ("signals", "rvol_so_far_min"): 0.5008057683562838,            # #3155 (was 0.7)
    ("signals", "projected_full_day_rvol_min"): 1.864062376763409,  # #3155 (was 0.5)
    ("signals", "prior_atr_pct_min"): 0.10059887989166297,         # #3155 (was 0.06)
    ("signals", "close_location_so_far_min"): 0.7610800219990064,   # #3155 (was 0.60)
    ("sizing", "sizing_mode"): "equal_slice",
    ("sizing", "bankroll_fixed_dollars"): 90000,
    ("sizing", "max_concurrent_positions"): 1,                     # #3155 (was 18)
    ("sizing", "equal_slice_bankroll_fraction"): 0.7016473758770456,  # #3155 (was 0.80)
    ("risk", "daily_loss_pct"): 0.09182164526340102,              # #3155 (was 0.03)
    ("risk", "max_lots_per_symbol"): 4,                            # #3155 (was 3)
    ("exits", "stop_pct"): 0.10383796823643686,                   # #3155 (was 0.025)
    ("exits", "target_pct"): 0.4,                                  # #3155 (was 0.15)
    ("exits", "max_hold_days"): 10,                                # #3155 (was 3)
}


@pytest.fixture
def contract() -> dict:
    if not reference.contract_available():
        pytest.xfail(
            "frozen contract not generated -- run mirror_bowaka_v2_source.ps1 "
            "(or `python -m bowaka_v2_lab.reference`)"
        )
    return reference.load_actual_contract()


def test_contract_exists_and_parses(contract: dict) -> None:
    assert isinstance(contract, dict)
    assert contract.get("contract_schema_version") == reference.CONTRACT_SCHEMA_VERSION
    sha = contract.get("source_sha256")
    assert isinstance(sha, str) and len(sha) == 64
    for section in reference.CONTRACT_SECTIONS:
        assert section in contract, f"contract missing pinned section: {section}"


def test_contract_loaded_by_reference_loader(contract: dict) -> None:
    """Phase 0 acceptance: the reference loader parses the contract."""
    assert contract  # loaded via reference.load_actual_contract()
    assert len(reference.actual_contract_hash()) == 64  # sha256 of the file bytes


@pytest.mark.parametrize(
    "path,expected", list(_EXPECTED.items()), ids=[".".join(k) for k in _EXPECTED]
)
def test_contract_field_spotcheck(contract: dict, path: tuple, expected: object) -> None:
    section, key = path
    assert section in contract, f"contract missing section {section}"
    assert contract[section].get(key) == expected, (
        f"contract {section}.{key} = {contract[section].get(key)!r}, expected {expected!r}"
    )


def test_contract_source_sha256_matches_live(contract: dict) -> None:
    """Cross-check the embedded sha256 against the live config, when reachable."""
    live = reference.source_config_path()
    if live is None:
        pytest.xfail("live Bowaka v2 source not resolvable in this environment")
    live_sha = hashlib.sha256(live.read_bytes()).hexdigest()
    assert contract["source_sha256"] == live_sha, (
        "frozen contract has drifted from the live config -- regenerate with "
        "`python -m bowaka_v2_lab.reference`"
    )


def test_contract_adv_tier_caps_and_shadow_pinned(contract: dict) -> None:
    """Phase 0 task 1 requires risk.adv_tier_caps AND risk.shadow to be pinned."""
    risk = contract.get("risk", {})
    assert isinstance(risk.get("adv_tier_caps"), list) and risk["adv_tier_caps"]
    assert "shadow" in risk, "contract risk section must pin the `shadow` sub-block"
