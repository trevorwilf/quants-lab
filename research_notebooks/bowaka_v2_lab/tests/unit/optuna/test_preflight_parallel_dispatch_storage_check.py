"""``preflight_parallel_dispatch`` refuses SQLite + n_jobs > 1.

Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 task 6. Process-parallel
Optuna against a SQLite study corrupts the database (concurrent writers).
The preflight helper refuses unconditionally for ``n_jobs > 1`` against
``sqlite:`` / in-memory URIs — strict_parallel does not gate this check
because SQLite-under-parallel is unsafe regardless. The only escape is
``n_jobs == 1`` (serial fallback).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.parallel import (
    ParallelDecision,
    preflight_parallel_dispatch,
)
from bowaka_v2_lab.utils.memory_guard import MemoryBudget


def _budget() -> MemoryBudget:
    return MemoryBudget(
        total_ram_gib=192.0,
        reserve_system_gib=62.0,
        max_optuna_workers=8,
        worker_private_gib_estimate=6.0,
        postgres_gib_estimate=8.0,
        emergency_headroom_gib=16.0,
    )


@pytest.mark.parametrize("strict_parallel", [True, False])
def test_sqlite_uri_with_njobs_gt_1_raises(strict_parallel: bool) -> None:
    """SQLite + parallel is unsafe regardless of strict_parallel."""
    study = MagicMock()
    with pytest.raises(OptunaStudyInvalidError, match=r"PostgreSQL|SQLite"):
        preflight_parallel_dispatch(
            study, n_jobs=4, storage_uri="sqlite:///tmp.db",
            mem_budget=_budget(), strict_parallel=strict_parallel,
        )


@pytest.mark.parametrize("strict_parallel", [True, False])
def test_none_uri_with_njobs_gt_1_raises(strict_parallel: bool) -> None:
    """In-memory (``storage_uri=None``) + parallel is unsafe regardless."""
    study = MagicMock()
    with pytest.raises(OptunaStudyInvalidError, match=r"PostgreSQL|SQLite"):
        preflight_parallel_dispatch(
            study, n_jobs=4, storage_uri=None,
            mem_budget=_budget(), strict_parallel=strict_parallel,
        )


def test_sqlite_uri_with_njobs_1_returns_serial() -> None:
    """Serial-on-SQLite is allowed (no concurrent writers)."""
    study = MagicMock()
    decision = preflight_parallel_dispatch(
        study, n_jobs=1, storage_uri="sqlite:///tmp.db",
        mem_budget=_budget(), strict_parallel=True,
    )
    assert decision.mode == "serial"
    assert decision.n_workers == 1


def test_postgres_uri_with_budget_returns_process_parallel() -> None:
    study = MagicMock()
    decision = preflight_parallel_dispatch(
        study, n_jobs=8,
        storage_uri="postgresql+psycopg2://localhost/optuna",
        mem_budget=_budget(), strict_parallel=False,
    )
    assert isinstance(decision, ParallelDecision)
    assert decision.mode == "process_parallel"
    assert decision.n_workers == 8
    assert decision.reason == "ok"
