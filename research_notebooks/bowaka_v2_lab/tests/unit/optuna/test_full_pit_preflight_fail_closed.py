"""Full-PIT preflight gate (audit 2026-05-23 §6.6 / Phase 1).

Under ``intended_realism`` the preflight must probe the *full* per-fold PIT
union (no 100-symbol cap) unless ``optuna.preflight.research_waiver_capped_symbols: true``
is set; in that case the study is permitted but tagged research-only.
``smoke_fixture`` and ``current_code_parity`` are unaffected.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest

from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.optuna.preflight import PreflightError


def _make_plan_with_two_folds():
    from bowaka_v2_lab.optuna.walkforward import (
        WalkForwardPlan,
        WalkForwardSplit,
    )

    splits = (
        WalkForwardSplit(
            train_start=dt.date(2023, 12, 1), train_end=dt.date(2024, 1, 1),
            val_start=dt.date(2024, 1, 2), val_end=dt.date(2024, 1, 5),
        ),
        WalkForwardSplit(
            train_start=dt.date(2023, 12, 8), train_end=dt.date(2024, 1, 8),
            val_start=dt.date(2024, 1, 9), val_end=dt.date(2024, 1, 12),
        ),
    )
    return WalkForwardPlan(
        splits=splits,
        final_holdout_start=dt.date(2024, 1, 15),
        final_holdout_end=dt.date(2024, 1, 19),
    )


def test_resolve_symbols_intended_realism_uses_full_pit_union(monkeypatch, tmp_path):
    """`_resolve_symbols(sim_mode='intended_realism', plan=plan)` returns the full
    PIT union, not a capped sample."""
    fake_union = {f"SYM{i:03d}" for i in range(250)}
    monkeypatch.setattr(
        walkforward_runner, "_resolve_symbols",
        walkforward_runner._resolve_symbols,  # use real impl
    )

    def _fake_plan_union(*args, **kwargs):
        return set(fake_union)

    monkeypatch.setattr(
        "bowaka_v2_lab.optuna.pit_universe.plan_pit_symbol_union",
        _fake_plan_union,
    )
    plan = _make_plan_with_two_folds()
    cfg = {"universe": {}, "optuna": {"preflight": {}}}
    md = {"minute_bar_source": "alpaca", "feed": "iex", "shared_root": str(tmp_path)}
    symbols = walkforward_runner._resolve_symbols(
        cfg, md, sim_mode="intended_realism", plan=plan,
    )
    assert set(symbols) == fake_union


def test_resolve_symbols_intended_realism_with_waiver_uses_capped(monkeypatch, tmp_path):
    """A research-only waiver returns the capped sample, not the PIT union."""
    monkeypatch.setattr(
        "bowaka_common.marketdata.available_symbols",
        # **kwargs so the mock tolerates production's adjustment= kwarg
        # (walkforward_runner._resolve_symbols passes adjustment=daily_adjustment_for_config).
        lambda root, timeframe, feed, **kwargs: [f"SYM{i:03d}" for i in range(500)],
    )
    plan = _make_plan_with_two_folds()
    cfg = {"universe": {},
           "optuna": {"preflight": {"research_waiver_capped_symbols": True}}}
    md = {"minute_bar_source": "alpaca", "feed": "iex", "shared_root": str(tmp_path)}
    symbols = walkforward_runner._resolve_symbols(
        cfg, md, sim_mode="intended_realism", plan=plan,
    )
    assert len(symbols) == 100  # the capped default


def test_resolve_symbols_smoke_unaffected(monkeypatch, tmp_path):
    """`smoke_fixture` keeps the legacy synthetic fallback."""
    plan = _make_plan_with_two_folds()
    cfg = {"universe": {}, "optuna": {"preflight": {}}}
    md = {"minute_bar_source": "fixture", "feed": "iex"}
    symbols = walkforward_runner._resolve_symbols(
        cfg, md, sim_mode="smoke_fixture", plan=plan,
    )
    assert symbols == ["AAA", "BBB", "CCC"]


def test_resolve_symbols_parity_uses_capped(monkeypatch, tmp_path):
    """`current_code_parity` uses the capped sample (its preflight is plumbing)."""
    monkeypatch.setattr(
        "bowaka_common.marketdata.available_symbols",
        # **kwargs so the mock tolerates production's adjustment= kwarg
        # (walkforward_runner._resolve_symbols passes adjustment=daily_adjustment_for_config).
        lambda root, timeframe, feed, **kwargs: [f"SYM{i:03d}" for i in range(500)],
    )
    plan = _make_plan_with_two_folds()
    cfg = {"universe": {}, "optuna": {"preflight": {}}}
    md = {"minute_bar_source": "alpaca", "feed": "iex", "shared_root": str(tmp_path)}
    symbols = walkforward_runner._resolve_symbols(
        cfg, md, sim_mode="current_code_parity", plan=plan,
    )
    assert len(symbols) == 100


def test_resolve_symbols_explicit_overrides_all(tmp_path):
    """An explicit `universe.symbols` list short-circuits everything."""
    plan = _make_plan_with_two_folds()
    cfg = {"universe": {"symbols": ["X", "Y", "Z"]}, "optuna": {"preflight": {}}}
    md = {"minute_bar_source": "alpaca", "feed": "iex", "shared_root": str(tmp_path)}
    symbols = walkforward_runner._resolve_symbols(
        cfg, md, sim_mode="intended_realism", plan=plan,
    )
    assert symbols == ["X", "Y", "Z"]
