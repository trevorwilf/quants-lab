"""Workstation overlay configs load + carry the operator-specified knobs.

Speedup report v2 prompt header / Phase 2 task 3. The base profile pins
``memory_reserve_gib=62, strict_parallel=true, max_workers=8, n_jobs=8``;
the 10/12/16-worker overlays differ only in ``max_workers`` / ``n_jobs``.
All overlays opt into ``blas_thread_pin``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_LAB_ROOT = Path(__file__).resolve().parents[3]
_CFG_DIR = _LAB_ROOT / "configs"


def _load(name: str) -> dict:
    return yaml.safe_load((_CFG_DIR / name).read_text(encoding="utf-8"))


def test_workstation_base_profile_loads_and_sets_workstation_fields() -> None:
    doc = _load("bowaka_v2_actual_iex_current_code_optuna.workstation.yml")
    parallel = doc["optuna"]["parallel"]
    assert parallel["memory_reserve_gib"] == 62
    assert parallel["strict_parallel"] is True
    assert parallel["max_workers"] == 8
    assert parallel["blas_thread_pin"] is True
    assert doc["optuna"]["n_jobs"] == 8


@pytest.mark.parametrize("n", [10, 12, 16])
def test_workstation_Nw_overlay_loads_with_matching_njobs_max_workers(n: int) -> None:
    doc = _load(f"bowaka_v2_actual_iex_current_code_optuna.workstation_{n}w.yml")
    parallel = doc["optuna"]["parallel"]
    assert parallel["max_workers"] == n
    assert doc["optuna"]["n_jobs"] == n
    assert parallel["memory_reserve_gib"] == 62
    assert parallel["strict_parallel"] is True
    assert parallel["blas_thread_pin"] is True
