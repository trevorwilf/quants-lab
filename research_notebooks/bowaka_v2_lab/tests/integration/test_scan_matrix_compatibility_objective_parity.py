"""Phase 3 — end-to-end objective parity: disabled vs compatibility runtime.

Speedup report v2 §10.5. Builds the walk-forward fold contexts twice — once
with the scan-matrix runtime disabled (legacy scanner) and once with
``runtime_mode="compatibility"`` + the matrix store attached — runs the
per-fold objective backtest for both, and asserts the resulting
``FoldResult.objective`` values are equal to 1e-9.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.objective import (
    compute_objective,
    fold_result_from_backtest_result,
)
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
from bowaka_v2_lab.optuna.walkforward_runner import _run_fold_backtest_objective
from tests.fixtures.scan_matrix_parity import build_matrix_parity_fixture


pytestmark = pytest.mark.slow


def _paths(tmp_path: Path, tag: str) -> BowakaV2Paths:
    lab = tmp_path / tag / "research_notebooks" / "bowaka_v2_lab"
    return BowakaV2Paths(
        lab_root=lab, data_root=lab / "data", artifact_root=lab / "artifacts",
        config_path=Path("ignored.yml"),
    )


def test_compatibility_objective_parity(tmp_path, lab_root) -> None:
    fx = build_matrix_parity_fixture(tmp_path / "fx", lab_root)
    lake = fx.lake

    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 5, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    base_cfg = dict(fx.cfg)
    base_cfg["market_data"] = dict(base_cfg.get("market_data") or {})
    base_cfg["market_data"]["shared_root"] = str(lake)

    # --- disabled (legacy scanner) ---
    cfg_off = dict(base_cfg)
    cfg_off["optuna"] = dict(cfg_off.get("optuna") or {})
    cfg_off["optuna"]["acceleration"] = {"scan_matrix": {"enabled": False}}
    ctx_off = build_fold_contexts(
        cfg_off, plan, lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path, "off"), holdout_guard=guard,
    )

    # --- compatibility (matrix-backed scanner) ---
    cfg_on = dict(base_cfg)
    cfg_on["optuna"] = dict(cfg_on.get("optuna") or {})
    cfg_on["optuna"]["acceleration"] = {
        "scan_matrix": {
            "enabled": True,
            "runtime_mode": "compatibility",
            "require_parity_manifest": False,
            "store_root": str(fx.store_root),
        }
    }
    ctx_on = build_fold_contexts(
        cfg_on, plan, lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path, "on"), holdout_guard=guard,
    )

    # Find the first fold with sessions in BOTH context tuples.
    ran = 0
    for i, split in enumerate(plan.splits):
        c_off = ctx_off[i] if i < len(ctx_off) else None
        c_on = ctx_on[i] if i < len(ctx_on) else None
        if c_off is None or c_on is None:
            continue
        # The compat context must have actually attached a matrix store.
        assert c_on.scan_matrix_store is not None, (
            "compat fold context did not open the scan-matrix store"
        )
        assert c_off.scan_matrix_store is None

        r_off = _run_fold_backtest_objective(
            cfg_off, val_start=split.val_start, val_end=split.val_end,
            lake_root=lake, feed="iex", symbols=["AAA"],
            paths=_paths(tmp_path, "off"), ctx=c_off,
        )
        r_on = _run_fold_backtest_objective(
            cfg_on, val_start=split.val_start, val_end=split.val_end,
            lake_root=lake, feed="iex", symbols=["AAA"],
            paths=_paths(tmp_path, "on"), ctx=c_on,
        )
        if r_off is None or r_on is None:
            continue
        fold_id = f"f{i}_{split.val_start.isoformat()}"
        fr_off = fold_result_from_backtest_result(fold_id, r_off)
        fr_on = fold_result_from_backtest_result(fold_id, r_on)
        assert compute_objective([fr_off]).objective == pytest.approx(
            compute_objective([fr_on]).objective, abs=1e-9
        )
        ran += 1

    assert ran > 0, "no validation fold had sessions to compare"
