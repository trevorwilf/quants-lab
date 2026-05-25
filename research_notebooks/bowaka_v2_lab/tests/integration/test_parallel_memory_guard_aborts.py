"""Memory budget refuses parallel launch when available reserve too low.

Speedup report §6.1 / §11.3 Phase 5. With ``strict_parallel=True`` the
launcher raises ``MemoryReserveViolation``; with the default
``strict_parallel=False`` it logs and falls back to serial.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from bowaka_v2_lab.optuna.dispatcher import run_bowaka_optimization_dispatch
from bowaka_v2_lab.utils.memory_guard import MemoryBudget, MemoryReserveViolation


def _stub_study():
    s = MagicMock(name="optuna.Study")
    s.optimize = MagicMock()
    return s


def test_strict_parallel_raises_when_projection_exceeds_budget():
    """8 workers × 6 GiB = 48 GiB on a 32-GiB machine cannot fit."""
    tiny_budget = MemoryBudget(
        total_ram_gib=32.0, reserve_system_gib=16.0,
        emergency_headroom_gib=8.0, postgres_gib_estimate=0.0,
        max_optuna_workers=8, worker_private_gib_estimate=6.0,
    )
    with pytest.raises(MemoryReserveViolation):
        run_bowaka_optimization_dispatch(
            study=_stub_study(), study_name="x",
            objective=lambda t: 0.0,
            objective_factory_dotted="some:thing",
            factory_kwargs={},
            n_trials=4, n_jobs=8,
            storage_url="postgresql+psycopg2://u:p@h:5432/d",
            memory_budget=tiny_budget,
            strict_parallel=True,
        )


def test_non_strict_parallel_falls_back_when_budget_violated(caplog):
    import logging

    tiny_budget = MemoryBudget(
        total_ram_gib=32.0, reserve_system_gib=16.0,
        emergency_headroom_gib=8.0, postgres_gib_estimate=0.0,
        max_optuna_workers=8, worker_private_gib_estimate=6.0,
    )
    study = _stub_study()
    caplog.set_level(logging.WARNING)
    run_bowaka_optimization_dispatch(
        study=study, study_name="x",
        objective=lambda t: 0.0,
        objective_factory_dotted="some:thing",
        factory_kwargs={},
        n_trials=4, n_jobs=8,
        storage_url="postgresql+psycopg2://u:p@h:5432/d",
        memory_budget=tiny_budget,
        strict_parallel=False,
    )
    study.optimize.assert_called_once()
    _, kwargs = study.optimize.call_args
    assert kwargs.get("n_jobs") == 1


def test_assert_available_reserve_blocks_launch_when_psutil_low(monkeypatch):
    """``run_parallel_bowaka_optimization`` rejects launch when available
    RAM is below the configured reserve."""
    import psutil

    monkeypatch.setattr(
        psutil, "virtual_memory",
        lambda: SimpleNamespace(total=int(192 * 1024 ** 3), available=int(4 * 1024 ** 3)),
    )
    from bowaka_v2_lab.optuna.parallel import run_parallel_bowaka_optimization

    budget = MemoryBudget(total_ram_gib=192.0, reserve_system_gib=32.0)
    with pytest.raises(MemoryReserveViolation):
        run_parallel_bowaka_optimization(
            study_name="x",
            storage_url="postgresql+psycopg2://u:p@h:5432/d",
            n_total_trials=1, n_workers=1,
            objective_factory_dotted="some:thing", factory_kwargs={},
            memory_budget=budget,
        )
