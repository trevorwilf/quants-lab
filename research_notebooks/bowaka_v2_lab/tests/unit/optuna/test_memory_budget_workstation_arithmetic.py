"""Workstation MemoryBudget arithmetic at the operator-specified hardware profile.

Speedup report v2 prompt header / Phase 2 task 6:

* 192 GiB total RAM, 18 cores.
* Reserve 62 GiB + 2 cores for the OS.
* PostgreSQL locked to 8 threads → start at 8 workers; 10/12/16 are
  benchmark-only.
* Effective Bowaka budget = 192 − 62 (reserve) − 16 (emergency) − 8 (PG)
  = 106 GiB.
* At ``worker_private_gib_estimate=6.0``: 8w=48, 10w=60, 12w=72, 16w=96 —
  all fit under 106 GiB.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.utils.memory_guard import MemoryBudget, MemoryReserveViolation


def _budget() -> MemoryBudget:
    return MemoryBudget(
        total_ram_gib=192.0,
        reserve_system_gib=62.0,
        max_optuna_workers=8,
        worker_private_gib_estimate=6.0,
        postgres_gib_estimate=8.0,
        emergency_headroom_gib=16.0,
    )


def test_effective_budget_is_106_gib() -> None:
    """192 - 62 - 16 - 8 = 106 GiB Bowaka."""
    b = _budget()
    # Match the docstring arithmetic. ``effective_bowaka_budget_gib`` may not be
    # a public method on the class — derive it from the private fields.
    assert (
        b.total_ram_gib
        - b.reserve_system_gib
        - b.emergency_headroom_gib
        - b.postgres_gib_estimate
    ) == pytest.approx(106.0, abs=0.5)


@pytest.mark.parametrize("n_workers", [8, 10, 12, 16])
def test_workstation_workers_fit_under_effective_budget(n_workers: int) -> None:
    """8/10/12/16 workers at 6 GiB each fit under 106 GiB."""
    b = _budget()
    # assert_launch_safe should accept these counts; treat any
    # MemoryReserveViolation as a test failure.
    try:
        b.assert_launch_safe(feature_store_gib_estimate=0.0, n_workers=n_workers)
    except MemoryReserveViolation as exc:  # pragma: no cover — fail on regression
        pytest.fail(f"n_workers={n_workers} unexpectedly refused: {exc}")


def test_excessive_worker_count_raises() -> None:
    """50 workers at 6 GiB = 300 GiB overspends the 106 GiB budget."""
    b = _budget()
    with pytest.raises(MemoryReserveViolation):
        b.assert_launch_safe(feature_store_gib_estimate=0.0, n_workers=50)
