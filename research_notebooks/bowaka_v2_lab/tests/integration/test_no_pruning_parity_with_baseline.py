"""With pruning disabled the walk-forward result is unchanged.

Speedup report §6.2 / §11.2 Phase 7. Default config (no ``optuna.pruning``
block) must produce identical results to a config that explicitly sets
``optuna.pruning.enabled: false``.
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


def _write_cfg(tmp_path, lab_root, *, pruning_block: dict | None):
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / f"wf_{int(bool(pruning_block))}.yml",
        lake=tmp_path / "lake", symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if pruning_block is not None:
        raw["optuna"]["pruning"] = pruning_block
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return cfg_path


def test_no_pruning_block_matches_explicit_disabled(tmp_path, lab_root):
    build_tiny_lake(
        tmp_path / "lake", ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg_omit = _write_cfg(tmp_path, lab_root, pruning_block=None)
    cfg_disabled = _write_cfg(
        tmp_path, lab_root,
        pruning_block={"enabled": False, "catastrophic_floor": -0.5,
                        "min_completed_trials_before_pruning": 30},
    )
    r_omit = run_walkforward_study(cfg_omit, allow_smoke=True)
    r_disabled = run_walkforward_study(cfg_disabled, allow_smoke=True)
    assert r_omit["status"] == r_disabled["status"] == "ok"
    assert r_omit["n_folds"] == r_disabled["n_folds"]
    assert r_omit["n_trials_completed"] == r_disabled["n_trials_completed"]
    assert r_omit["best_value"] == pytest.approx(r_disabled["best_value"], abs=1e-9)
    assert json.dumps(r_omit["best_params"], sort_keys=True, default=str) == \
        json.dumps(r_disabled["best_params"], sort_keys=True, default=str)
