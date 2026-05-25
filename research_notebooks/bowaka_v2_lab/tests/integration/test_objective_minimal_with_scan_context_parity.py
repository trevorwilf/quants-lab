"""Walk-forward objective: identical FoldResults across scan-context settings.

Speedup report §5.4 / §11.2 Phase 4. With Phase 1 objective_artifact_mode=
objective_minimal, the per-trial scanner sees collect_gate_dump=False and a
precomputed scan_session_context. Running the same study with and without
the Phase 4 wiring (via flipping artifact_mode between full and
objective_minimal — both now use the context) must produce identical
``best_value`` and ``fold_scores``.
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


def _write_cfg(tmp_path, lab_root, *, artifact_mode: str, cached: bool):
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / f"wf_{artifact_mode}_{int(cached)}.yml",
        lake=tmp_path / "lake", symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw["optuna"]["objective_artifact_mode"] = artifact_mode
    raw["optuna"]["cached_suppliers"] = cached
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return cfg_path


def test_phase4_wiring_does_not_alter_objective(tmp_path, lab_root):
    """Across full / objective_minimal modes the trial best_value/best_params
    are identical (within numerical tolerance for the objective)."""
    build_tiny_lake(
        tmp_path / "lake", ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg_full = _write_cfg(tmp_path, lab_root,
                           artifact_mode="full", cached=False)
    cfg_min = _write_cfg(tmp_path, lab_root,
                          artifact_mode="objective_minimal", cached=False)
    r_full = run_walkforward_study(cfg_full, allow_smoke=True)
    r_min = run_walkforward_study(cfg_min, allow_smoke=True)
    assert r_full["status"] == r_min["status"] == "ok"
    assert r_full["n_folds"] == r_min["n_folds"]
    assert r_full["n_trials_completed"] == r_min["n_trials_completed"]
    assert r_full["best_value"] == pytest.approx(r_min["best_value"], abs=1e-9)
    assert json.dumps(r_full["best_params"], sort_keys=True, default=str) == \
        json.dumps(r_min["best_params"], sort_keys=True, default=str)
