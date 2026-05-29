"""Phase 3 (audit 2026-05-29 §6.10) — first-N trials write debug telemetry.

Under ``objective_minimal``, the incumbent + the first ``debug_first_n_trials``
sampled trials persist a per-trial debug record under
``artifacts/optuna/debug/trial_<N>.json``; later trials do not.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def test_first_three_trials_write_debug_artifacts(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=5,
    )
    # objective_minimal + debug_first_n_trials=3, no incumbent (so trial numbers
    # map cleanly: 0,1,2 escalate, 3,4 do not).
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc["optuna"]["objective_artifact_mode"] = "objective_minimal"
    doc["optuna"]["debug_first_n_trials"] = 3
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    run_walkforward_study(cfg_path, allow_smoke=True, incumbent_trial=False)

    debug_files = sorted(
        p.name for p in tmp_path.rglob("optuna/debug/trial_*.json")
    )
    assert "trial_0000.json" in debug_files
    assert "trial_0001.json" in debug_files
    assert "trial_0002.json" in debug_files
    assert "trial_0003.json" not in debug_files
    assert "trial_0004.json" not in debug_files
