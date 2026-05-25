"""Notebook 10's built ipynb carries the Phase 10 incumbent default.

Speedup report §9 / Phase 10 Task 1. ``INCUMBENT_TRIAL = True`` is the
default; ``run_walkforward_study(..., incumbent_trial=INCUMBENT_TRIAL)``
is wired into the optimize call.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _read_built_notebook(lab_root: Path) -> dict:
    nb_path = lab_root / "notebooks" / "10_optuna_walkforward.ipynb"
    if not nb_path.is_file():
        pytest.skip("notebook 10 not built")
    return json.loads(nb_path.read_text(encoding="utf-8"))


def _cell_sources(nb: dict) -> list[str]:
    out: list[str] = []
    for cell in nb.get("cells", []):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        out.append(source)
    return out


def test_notebook_10_papermill_params_carry_incumbent_default(lab_root: Path):
    nb = _read_built_notebook(lab_root)
    sources = _cell_sources(nb)
    # First code cell sets papermill parameters; assert INCUMBENT_TRIAL is True.
    param_cell = next((s for s in sources if "CONFIG_PATH" in s and "INCUMBENT_TRIAL" in s), None)
    assert param_cell is not None, "INCUMBENT_TRIAL is not declared in the parameters cell"
    assert "INCUMBENT_TRIAL = True" in param_cell


def test_notebook_10_run_call_passes_incumbent(lab_root: Path):
    nb = _read_built_notebook(lab_root)
    sources = _cell_sources(nb)
    run_cell = next((s for s in sources if "run_walkforward_study" in s), None)
    assert run_cell is not None
    assert "incumbent_trial=INCUMBENT_TRIAL" in run_cell


def test_notebook_10_run_call_passes_n_jobs(lab_root: Path):
    """Phase 5 parameter surface — N_JOBS papermill var threaded into run."""
    nb = _read_built_notebook(lab_root)
    sources = _cell_sources(nb)
    run_cell = next((s for s in sources if "run_walkforward_study" in s), None)
    assert run_cell is not None
    assert "n_jobs=N_JOBS" in run_cell
