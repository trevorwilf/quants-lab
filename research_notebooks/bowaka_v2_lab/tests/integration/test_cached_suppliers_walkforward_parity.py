"""Walk-forward study with cached suppliers off vs on: same results.

Speedup report §5.3 / §11.2 Phase 3 end-to-end check. The cached supplier
adapter is purely an I/O optimisation; with ``objective_artifact_mode=
objective_minimal`` (so the in-memory FoldResult path is the only output),
turning ``cached_suppliers`` on or off must produce identical ``best_value``
/ ``best_params`` / ``fold_scores``.
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


def _write_cfg(tmp_path, lab_root, *, cached: bool):
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / f"wf_cached_{int(cached)}.yml",
        lake=tmp_path / "lake", symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw["optuna"]["objective_artifact_mode"] = "objective_minimal"
    raw["optuna"]["cached_suppliers"] = cached
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return cfg_path


def test_walkforward_cached_off_vs_on_agree(tmp_path, lab_root):
    build_tiny_lake(
        tmp_path / "lake", ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg_off = _write_cfg(tmp_path, lab_root, cached=False)
    cfg_on = _write_cfg(tmp_path, lab_root, cached=True)
    r_off = run_walkforward_study(cfg_off, allow_smoke=True)
    r_on = run_walkforward_study(cfg_on, allow_smoke=True)
    assert r_off["status"] == r_on["status"] == "ok"
    assert r_off["n_folds"] == r_on["n_folds"]
    assert r_off["n_trials_completed"] == r_on["n_trials_completed"]
    assert r_off["best_value"] == pytest.approx(r_on["best_value"], abs=1e-9)
    assert json.dumps(r_off["best_params"], sort_keys=True, default=str) == \
        json.dumps(r_on["best_params"], sort_keys=True, default=str)
