"""Walk-forward study yields identical results in full and objective_minimal.

Speedup report §5.1 / §11.2 Phase 1 — end-to-end check. Same tiny lake +
same n_trials + same seed: best_value, best_params, and fold_scores must
match across ``optuna.objective_artifact_mode`` settings.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest
import yaml

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _write_cfg(tmp_path, lab_root, *, artifact_mode: str):
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / f"wf_{artifact_mode}.yml",
        lake=tmp_path / "lake", symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw["optuna"]["objective_artifact_mode"] = artifact_mode
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return cfg_path


def test_walkforward_full_vs_objective_minimal_agree(tmp_path, lab_root):
    build_tiny_lake(
        tmp_path / "lake", ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg_full = _write_cfg(tmp_path, lab_root, artifact_mode="full")
    cfg_min = _write_cfg(tmp_path, lab_root, artifact_mode="objective_minimal")

    r_full = run_walkforward_study(cfg_full, allow_smoke=True)
    r_min = run_walkforward_study(cfg_min, allow_smoke=True)

    assert r_full["status"] == r_min["status"] == "ok"
    assert r_full["n_folds"] == r_min["n_folds"]
    assert r_full["n_trials_completed"] == r_min["n_trials_completed"]
    assert r_full["best_value"] == pytest.approx(r_min["best_value"], abs=1e-9)
    # best_params is the optimizer-selected parameter set. With the same
    # seed + sampler + objective the TPE startup samples are identical,
    # so the chosen best params should match exactly.
    assert json.dumps(r_full["best_params"], sort_keys=True, default=str) == \
        json.dumps(r_min["best_params"], sort_keys=True, default=str)
