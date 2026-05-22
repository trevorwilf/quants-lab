"""Every run artifact carries simulation_contract + suitability_tier.

Realism remediation 2 Phase 0. A smoke backtest's run_manifest.json and
report.json must both surface the simulation contract (== the simulation mode)
and the mechanical suitability tier at the top level.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.cli_runners import run_backtest_command
from bowaka_v2_lab.promotion.suitability import (
    SIMULATION_CONTRACTS,
    SUITABILITY_TIERS,
)


def _smoke_run(tmp_path: Path, lab_root: Path) -> Path:
    cfg = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    run_dir = tmp_path / "run"
    run_backtest_command(cfg, smoke=True, run_dir=str(run_dir))
    return run_dir


def test_run_manifest_has_simulation_contract_and_suitability_tier(
    tmp_path: Path, lab_root: Path
) -> None:
    run_dir = _smoke_run(tmp_path, lab_root)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("simulation_contract") in SIMULATION_CONTRACTS
    assert manifest["simulation_contract"] == "smoke_fixture"
    assert manifest.get("suitability_tier") in SUITABILITY_TIERS


def test_run_artifact_contains_simulation_contract_and_suitability_tier(
    tmp_path: Path, lab_root: Path
) -> None:
    """report.json (the top-level run report) has both fields."""
    run_dir = _smoke_run(tmp_path, lab_root)
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report.get("simulation_contract") in SIMULATION_CONTRACTS
    assert report["simulation_contract"] == "smoke_fixture"
    assert report.get("suitability_tier") in SUITABILITY_TIERS
    # smoke_fixture is mechanically capped at research_only.
    assert report["suitability_tier"] == "research_only"


def test_run_report_and_manifest_agree_on_labels(
    tmp_path: Path, lab_root: Path
) -> None:
    """The manifest and the report report the same contract + tier."""
    run_dir = _smoke_run(tmp_path, lab_root)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert manifest["simulation_contract"] == report["simulation_contract"]
    assert manifest["suitability_tier"] == report["suitability_tier"]
