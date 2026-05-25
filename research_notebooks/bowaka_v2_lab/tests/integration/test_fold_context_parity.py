"""Per-trial setup vs precomputed-context: same FoldResults.

Speedup report §5.2 / §11.2 Phase 2. For a fixed parameter set, running the
fold backtest with the legacy per-trial path (``ctx=None``) and the
precomputed context (``ctx=FoldRuntimeContext``) must produce identical
``FoldResult`` instances. Stability across modes is asserted for both
``artifact_mode="full"`` and ``"objective_minimal"``.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.objective import (
    compute_objective,
    fold_result_from_backtest_result,
    fold_result_from_report,
)
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
from bowaka_v2_lab.optuna.walkforward_runner import (
    _run_fold_backtest,
    _run_fold_backtest_objective,
)


def _paths(tmp_path: Path):
    from bowaka_v2_lab.config.paths import BowakaV2Paths

    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


@pytest.fixture
def setup(tmp_path):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 5, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    cfg = {
        "market_data": {"feed": "iex", "shared_root": str(lake)},
        "simulation": {"mode": "smoke_fixture"},
        "backtest": {"start_date": "2024-01-01", "end_date": "2024-05-01"},
        "universe": {"symbols": ["AAA"]},
        "strategy_version": "0.1.0",
    }
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        cfg, plan, lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    return tmp_path, lake, plan, cfg, contexts


def test_run_fold_backtest_with_and_without_ctx_match(setup):
    tmp_path, lake, plan, cfg, contexts = setup
    paths = _paths(tmp_path)

    split = plan.splits[0]
    ctx = contexts[0]
    if ctx is None:
        pytest.skip("tiny lake has no sessions in the first fold")

    legacy_summary = _run_fold_backtest(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake, feed="iex", symbols=["AAA"], paths=paths,
        return_report=True,
    )
    ctx_summary = _run_fold_backtest(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake, feed="iex", symbols=["AAA"], paths=paths,
        return_report=True, ctx=ctx,
    )

    fold_id = f"f0_{split.val_start.isoformat()}"
    fr_legacy = fold_result_from_report(fold_id, legacy_summary["_report"], legacy_summary)
    fr_ctx = fold_result_from_report(fold_id, ctx_summary["_report"], ctx_summary)

    for attr in (
        "net_return", "max_drawdown", "worst_day_loss", "turnover",
        "concentration", "n_trades", "ambiguous_bar_count",
        "missing_quote_count", "quote_coverage", "fill_rate",
    ):
        assert getattr(fr_legacy, attr) == pytest.approx(getattr(fr_ctx, attr)), (
            f"{attr} differs: legacy={getattr(fr_legacy, attr)!r} "
            f"ctx={getattr(fr_ctx, attr)!r}"
        )


def test_run_fold_backtest_objective_with_and_without_ctx_match(setup):
    tmp_path, lake, plan, cfg, contexts = setup
    paths = _paths(tmp_path)

    split = plan.splits[0]
    ctx = contexts[0]
    if ctx is None:
        pytest.skip("tiny lake has no sessions in the first fold")

    r_legacy = _run_fold_backtest_objective(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake, feed="iex", symbols=["AAA"], paths=paths,
    )
    r_ctx = _run_fold_backtest_objective(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake, feed="iex", symbols=["AAA"], paths=paths,
        ctx=ctx,
    )
    assert r_legacy is not None and r_ctx is not None
    fold_id = f"f0_{split.val_start.isoformat()}"
    fr_legacy = fold_result_from_backtest_result(fold_id, r_legacy)
    fr_ctx = fold_result_from_backtest_result(fold_id, r_ctx)

    for attr in (
        "net_return", "max_drawdown", "worst_day_loss", "n_trades",
        "missing_quote_count", "quote_coverage", "fill_rate",
    ):
        assert getattr(fr_legacy, attr) == pytest.approx(getattr(fr_ctx, attr))
    assert compute_objective([fr_legacy]).objective == pytest.approx(
        compute_objective([fr_ctx]).objective, abs=1e-9
    )


def test_walkforward_study_with_contexts_matches_without(tmp_path, lab_root):
    """End-to-end: same study run twice, both already use Phase 2 contexts
    by default — assert the result is byte-stable across two consecutive
    runs (regression check on the Phase 2 wiring itself)."""
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml", lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    r1 = run_walkforward_study(cfg_path, allow_smoke=True)
    r2 = run_walkforward_study(cfg_path, allow_smoke=True)
    assert r1["status"] == r2["status"] == "ok"
    assert r1["best_value"] == pytest.approx(r2["best_value"], abs=1e-9)
    assert r1["n_folds"] == r2["n_folds"]
    assert json.dumps(r1["best_params"], sort_keys=True, default=str) == \
        json.dumps(r2["best_params"], sort_keys=True, default=str)
