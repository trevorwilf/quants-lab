"""Phase 4 — end-to-end objective parity: disabled / compatibility / vectorized.

Speedup report v2 §10.6 task 8. Builds the fold contexts three ways and
asserts ``compute_objective`` produces equal FoldResult objectives to 1e-9
for all three runtime modes. The vectorized run requires a
verifier_version>=2 parity proof, written here.
"""
from __future__ import annotations

import datetime as dt
import json
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
from bowaka_v2_lab.scanner.scan_matrix import verify_scan_matrix
from tests.fixtures.scan_matrix_parity import build_matrix_parity_fixture


pytestmark = pytest.mark.slow


def _paths(tmp_path: Path, tag: str) -> BowakaV2Paths:
    lab = tmp_path / tag / "research_notebooks" / "bowaka_v2_lab"
    return BowakaV2Paths(
        lab_root=lab, data_root=lab / "data", artifact_root=lab / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _accel(mode: str, store_root: str):
    if mode == "disabled":
        return {"scan_matrix": {"enabled": False}}
    return {"scan_matrix": {
        "enabled": True, "runtime_mode": mode,
        # vectorized requires parity_manifest_present=True at the guard; the
        # verifier_version>=2 proof is the second gate.
        "require_parity_manifest": mode == "vectorized",
        "store_root": store_root,
    }}


def test_three_way_objective_parity(tmp_path, lab_root) -> None:
    fx = build_matrix_parity_fixture(tmp_path / "fx", lab_root)
    report = verify_scan_matrix(
        fx.store_root, fx.cfg_path, sample_count=50, vectorized_check=True,
    )
    assert report["status"] == "ok", report
    (Path(fx.store_root) / "parity_proof.json").write_text(
        json.dumps({"verifier_version": 2, "matrix_id": report["matrix_id"]}),
        encoding="utf-8",
    )
    lake = fx.lake
    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 5, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    base = dict(fx.cfg)
    base["market_data"] = dict(base.get("market_data") or {})
    base["market_data"]["shared_root"] = str(lake)

    objectives: dict[str, float] = {}
    for mode in ("disabled", "compatibility", "vectorized"):
        cfg = dict(base)
        cfg["optuna"] = dict(cfg.get("optuna") or {})
        cfg["optuna"]["acceleration"] = _accel(mode, str(fx.store_root))
        ctxs = build_fold_contexts(
            cfg, plan, lake_root=lake, feed="iex", symbols=["AAA"],
            paths=_paths(tmp_path, mode), holdout_guard=guard,
        )
        fr_list = []
        for i, split in enumerate(plan.splits):
            ctx = ctxs[i] if i < len(ctxs) else None
            if ctx is None:
                continue
            if mode != "disabled":
                assert ctx.scan_matrix_store is not None
            r = _run_fold_backtest_objective(
                cfg, val_start=split.val_start, val_end=split.val_end,
                lake_root=lake, feed="iex", symbols=["AAA"],
                paths=_paths(tmp_path, mode), ctx=ctx,
            )
            if r is None:
                continue
            fr_list.append(fold_result_from_backtest_result(
                f"f{i}_{split.val_start.isoformat()}", r,
            ))
        assert fr_list, f"no folds ran for mode={mode}"
        objectives[mode] = compute_objective(fr_list).objective

    assert objectives["disabled"] == pytest.approx(objectives["compatibility"], abs=1e-9)
    assert objectives["disabled"] == pytest.approx(objectives["vectorized"], abs=1e-9)
