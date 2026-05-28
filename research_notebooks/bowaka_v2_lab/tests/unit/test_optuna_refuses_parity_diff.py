"""Optuna refuses to start against an unannotated contract divergence.

Realism remediation 2 Phase 0 (audit §P0-001). A walk-forward Optuna study may
start only when its config is contract-parity clean OR every divergence is
declared in ``<config-stem>.parity_sidecar.yaml``. An undeclared divergence
raises before any (expensive) study work begins.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import reference
from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.config.parity_sidecar import ParitySidecar, write_parity_sidecar
from bowaka_v2_lab.optuna.walkforward_runner import (
    OptunaParityError,
    assert_optuna_config_parity,
    run_walkforward_study,
)

# tests/unit/<this file> -> tests -> bowaka_v2_lab
_LAB_ROOT = Path(__file__).resolve().parents[2]
_INTENDED = _LAB_ROOT / "configs" / "bowaka_v2_intended_realism.yml"


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


def _diverged_config(tmp_path: Path, name: str = "diverged.yml") -> Path:
    """An intended-realism config whose stop_pct diverges from the contract."""
    base = yaml.safe_load(_INTENDED.read_text(encoding="utf-8"))
    base["exits"]["stop_pct"] = 0.05  # contract is 0.025 (Phase 0 2026-05-27)
    dest = tmp_path / name
    dest.write_text(yaml.safe_dump(base), encoding="utf-8")
    return dest


def test_parity_gate_raises_on_undeclared_diff(tmp_path: Path) -> None:
    """The gate function raises OptunaParityError on an undeclared divergence."""
    cfg = load_config(_diverged_config(tmp_path))
    with pytest.raises(OptunaParityError, match="exits.stop_pct"):
        assert_optuna_config_parity(cfg)


def test_optuna_refuses_unannotated_parity_diff(tmp_path: Path) -> None:
    """Starting a study against an undeclared-divergent config raises."""
    diverged = _diverged_config(tmp_path, "wf_diverged.yml")
    # The parity gate runs before any plan building / lake probing — so this
    # raises without needing a market-data lake.
    with pytest.raises(OptunaParityError, match="exits.stop_pct"):
        run_walkforward_study(diverged, n_trials=1)


def test_parity_gate_passes_when_diff_is_declared(tmp_path: Path) -> None:
    """A divergence declared in the parity sidecar clears the gate."""
    diverged = _diverged_config(tmp_path, "wf_declared.yml")
    write_parity_sidecar(
        diverged,
        [
            ParitySidecar(
                field_path="exits.stop_pct",
                actual_value=0.025,
                lab_value=0.05,
                reason="experimental tighter stop — declared for the parity test",
                risk_classification="scoped",
            )
        ],
    )
    cfg = load_config(diverged)
    # No raise — the divergence is declared.
    assert_optuna_config_parity(cfg)


def test_parity_gate_passes_on_clean_intended_realism_config() -> None:
    """The shipped, generated intended-realism config clears the gate."""
    cfg = load_config(_INTENDED)
    assert_optuna_config_parity(cfg)
