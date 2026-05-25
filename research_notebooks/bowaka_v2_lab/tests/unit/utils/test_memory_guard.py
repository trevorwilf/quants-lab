"""MemoryBudget utility (speedup report §11.1, matrix doc §9).

Phase 0 ships the utility unused; Phases 5/8/9 wire it. These tests pin the
budget semantics so a later edit can't loosen the operator's 32 GB reserve.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from bowaka_v2_lab.utils.memory_guard import MemoryBudget, MemoryReserveViolation


def test_from_system_returns_sane_defaults(monkeypatch):
    """``MemoryBudget.from_system()`` reads ``psutil.virtual_memory().total``."""
    import psutil

    fake_total_bytes = int(192 * (1024 ** 3))  # 192 GiB
    monkeypatch.setattr(
        psutil, "virtual_memory",
        lambda: SimpleNamespace(total=fake_total_bytes, available=fake_total_bytes),
    )
    budget = MemoryBudget.from_system()
    assert budget.total_ram_gib == pytest.approx(192.0)
    assert budget.reserve_system_gib == 32.0
    assert budget.max_optuna_workers == 8


def test_effective_bowaka_budget_subtracts_reserve_emergency_postgres():
    budget = MemoryBudget(
        total_ram_gib=192.0,
        reserve_system_gib=32.0,
        emergency_headroom_gib=16.0,
        postgres_gib_estimate=8.0,
    )
    assert budget.effective_bowaka_budget_gib() == pytest.approx(192 - 32 - 16 - 8)


def test_assert_launch_safe_passes_for_8_workers_on_192_gib():
    budget = MemoryBudget(total_ram_gib=192.0)
    # Default: 8 workers x 6 GiB = 48 GiB; budget = 192 - 32 - 16 - 8 = 136 GiB. OK.
    budget.assert_launch_safe(feature_store_gib_estimate=0.0)


def test_assert_launch_safe_passes_with_matrix_estimate():
    budget = MemoryBudget(total_ram_gib=192.0)
    # 48 (workers) + 50 (matrix) = 98 < 136 budget — fine.
    budget.assert_launch_safe(feature_store_gib_estimate=50.0)


def test_assert_launch_safe_raises_when_projection_exceeds_budget():
    budget = MemoryBudget(total_ram_gib=192.0)
    with pytest.raises(MemoryReserveViolation):
        budget.assert_launch_safe(feature_store_gib_estimate=200.0)


def test_assert_launch_safe_honours_n_workers_override():
    budget = MemoryBudget(total_ram_gib=64.0)  # smaller machine
    # 64 - 32 - 16 - 8 = 8 GiB. 8 workers x 6 = 48 → fail; 1 worker x 6 = 6 → pass.
    with pytest.raises(MemoryReserveViolation):
        budget.assert_launch_safe(feature_store_gib_estimate=0.0, n_workers=8)
    budget.assert_launch_safe(feature_store_gib_estimate=0.0, n_workers=1)


def test_assert_available_reserve_raises_when_low(monkeypatch):
    import psutil

    monkeypatch.setattr(
        psutil, "virtual_memory",
        lambda: SimpleNamespace(total=int(192 * 1024 ** 3), available=int(10 * 1024 ** 3)),
    )
    budget = MemoryBudget(total_ram_gib=192.0, reserve_system_gib=32.0)
    with pytest.raises(MemoryReserveViolation):
        budget.assert_available_reserve()


def test_assert_available_reserve_passes_when_plenty(monkeypatch):
    import psutil

    monkeypatch.setattr(
        psutil, "virtual_memory",
        lambda: SimpleNamespace(total=int(192 * 1024 ** 3), available=int(150 * 1024 ** 3)),
    )
    budget = MemoryBudget(total_ram_gib=192.0, reserve_system_gib=32.0)
    budget.assert_available_reserve()  # must not raise


def test_assert_available_reserve_accepts_custom_threshold(monkeypatch):
    import psutil

    monkeypatch.setattr(
        psutil, "virtual_memory",
        lambda: SimpleNamespace(total=int(192 * 1024 ** 3), available=int(20 * 1024 ** 3)),
    )
    budget = MemoryBudget(total_ram_gib=192.0)
    budget.assert_available_reserve(reserve_gib=10.0)  # 20 GiB available > 10 GiB — pass.
    with pytest.raises(MemoryReserveViolation):
        budget.assert_available_reserve(reserve_gib=64.0)


def test_memory_budget_is_frozen():
    """The budget dataclass is immutable — operators reconfigure by constructing
    a new instance, not by mutating an existing one."""
    budget = MemoryBudget(total_ram_gib=192.0)
    with pytest.raises(Exception):
        budget.reserve_system_gib = 0.0  # type: ignore[misc]
