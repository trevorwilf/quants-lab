"""``FoldRuntimeContext`` matches the underlying per-fold setup.

Speedup report §5.2 / §11.2 Phase 2. The precomputed context is meaningful
ONLY if its sessions / PIT universe / daily cache match what the legacy
per-fold setup produces. The default search space (no overrides) is
exercised; the assertion is field-by-field equality.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.optuna.calendar_sessions import calendar_sessions_half_open
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def _paths(tmp_path: Path):
    from bowaka_v2_lab.config.paths import BowakaV2Paths

    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _plan_and_lake(tmp_path):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 5, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    return plan, lake


def test_contexts_sessions_match_half_open_helper(tmp_path):
    plan, lake = _plan_and_lake(tmp_path)
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        {"market_data": {"feed": "iex"}}, plan,
        lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    for i, split in enumerate(plan.splits):
        ctx = contexts[i]
        expected = calendar_sessions_half_open(split.val_start, split.val_end)
        if not expected:
            assert ctx is None
            continue
        assert ctx is not None
        assert list(ctx.sessions) == expected


def test_contexts_daily_cache_per_session_matches_direct_build(tmp_path):
    plan, lake = _plan_and_lake(tmp_path)
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        {"market_data": {"feed": "iex"}}, plan,
        lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake

    for ctx in contexts:
        if ctx is None:
            continue
        for sd in ctx.sessions:
            expected = build_daily_cache_from_lake(
                lake, list(ctx.eligible_symbols_by_session[sd]) or ["AAA"],
                sd, feed="iex",
            )
            got = ctx.daily_cache_by_session[sd]
            assert list(got.columns) == list(expected.columns)
            # Per-symbol prior_close should match exactly.
            assert got.equals(expected)


def test_contexts_universe_per_session_matches_direct_build(tmp_path):
    plan, lake = _plan_and_lake(tmp_path)
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        {"market_data": {"feed": "iex"}}, plan,
        lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    from bowaka_common.marketdata import MarketDataStore
    from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions

    store = MarketDataStore(lake)
    for ctx in contexts:
        if ctx is None:
            continue
        expected = build_pit_universe_for_sessions(
            list(ctx.sessions), {"market_data": {"feed": "iex"}}, store
        )
        for sd in ctx.sessions:
            assert ctx.universe_by_session[sd] == expected[sd]


def test_context_suppliers_are_shared_across_fold(tmp_path):
    """The per-fold supplier callables are constructed once per context
    (not per trial). The bundle exposes minute/daily/quote/forward_minute."""
    plan, lake = _plan_and_lake(tmp_path)
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        {"market_data": {"feed": "iex"}}, plan,
        lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    for ctx in contexts:
        if ctx is None:
            continue
        assert callable(ctx.suppliers.minute)
        assert callable(ctx.suppliers.daily)
        assert callable(ctx.suppliers.quote)
        assert callable(ctx.suppliers.forward_minute)


def test_context_is_frozen_immutable(tmp_path):
    """The dataclass is frozen so callers cannot mutate state held by
    other trials."""
    plan, lake = _plan_and_lake(tmp_path)
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    contexts = build_fold_contexts(
        {"market_data": {"feed": "iex"}}, plan,
        lake_root=lake, feed="iex", symbols=["AAA"],
        paths=_paths(tmp_path), holdout_guard=guard,
    )
    ctx = next((c for c in contexts if c is not None), None)
    assert ctx is not None
    with pytest.raises(Exception):
        ctx.feed = "sip"  # type: ignore[misc]
