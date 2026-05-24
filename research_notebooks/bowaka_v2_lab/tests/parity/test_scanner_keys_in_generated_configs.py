"""Generated optuna configs must expose every live ``scanner:`` key.

Audit 2026-05-23 §P1-003. Pre-remediation the generated configs hid every
scanner key except ``max_candidates_per_scan`` / ``max_entries_per_scan`` /
``min_signal_strength``. After Phase 2 the generator iterates the contract's
scanner mapping so the configs grow automatically when the contract grows.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.reference import contract_available, load_actual_contract


pytestmark = pytest.mark.parity


_CONFIG_NAMES = (
    "bowaka_v2_actual_iex_intended_realism.yml",
    "bowaka_v2_actual_iex_intended_realism_optuna.yml",
    "bowaka_v2_actual_iex_current_code.yml",
    "bowaka_v2_actual_iex_current_code_optuna.yml",
    "bowaka_v2_actual_sip_intended_realism.yml",
    "bowaka_v2_actual_sip_intended_realism_optuna.yml",
)


@pytest.mark.parametrize("cfg_name", _CONFIG_NAMES)
def test_generated_config_exposes_every_live_scanner_key(cfg_name, lab_root):
    if not contract_available():
        pytest.xfail("frozen contract not present")
    actual = load_actual_contract().get("scanner") or {}
    cfg_path = lab_root / "configs" / cfg_name
    if not cfg_path.is_file():
        pytest.skip(f"{cfg_name} not present (re-run import-actual-config)")
    generated = yaml.safe_load(cfg_path.read_text(encoding="utf-8")).get("scanner") or {}
    missing = set(actual) - set(generated)
    assert not missing, f"{cfg_name} hides live scanner keys: {sorted(missing)}"


def test_generator_iterates_contract_scanner_mapping():
    """The contract->config mapper must copy every contract.scanner key.

    Invokes :func:`build_config_from_contract` directly (bypasses the strict
    Pydantic validator that would reject the synthetic key) and asserts every
    contract scanner key — including a synthetic ``signal_expiry_seconds``
    override added here — survives the mapping.
    """
    if not contract_available():
        pytest.xfail("frozen contract not present")
    from bowaka_v2_lab.reference.import_config import build_config_from_contract

    contract = load_actual_contract()
    synthetic = dict(contract.get("scanner") or {})
    # Use a *valid* scanner key with a synthetic value to prove the mapper
    # copies whatever is in the contract verbatim — not just the hard-coded
    # original three keys.
    synthetic["signal_expiry_seconds"] = 999
    synthetic["symbol_cooldown_minutes"] = 12345
    extended_contract = dict(contract)
    extended_contract["scanner"] = synthetic
    cfg = build_config_from_contract(
        extended_contract, feed="iex", mode="current_code_parity",
        feed_thresholds="actual", purpose="backtest",
    )
    assert cfg["scanner"]["signal_expiry_seconds"] == 999
    assert cfg["scanner"]["symbol_cooldown_minutes"] == 12345
    # And every original key still made it through.
    for key, value in synthetic.items():
        assert cfg["scanner"][key] == value, (
            f"the mapper dropped contract.scanner.{key}; expected {value}, "
            f"got {cfg['scanner'].get(key)!r}"
        )
