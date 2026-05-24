"""Full per-fold PIT eligible-universe union (audit 2026-05-23 §6.6 / Phase 1).

Pins ``fold_pit_symbol_union`` to compute the union across every session in a
half-open window and ``plan_pit_symbol_union`` to roll that up across folds +
final-holdout.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest

from bowaka_v2_lab.optuna import pit_universe


class _StubLakeStore:
    """Drop-in replacement for :class:`MarketDataStore` for the union tests."""


def _fake_build_pit_universe_for_sessions(per_session: dict[dt.date, dict[str, Any]]):
    """Return a stub for ``build_pit_universe_for_sessions`` that yields
    a controlled per-session universe."""

    def _impl(sessions, cfg, lake_store):  # noqa: ARG001
        return {sd: per_session.get(sd, {}) for sd in sessions}

    return _impl


def _record(symbol: str, eligible: bool = True):
    from bowaka_v2_lab.universe.builder import UniverseRecord

    return UniverseRecord(
        symbol=symbol,
        instrument_class="common_stock",
        venue_code="XNAS",
        prior_close=10.0,
        prior_avg_dollar_volume_20d=5_000_000.0,
        eligible_for_bowaka_equity_bucket=eligible,
        rejection_reasons=[] if eligible else ["test_rejection"],
        as_of_assets_snapshot_id="test",
        classification_basis="lake_master",
        exchange="NASDAQ",
    )


def test_fold_pit_symbol_union_unions_three_sessions(monkeypatch, tmp_path):
    """Union should accumulate symbols across each session in the half-open window."""
    s1 = dt.date(2024, 1, 2)  # Tue
    s2 = dt.date(2024, 1, 3)  # Wed
    s3 = dt.date(2024, 1, 4)  # Thu
    per_session = {
        s1: {"AAA": _record("AAA"), "BBB": _record("BBB")},
        s2: {"BBB": _record("BBB"), "CCC": _record("CCC")},
        s3: {"DDD": _record("DDD")},
    }
    monkeypatch.setattr(
        "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
        _fake_build_pit_universe_for_sessions(per_session),
    )
    monkeypatch.setattr(
        "bowaka_common.marketdata.MarketDataStore",
        lambda root: _StubLakeStore(),
    )
    union = pit_universe.fold_pit_symbol_union(
        tmp_path, feed="iex",
        fold_start=dt.date(2024, 1, 2), fold_end=dt.date(2024, 1, 5),  # half-open
    )
    assert union == {"AAA", "BBB", "CCC", "DDD"}


def test_fold_pit_symbol_union_drops_ineligible(monkeypatch, tmp_path):
    s1 = dt.date(2024, 1, 2)
    per_session = {s1: {"AAA": _record("AAA"), "BAD": _record("BAD", eligible=False)}}
    monkeypatch.setattr(
        "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
        _fake_build_pit_universe_for_sessions(per_session),
    )
    monkeypatch.setattr(
        "bowaka_common.marketdata.MarketDataStore",
        lambda root: _StubLakeStore(),
    )
    union = pit_universe.fold_pit_symbol_union(
        tmp_path, feed="iex",
        fold_start=dt.date(2024, 1, 2), fold_end=dt.date(2024, 1, 3),
    )
    assert union == {"AAA"}


def test_fold_pit_symbol_union_half_open_excludes_end_session(monkeypatch, tmp_path):
    """``[start, end)``: end-day session is NOT included (audit §P0-002)."""
    s1 = dt.date(2024, 1, 2)
    s2 = dt.date(2024, 1, 3)
    per_session = {
        s1: {"AAA": _record("AAA")},
        s2: {"BBB": _record("BBB")},
    }
    monkeypatch.setattr(
        "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
        _fake_build_pit_universe_for_sessions(per_session),
    )
    monkeypatch.setattr(
        "bowaka_common.marketdata.MarketDataStore",
        lambda root: _StubLakeStore(),
    )
    # half-open window: [s1, s2) -> only s1 in range.
    union = pit_universe.fold_pit_symbol_union(
        tmp_path, feed="iex",
        fold_start=s1, fold_end=s2,
    )
    assert union == {"AAA"}


def test_fold_pit_symbol_union_returns_empty_for_none_lake():
    union = pit_universe.fold_pit_symbol_union(
        None, feed="iex",
        fold_start=dt.date(2024, 1, 1), fold_end=dt.date(2024, 2, 1),
    )
    assert union == set()


def test_plan_pit_symbol_union_includes_holdout(monkeypatch, tmp_path):
    """Plan union should accumulate across every fold + the final holdout window."""
    from bowaka_v2_lab.optuna.walkforward import WalkForwardPlan, WalkForwardSplit

    splits = (
        WalkForwardSplit(
            train_start=dt.date(2023, 1, 1), train_end=dt.date(2024, 1, 1),
            val_start=dt.date(2024, 1, 2), val_end=dt.date(2024, 1, 3),
        ),
        WalkForwardSplit(
            train_start=dt.date(2023, 2, 1), train_end=dt.date(2024, 2, 1),
            val_start=dt.date(2024, 1, 3), val_end=dt.date(2024, 1, 4),
        ),
    )
    plan = WalkForwardPlan(
        splits=splits,
        final_holdout_start=dt.date(2024, 1, 4),
        final_holdout_end=dt.date(2024, 1, 5),
    )
    per_session = {
        dt.date(2024, 1, 2): {"AAA": _record("AAA")},
        dt.date(2024, 1, 3): {"BBB": _record("BBB")},
        dt.date(2024, 1, 4): {"CCC": _record("CCC")},
    }
    monkeypatch.setattr(
        "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
        _fake_build_pit_universe_for_sessions(per_session),
    )
    monkeypatch.setattr(
        "bowaka_common.marketdata.MarketDataStore",
        lambda root: _StubLakeStore(),
    )
    union = pit_universe.plan_pit_symbol_union(
        tmp_path, feed="iex", plan=plan, include_holdout=True,
    )
    assert union == {"AAA", "BBB", "CCC"}


def test_plan_pit_symbol_union_can_exclude_holdout(monkeypatch, tmp_path):
    from bowaka_v2_lab.optuna.walkforward import WalkForwardPlan, WalkForwardSplit

    splits = (
        WalkForwardSplit(
            train_start=dt.date(2023, 1, 1), train_end=dt.date(2024, 1, 1),
            val_start=dt.date(2024, 1, 2), val_end=dt.date(2024, 1, 3),
        ),
    )
    plan = WalkForwardPlan(
        splits=splits,
        final_holdout_start=dt.date(2024, 1, 4),
        final_holdout_end=dt.date(2024, 1, 5),
    )
    per_session = {
        dt.date(2024, 1, 2): {"AAA": _record("AAA")},
        dt.date(2024, 1, 4): {"HHH": _record("HHH")},
    }
    monkeypatch.setattr(
        "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
        _fake_build_pit_universe_for_sessions(per_session),
    )
    monkeypatch.setattr(
        "bowaka_common.marketdata.MarketDataStore",
        lambda root: _StubLakeStore(),
    )
    union = pit_universe.plan_pit_symbol_union(
        tmp_path, feed="iex", plan=plan, include_holdout=False,
    )
    assert union == {"AAA"}
