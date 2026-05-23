"""Every generated walk-forward Optuna config is contract-parity-clean or sidecar-annotated.

Realism remediation 2 Phase 8 (audit §P0-001 finalization). The three shipping
optuna configs replace the quarantined ``bowaka_v2_walkforward_optuna.yml``;
each must either be contract-parity-clean against ``actual_bowaka_v2_contract.yaml``
or every divergence must be declared in ``<stem>.parity_sidecar.yaml``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab import reference
from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.config.parity_sidecar import (
    classify_config_parity,
    load_parity_sidecar,
)
from bowaka_v2_lab.optuna.walkforward_runner import (
    OptunaParityError,
    assert_optuna_config_parity,
)

_LAB_ROOT = Path(__file__).resolve().parents[2]

#: The three commit-shipped optuna configs the operator launches a study against.
_OPTUNA_CONFIGS = (
    "bowaka_v2_actual_iex_current_code_optuna.yml",
    "bowaka_v2_actual_iex_intended_realism_optuna.yml",
    "bowaka_v2_actual_sip_intended_realism_optuna.yml",
)


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_optuna_config_is_committed(name: str) -> None:
    """Every Phase-8 optuna config is committed to the configs/ directory."""
    assert (_LAB_ROOT / "configs" / name).is_file(), (
        f"{name} not committed — regenerate with "
        f"`python -m bowaka_v2_lab.cli import-actual-config --purpose optuna ...`"
    )


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_optuna_config_clean_or_annotated(name: str) -> None:
    """Each Phase-8 optuna config is contract-parity-clean or sidecar-annotated."""
    config_path = _LAB_ROOT / "configs" / name
    cfg = load_config(config_path)
    sidecar = load_parity_sidecar(config_path)
    result = classify_config_parity(
        {k: v for k, v in cfg.items() if k != "_source_path"},
        reference.load_actual_contract(),
        sidecar=sidecar,
    )
    assert not result["undeclared"], (
        f"{name} has undeclared contract divergences: {result['undeclared']}. "
        "Either reconcile the config to the contract or declare the diffs in "
        f"{name.removesuffix('.yml')}.parity_sidecar.yaml."
    )


@pytest.mark.parametrize("name", _OPTUNA_CONFIGS)
def test_assert_optuna_config_parity_admits_optuna_config(name: str) -> None:
    """The Phase-0 parity-gate function admits every committed optuna config."""
    config_path = _LAB_ROOT / "configs" / name
    cfg = load_config(config_path)
    # No raise — committed optuna configs clear the parity gate.
    assert_optuna_config_parity(cfg)
