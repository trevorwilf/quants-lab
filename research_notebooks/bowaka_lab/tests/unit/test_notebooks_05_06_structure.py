"""Structure tests for the counterfactual notebooks (05, 06)."""

from __future__ import annotations

import re
from pathlib import Path

import nbformat
import pytest


def _read(p: Path):
    return nbformat.read(p, as_version=4)


def _src(nb) -> str:
    return "\n".join(c.source or "" for c in nb.cells if c.cell_type == "code")


def _param_cell_src(nb) -> str:
    for c in nb.cells:
        if c.cell_type == "code" and "parameters" in (c.get("metadata", {}).get("tags") or []):
            return c.source or ""
    return ""


# ---------------------------------------------------------------------------
# Notebook 05
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_05(bowaka_root):
    p = bowaka_root / "notebooks" / "05_entry_timing_counterfactuals.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_05_has_parameters_cell_with_ENTRY_RULES_list(nb_05):
    """After Phase fidelity-1, the override knob is named OVERRIDE_ENTRY_RULES;
    the underlying CounterfactualConfig defaults come from CONFIG_PATH."""
    src = _param_cell_src(nb_05)
    assert re.search(r"\bOVERRIDE_ENTRY_RULES\b\s*=", src), "05 parameters missing OVERRIDE_ENTRY_RULES"
    # Must include the canonical 5 rules.
    for rule in ("fixed_time_0935", "fixed_time_0945", "fixed_time_1000",
                 "opening_range_break", "vwap_reclaim"):
        assert rule in src, f"05 OVERRIDE_ENTRY_RULES missing {rule!r}"
    assert re.search(r'CONFIG_PATH\s*=\s*[\'"][^\'"]+\.yml[\'"]', src)


def test_notebook_05_imports_build_variant_grid_and_run_grid_for_candidates(nb_05):
    src = _src(nb_05)
    # Either the grid builder is invoked directly, or run_grid_for_candidates
    # (which calls build_variant_grid internally) is used. The notebook uses
    # the latter pattern.
    assert "run_grid_for_candidates" in src
    # CounterfactualConfig is the type that holds the grid axes.
    assert "CounterfactualConfig" in src


def test_notebook_05_saves_cf_entry_artifact(nb_05):
    assert "paths.cf_entry" in _src(nb_05)


def test_notebook_05_loads_candidates_from_notebook_03(nb_05):
    src = _src(nb_05)
    assert "paths.candidates" in src
    assert "load_parquet" in src


# ---------------------------------------------------------------------------
# Notebook 06
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nb_06(bowaka_root):
    p = bowaka_root / "notebooks" / "06_exit_surface_and_stop_manager.ipynb"
    assert p.exists()
    return _read(p)


def test_notebook_06_has_parameters_cell_with_stop_target_hold_lists(nb_06):
    """After Phase fidelity-1, knobs are renamed OVERRIDE_* and the base
    config comes from CONFIG_PATH."""
    src = _param_cell_src(nb_06)
    for name in ("OVERRIDE_STOP_PCTS", "OVERRIDE_TARGET_PCTS",
                 "OVERRIDE_MAX_HOLD_DAYS", "OVERRIDE_STOP_MGRS"):
        assert re.search(rf"\b{name}\b\s*=", src), f"06 parameters missing {name}"
    assert re.search(r'CONFIG_PATH\s*=\s*[\'"][^\'"]+\.yml[\'"]', src)


def test_notebook_06_imports_build_variant_grid_and_run_grid_for_candidates(nb_06):
    src = _src(nb_06)
    assert "run_grid_for_candidates" in src
    assert "CounterfactualConfig" in src


def test_notebook_06_saves_cf_exit_artifact(nb_06):
    assert "paths.cf_exit" in _src(nb_06)


def test_notebook_06_includes_gap_through_diagnostic_section(nb_06):
    """Addresses the high stop_gap rate from the IEX baseline run."""
    src = _src(nb_06)
    assert "stop_gap" in src


def test_notebook_06_includes_stop_manager_section(nb_06):
    """The notebook must reference the stop_manager_model variants."""
    src = _src(nb_06)
    assert "stop_manager_model" in src or "STOP_MANAGER_MODELS" in src


def test_notebook_06_uses_REBUILD_fast_path(nb_06):
    src = _src(nb_06)
    assert "REBUILD" in src
    assert "artifact_exists" in src
