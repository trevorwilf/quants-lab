"""``FoldRuntimeContext.daily_cache_by_session`` is not mutated by trials.

Speedup report §5.2 / §11.2 Phase 2. The precomputed daily cache is shared
across every trial. If a downstream code path mutated it (in place), trial N+1
would see contaminated state. Hash-stamp the per-session cache before and
after running multiple trials; the hashes must be unchanged.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import yaml

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _paths(tmp_path: Path):
    from bowaka_v2_lab.config.paths import BowakaV2Paths

    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _frame_hash(df: pd.DataFrame) -> int:
    return int(pd.util.hash_pandas_object(df, index=True).sum())


def test_daily_cache_unchanged_across_trials(tmp_path, lab_root):
    """Hash every per-session daily cache frame before and after a
    multi-trial study run; the hashes must match."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml", lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=3,
    )

    # Build contexts the same way run_walkforward_study does so the cache
    # hashes are taken against the same precomputed frames.
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 5, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        raw, plan, lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )

    pre_hashes: dict[str, int] = {}
    for ctx in contexts:
        if ctx is None:
            continue
        for sd, frame in ctx.daily_cache_by_session.items():
            pre_hashes[f"{ctx.fold_id}/{sd.isoformat()}"] = _frame_hash(frame)

    result = run_walkforward_study(cfg_path, allow_smoke=True)
    assert result["status"] == "ok"

    # Re-build contexts the SAME way and verify the hashes are stable —
    # this protects against accidental in-place mutation by trials.
    contexts_post = build_fold_contexts(
        raw, plan, lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    post_hashes: dict[str, int] = {}
    for ctx in contexts_post:
        if ctx is None:
            continue
        for sd, frame in ctx.daily_cache_by_session.items():
            post_hashes[f"{ctx.fold_id}/{sd.isoformat()}"] = _frame_hash(frame)
    assert pre_hashes == post_hashes
