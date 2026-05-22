"""The `config-parity` CLI subcommand (realism remediation 2 Phase 0).

`bowaka-v2-lab config-parity --config <path>` diffs a config against the frozen
contract and exits non-zero on any *undeclared* divergence. A diff declared in
``<config-stem>.parity_sidecar.yaml`` is not a violation.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import cli, reference
from bowaka_v2_lab.config.parity_sidecar import ParitySidecar, write_parity_sidecar

# tests/parity/<this file> -> tests -> bowaka_v2_lab
_LAB_ROOT = Path(__file__).resolve().parents[2]
_INTENDED = _LAB_ROOT / "configs" / "bowaka_v2_intended_realism.yml"


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


def test_config_parity_cli_clean_on_generated_intended_realism(capsys) -> None:
    """The generated intended-realism config is contract-parity clean -> exit 0."""
    assert _INTENDED.is_file(), f"{_INTENDED} missing -- run import-actual-config"
    rc = cli.main(["config-parity", "--config", str(_INTENDED)])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"parity_clean": true' in out
    assert '"undeclared_diffs": []' in out


def test_config_parity_cli_fails_on_undeclared_diff(tmp_path: Path, capsys) -> None:
    """A config that changes stop_pct with no sidecar -> non-zero exit + listing."""
    base = yaml.safe_load(_INTENDED.read_text(encoding="utf-8"))
    base["exits"]["stop_pct"] = 0.05  # contract is 0.08
    diverged = tmp_path / "diverged.yml"
    diverged.write_text(yaml.safe_dump(base), encoding="utf-8")

    rc = cli.main(["config-parity", "--config", str(diverged)])
    assert rc == 1  # non-zero — undeclared divergence
    out = capsys.readouterr().out
    assert '"parity_clean": false' in out
    assert "exits.stop_pct" in out
    assert '"status": "parity_violation"' in out


def test_config_parity_cli_clean_when_diff_is_declared(tmp_path: Path, capsys) -> None:
    """The same divergence, declared in a parity_sidecar.yaml, exits 0."""
    base = yaml.safe_load(_INTENDED.read_text(encoding="utf-8"))
    base["exits"]["stop_pct"] = 0.05
    diverged = tmp_path / "declared.yml"
    diverged.write_text(yaml.safe_dump(base), encoding="utf-8")
    write_parity_sidecar(
        diverged,
        [
            ParitySidecar(
                field_path="exits.stop_pct",
                actual_value=0.08,
                lab_value=0.05,
                reason="experimental tighter stop — declared for the parity test",
                risk_classification="scoped",
            )
        ],
    )
    rc = cli.main(["config-parity", "--config", str(diverged)])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"parity_clean": true' in out
    assert "scoped" in out
