"""``build_fold_contexts(...)`` produces identical daily caches in legacy + batch modes.

Speedup report v2 §4 P1 / Phase 1 task 5. The wiring layer in
``optuna/fold_context.py`` branches on
``optuna.acceleration.batch_daily_cache.enabled``; the resulting
``FoldRuntimeContext.daily_cache_by_session`` must be the same dict in both
modes.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def _build_minimal_cfg(lake: Path, symbols: list[str], *, batch: bool) -> dict:
    return {
        "simulation": {"mode": "smoke_fixture"},
        "market_data": {
            "feed": "iex", "shared_root": str(lake), "minute_bar_source": "fixture",
        },
        "universe": {"symbols": symbols, "min_adv_dollars": 0,
                     "min_price": 1.0, "max_price": 1_000.0},
        "backtest": {"start_date": "2024-01-01", "end_date": "2024-04-01",
                     "cost_stress": "conservative"},
        "optuna": {
            "n_trials": 1, "n_jobs": 1,
            "walkforward": {"train_months": 1, "val_months": 1,
                            "final_holdout_months": 1},
            "acceleration": {"batch_daily_cache": {"enabled": bool(batch)}},
        },
    }


def test_legacy_and_batch_fold_contexts_produce_identical_daily_caches(
    tmp_path: Path,
) -> None:
    lake = tmp_path / "lake"
    symbols = ["AAA", "BBB"]
    build_tiny_lake(lake, symbols, start=dt.date(2024, 1, 1), end=dt.date(2024, 4, 1))

    cfg_legacy = _build_minimal_cfg(lake, symbols, batch=False)
    cfg_batch = _build_minimal_cfg(lake, symbols, batch=True)
    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 4, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    legacy_ctxs = build_fold_contexts(
        cfg_legacy, plan, lake_root=lake, feed="iex", symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
    )
    batch_ctxs = build_fold_contexts(
        cfg_batch, plan, lake_root=lake, feed="iex", symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
    )

    assert len(legacy_ctxs) == len(batch_ctxs)
    for legacy, batch in zip(legacy_ctxs, batch_ctxs):
        if legacy is None and batch is None:
            continue
        assert legacy is not None and batch is not None
        l_cache = legacy.daily_cache_by_session
        b_cache = batch.daily_cache_by_session
        assert set(l_cache.keys()) == set(b_cache.keys())
        for s in l_cache:
            la = l_cache[s].reset_index(drop=True)
            ba = b_cache[s].reset_index(drop=True)
            assert list(la.columns) == list(ba.columns)
            assert la["symbol"].tolist() == ba["symbol"].tolist()
            for col in la.columns:
                if col == "symbol":
                    continue
                for va, vb in zip(la[col].tolist(), ba[col].tolist()):
                    assert abs(float(va) - float(vb)) <= 1e-12, (
                        f"session={s} col={col} legacy={va!r} batch={vb!r}"
                    )
