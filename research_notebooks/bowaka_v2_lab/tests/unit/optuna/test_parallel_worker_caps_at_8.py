"""``run_bowaka_optimization_dispatch`` caps n_jobs at MemoryBudget cap.

Speedup report §6.1 / §11.3 Phase 5. Even if the operator requests
``n_jobs=18``, the dispatcher caps the effective worker count at
``memory_budget.max_optuna_workers`` (default 8).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bowaka_v2_lab.optuna.dispatcher import run_bowaka_optimization_dispatch
from bowaka_v2_lab.utils.memory_guard import MemoryBudget


def _stub_study():
    return MagicMock(name="optuna.Study")


def test_n_jobs_capped_at_memory_budget_max():
    captured: dict = {}

    def fake_parallel(*, study_name, storage_url, n_total_trials, n_workers,
                      objective_factory_dotted, factory_kwargs,
                      sampler_seed, n_startup_trials, memory_budget):
        captured["n_workers"] = n_workers
        captured["n_total_trials"] = n_total_trials
        # Return a single successful worker so the dispatcher path completes.
        return [SimpleNamespace(
            worker_id=0, n_completed=n_total_trials, n_pruned=0,
            n_failed=0, error=None,
        )]

    budget = MemoryBudget(total_ram_gib=192.0, max_optuna_workers=8)
    fake_optuna = MagicMock()
    fake_optuna.load_study = MagicMock(return_value=_stub_study())
    with patch(
        "bowaka_v2_lab.optuna.dispatcher.run_parallel_bowaka_optimization",
        side_effect=fake_parallel,
    ), patch("bowaka_v2_lab.optuna.dispatcher.optuna", fake_optuna):
        run_bowaka_optimization_dispatch(
            study=_stub_study(), study_name="x",
            objective=lambda t: 0.0,
            objective_factory_dotted="some:thing",
            factory_kwargs={},
            n_trials=160, n_jobs=18,
            storage_url="postgresql+psycopg2://u:p@h:5432/d",
            memory_budget=budget,
        )
    assert captured["n_workers"] == 8, f"expected cap to 8, got {captured['n_workers']}"


def test_n_jobs_under_cap_passes_through():
    captured: dict = {}

    def fake_parallel(*, n_workers, **kwargs):
        captured["n_workers"] = n_workers
        return [SimpleNamespace(
            worker_id=0, n_completed=kwargs["n_total_trials"], n_pruned=0,
            n_failed=0, error=None,
        )]

    fake_optuna = MagicMock()
    fake_optuna.load_study = MagicMock(return_value=_stub_study())
    with patch(
        "bowaka_v2_lab.optuna.dispatcher.run_parallel_bowaka_optimization",
        side_effect=fake_parallel,
    ), patch("bowaka_v2_lab.optuna.dispatcher.optuna", fake_optuna):
        run_bowaka_optimization_dispatch(
            study=_stub_study(), study_name="x",
            objective=lambda t: 0.0,
            objective_factory_dotted="some:thing",
            factory_kwargs={},
            n_trials=12, n_jobs=4,
            storage_url="postgresql+psycopg2://u:p@h:5432/d",
            memory_budget=MemoryBudget(total_ram_gib=192.0, max_optuna_workers=8),
        )
    assert captured["n_workers"] == 4
