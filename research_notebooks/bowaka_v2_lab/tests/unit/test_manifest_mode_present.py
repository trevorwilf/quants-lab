"""run_manifest.json carries the simulation-mode contract + lineage (realism Phase 0).

The 16-file artifact contract names the run manifest `run_manifest.json`; the
prompt's `manifest.json` refers to it.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.cli_runners import run_backtest_command

_COUPLED = (
    "intraday_window_policy",
    "accepted_event_sequencing",
    "unknown_instrument_class_policy",
    "quote_fallback_policy",
)


def _smoke_run(tmp_path: Path, lab_root: Path) -> Path:
    cfg = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    run_dir = tmp_path / "run"
    run_backtest_command(cfg, smoke=True, run_dir=str(run_dir))
    return run_dir


def test_run_manifest_has_simulation_block(tmp_path: Path, lab_root: Path) -> None:
    run_dir = _smoke_run(tmp_path, lab_root)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert "simulation" in manifest, "run_manifest.json missing `simulation` block"
    assert manifest["simulation"]["mode"] == "smoke_fixture"
    for field in _COUPLED:
        assert field in manifest["simulation"], f"simulation block missing {field}"
        assert manifest["simulation"][field] is not None
    assert "allow_research_relaxed" in manifest["simulation"]


def test_run_manifest_has_lineage_hashes(tmp_path: Path, lab_root: Path) -> None:
    run_dir = _smoke_run(tmp_path, lab_root)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    lineage = manifest.get("lineage", {})
    for key in (
        "simulation_mode",
        "feed",
        "strategy_config_hash_actual",
        "lab_config_hash",
        "dataset_hash",
        "code_hash",
    ):
        assert key in lineage, f"run_manifest.json lineage missing {key}"
    assert lineage["simulation_mode"] == "smoke_fixture"


def test_report_header_lists_mode_and_lineage(tmp_path: Path, lab_root: Path) -> None:
    run_dir = _smoke_run(tmp_path, lab_root)
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    # Phase 8: the substantive renderer's header section is "## Header".
    assert "## Header" in report
    assert "simulation.mode" in report
    assert "smoke_fixture" in report
    assert "lab_config_hash" in report
    assert "dataset_hash" in report
    assert "code_hash" in report
