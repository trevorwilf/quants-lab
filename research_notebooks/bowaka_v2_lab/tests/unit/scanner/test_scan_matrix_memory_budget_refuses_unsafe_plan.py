"""The scan-matrix builder refuses to start when the budget would breach.

Matrix doc §9 / Phase 8.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_matrix import _estimate_matrix_size_gib
from bowaka_v2_lab.utils.memory_guard import MemoryBudget, MemoryReserveViolation
import pytest


def test_estimate_matrix_size_gib_scales_with_sessions():
    a = _estimate_matrix_size_gib(n_sessions=10, n_scans_per_session=100, n_symbols=100)
    b = _estimate_matrix_size_gib(n_sessions=100, n_scans_per_session=100, n_symbols=100)
    assert b >= 10 * a * 0.9  # roughly linear in n_sessions


def test_budget_refuses_200_gib_on_64_gib_machine():
    budget = MemoryBudget(
        total_ram_gib=64.0, reserve_system_gib=16.0,
        emergency_headroom_gib=8.0, postgres_gib_estimate=4.0,
        max_optuna_workers=8, worker_private_gib_estimate=4.0,
    )
    with pytest.raises(MemoryReserveViolation):
        budget.assert_launch_safe(feature_store_gib_estimate=200.0, n_workers=8)


def test_budget_passes_for_reasonable_matrix_on_192_gib():
    budget = MemoryBudget(total_ram_gib=192.0)
    # 8 workers x 6 GiB + 50 GiB matrix = 98 GiB; budget = 136 GiB. OK.
    budget.assert_launch_safe(feature_store_gib_estimate=50.0, n_workers=8)
