"""Memory budget utility for Bowaka v2 lab parallel/precompute launchers.

Per matrix doc §9: the operator hardware has 192 GB RAM and 18 primary cores;
**32 GB must remain reserved** for non-Bowaka activity at all times. Optuna
workers are capped at 8 (so 8 × ~6 GB worker private + matrix mmap + Postgres
+ emergency headroom fits under the budget). Every parallel launcher
(walk-forward dispatch in Phase 5, the scan matrix builder in Phase 8, the
matrix-backed scanner in Phase 9) must call :meth:`MemoryBudget.assert_launch_safe`
before launching workers and :meth:`MemoryBudget.assert_available_reserve`
during the run.

Phase 0 only **adds** this module — it is unit-tested but no call sites are
wired yet. Phases 5/8/9 take it as a dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class MemoryReserveViolation(RuntimeError):
    """Raised when an action would breach the configured memory reserve."""


@dataclass(frozen=True)
class MemoryBudget:
    """Operator-tunable RAM budget for the Bowaka v2 lab parallel launchers.

    Defaults reflect the operator hardware (192 GB RAM, 18 cores) with a hard
    32 GB system reserve and 8-worker cap for Optuna. The estimates are coarse
    and intentionally conservative; the goal is to refuse obviously-unsafe
    plans, not to micro-budget.
    """

    total_ram_gib: float
    reserve_system_gib: float = 32.0
    max_optuna_workers: int = 8
    worker_private_gib_estimate: float = 6.0
    postgres_gib_estimate: float = 8.0
    emergency_headroom_gib: float = 16.0

    @classmethod
    def from_system(cls, **overrides) -> "MemoryBudget":
        """Construct a :class:`MemoryBudget` reading total RAM from ``psutil``.

        Overrides any field by keyword. Defaults are the operator's hardware.
        """
        import psutil

        total_bytes = int(psutil.virtual_memory().total)
        total_gib = total_bytes / (1024.0 ** 3)
        kwargs: dict[str, object] = {"total_ram_gib": total_gib}
        kwargs.update(overrides)
        return cls(**kwargs)  # type: ignore[arg-type]

    def effective_bowaka_budget_gib(self) -> float:
        """Bytes available to all Bowaka processes combined.

        Total minus system reserve minus emergency headroom minus Postgres.
        """
        budget = (
            float(self.total_ram_gib)
            - float(self.reserve_system_gib)
            - float(self.emergency_headroom_gib)
            - float(self.postgres_gib_estimate)
        )
        return max(0.0, budget)

    def projected_worker_use_gib(self, n_workers: Optional[int] = None) -> float:
        """Estimated steady-state worker RAM (all workers combined)."""
        n = self.max_optuna_workers if n_workers is None else int(n_workers)
        return float(self.worker_private_gib_estimate) * max(0, n)

    def assert_launch_safe(
        self,
        feature_store_gib_estimate: float = 0.0,
        *,
        n_workers: Optional[int] = None,
    ) -> None:
        """Raise :class:`MemoryReserveViolation` if launching would breach the budget.

        Projected use = ``n_workers * worker_private_gib_estimate +
        feature_store_gib_estimate``. The matrix file is mmap'd so the
        operating system can evict pages — but at the budget level it counts
        as private since it competes with other Bowaka allocations.
        """
        n = self.max_optuna_workers if n_workers is None else int(n_workers)
        worker_use = self.projected_worker_use_gib(n)
        projected = worker_use + max(0.0, float(feature_store_gib_estimate))
        budget = self.effective_bowaka_budget_gib()
        if projected > budget:
            raise MemoryReserveViolation(
                f"projected Bowaka RAM use {projected:.1f} GiB exceeds effective "
                f"budget {budget:.1f} GiB (total {self.total_ram_gib:.1f} - "
                f"reserve {self.reserve_system_gib:.1f} - emergency "
                f"{self.emergency_headroom_gib:.1f} - postgres "
                f"{self.postgres_gib_estimate:.1f}); reduce n_workers "
                f"(={n}) or matrix footprint (={feature_store_gib_estimate:.1f} GiB)"
            )

    def assert_available_reserve(self, reserve_gib: Optional[float] = None) -> None:
        """Raise :class:`MemoryReserveViolation` if ``psutil`` shows less than
        ``reserve_gib`` available right now.

        Defaults to :attr:`reserve_system_gib`.
        """
        import psutil

        threshold = float(reserve_gib) if reserve_gib is not None else float(self.reserve_system_gib)
        avail = float(psutil.virtual_memory().available) / (1024.0 ** 3)
        if avail < threshold:
            raise MemoryReserveViolation(
                f"available RAM {avail:.1f} GiB is below the reserve {threshold:.1f} GiB; "
                f"refuse to start additional work"
            )


__all__ = ["MemoryBudget", "MemoryReserveViolation"]
