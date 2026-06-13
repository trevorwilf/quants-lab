"""Every signal threshold in bowaka_v2_intended_realism.yml equals the contract.

Realism Phase 1, Task D. The generated intended-realism config copies all 16
signal-gate thresholds verbatim from the frozen contract
(``reference/actual_bowaka_v2_contract.yaml``); this proves they did not drift.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import reference
from bowaka_v2_lab.reference.import_config import SIGNAL_THRESHOLD_KEYS

_LAB_ROOT = Path(__file__).resolve().parents[2]
_REALISM_CONFIG = _LAB_ROOT / "configs" / "bowaka_v2_intended_realism.yml"


@pytest.fixture
def contract() -> dict:
    if not reference.contract_available():
        # P2/§6: a missing COMMITTED contract is a real drift-detection gap, not an
        # expected xfail. The contract is a committed artifact; if it's absent the
        # config-vs-contract parity simply isn't being checked -> fail loudly.
        pytest.fail(
            "frozen contract not generated (run mirror_bowaka_v2_source.ps1); the "
            "committed contract must be present so signal-threshold parity is checked."
        )
    return reference.load_actual_contract()


@pytest.fixture
def realism_signals() -> dict:
    assert _REALISM_CONFIG.is_file(), (
        f"{_REALISM_CONFIG} missing -- run `bowaka-v2-lab import-actual-config`"
    )
    cfg = yaml.safe_load(_REALISM_CONFIG.read_text(encoding="utf-8"))
    return cfg["signals"]


@pytest.mark.parametrize("gate", SIGNAL_THRESHOLD_KEYS)
def test_signal_threshold_matches_contract(
    gate: str, contract: dict, realism_signals: dict
) -> None:
    contract_value = contract["signals"].get(gate)
    lab_value = realism_signals.get(gate)
    assert lab_value == contract_value, (
        f"signals.{gate}: realism config = {lab_value!r}, contract = {contract_value!r}"
    )


def test_all_16_thresholds_present(realism_signals: dict) -> None:
    """The realism config must carry the full 16-threshold set."""
    for gate in SIGNAL_THRESHOLD_KEYS:
        assert gate in realism_signals, f"realism config signals missing {gate}"
    assert len(SIGNAL_THRESHOLD_KEYS) == 16
