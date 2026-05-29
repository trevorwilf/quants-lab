"""Workstation overlay configs load + carry the operator-specified knobs.

Speedup report v2 prompt header / Phase 2 task 3. The base profile pins
``memory_reserve_gib=62, strict_parallel=true``; ``blas_thread_pin`` is on.

2026-05-28: the base profile's worker count is 10 (operator decision). A
16-worker flip was attempted and reverted — 16*6=96 GiB exceeds the
ql-jupyter CONTAINER budget (157 GiB WSL2 cap -> 71.2 GiB effective), which
strict_parallel correctly hard-failed. 10 (60 GiB) fits with ~11 GiB spare.
The base now pins ``max_workers=10, n_jobs=10`` (matching the 10w overlay).
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
    # 2026-05-28: base worker count is 10 (see module docstring — 16 was
    # reverted as it exceeds the container memory budget).
    assert parallel["max_workers"] == 10
    assert parallel["blas_thread_pin"] is True
    assert doc["optuna"]["n_jobs"] == 10


@pytest.mark.parametrize("n", [10, 12, 16])
def test_workstation_Nw_overlay_loads_with_matching_njobs_max_workers(n: int) -> None:
    doc = _load(f"bowaka_v2_actual_iex_current_code_optuna.workstation_{n}w.yml")
    parallel = doc["optuna"]["parallel"]
    assert parallel["max_workers"] == n
    assert doc["optuna"]["n_jobs"] == n
    assert parallel["memory_reserve_gib"] == 62
    assert parallel["strict_parallel"] is True
    assert parallel["blas_thread_pin"] is True
