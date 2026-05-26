"""The cached DQ path produces identical invariant-check results to legacy.

Speedup report v2 §4 P4 / §5.6 / Phase 3 task 6. With the cache flag on
the fold context carries the invariant half; the per-trial backtester
merges it with the trial-dependent half. The resulting report matches
the un-cached path for every invariant check.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.data_quality import dq_check_invariance
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def _make_cfg(lake: Path, symbols: list[str], *, cache: bool) -> dict:
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
            "acceleration": {"startup_dq_cache": {"enabled": bool(cache)}},
        },
    }


def test_cached_invariant_subset_matches_uncached_subset(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    symbols = ["AAA"]
    build_tiny_lake(lake, symbols, start=dt.date(2024, 1, 1), end=dt.date(2024, 4, 1))

    cfg_cached = _make_cfg(lake, symbols, cache=True)
    cfg_legacy = _make_cfg(lake, symbols, cache=False)
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

    cached_ctxs = build_fold_contexts(
        cfg_cached, plan, lake_root=lake, feed="iex", symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
    )
    legacy_ctxs = build_fold_contexts(
        cfg_legacy, plan, lake_root=lake, feed="iex", symbols=symbols,
        paths=paths, holdout_guard=holdout_guard,
    )

    # With cache off the fold context's startup_dq_report is None.
    for ctx in legacy_ctxs:
        if ctx is not None:
            assert ctx.startup_dq_report is None

    # With cache on each non-empty fold has an invariant-only DQ report.
    for cached, legacy in zip(cached_ctxs, legacy_ctxs):
        if cached is None and legacy is None:
            continue
        assert cached.startup_dq_report is not None, "cache flag enabled but report missing"
        for c in cached.startup_dq_report["checks"]:
            cls = dq_check_invariance(c["name"])
            assert cls == "invariant", (
                f"cached fold context carries non-invariant check {c['name']!r}"
                f" (classified as {cls})"
            )
