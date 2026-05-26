"""``preflight_parallel_dispatch`` refuses overspend per :class:`MemoryBudget`.

Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 task 6. The 130 GiB Bowaka
effective budget at 6 GiB per worker fits 8/10/12/16 workers but refuses
≥ 22 workers (effective budget ÷ 6 GiB ≈ 21). In strict_parallel mode the
refusal raises; in non-strict mode it falls back to serial with the
violation reason in the decision.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.parallel import preflight_parallel_dispatch
from bowaka_v2_lab.utils.memory_guard import MemoryBudget


def _workstation_budget() -> MemoryBudget:
    return MemoryBudget(
        total_ram_gib=192.0,
        reserve_system_gib=62.0,
        max_optuna_workers=8,
        worker_private_gib_estimate=6.0,
        postgres_gib_estimate=8.0,
        emergency_headroom_gib=16.0,
    )


def test_8_workers_with_workstation_budget_is_viable() -> None:
    study = MagicMock()
    decision = preflight_parallel_dispatch(
        study, n_jobs=8,
        storage_uri="postgresql+psycopg2://localhost/optuna",
        mem_budget=_workstation_budget(), strict_parallel=False,
    )
    assert decision.mode == "process_parallel"
    assert decision.n_workers == 8


def test_overspend_strict_parallel_raises() -> None:
    """20 workers @ 6 GiB = 120 GiB; budget allows 130 GiB so still fits, but
    50 workers @ 6 GiB = 300 GiB which clearly overspends."""
    study = MagicMock()
    with pytest.raises(OptunaStudyInvalidError, match="strict_parallel"):
        preflight_parallel_dispatch(
            study, n_jobs=50,
            storage_uri="postgresql+psycopg2://localhost/optuna",
            mem_budget=_workstation_budget(), strict_parallel=True,
        )


def test_overspend_without_strict_parallel_falls_back_to_serial() -> None:
    study = MagicMock()
    decision = preflight_parallel_dispatch(
        study, n_jobs=50,
        storage_uri="postgresql+psycopg2://localhost/optuna",
        mem_budget=_workstation_budget(), strict_parallel=False,
    )
    assert decision.mode == "serial"
    assert decision.n_workers == 1
    assert "memory refused" in decision.reason
