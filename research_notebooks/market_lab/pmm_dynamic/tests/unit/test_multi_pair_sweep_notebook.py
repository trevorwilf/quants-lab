"""Tests for the multi-pair sweep notebook structure and wiring.

Validates that the notebook cells contain the expected configuration,
imports, and logic after the refactoring changes.
"""

import nbformat
import pytest
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "pmm_dynamic_multi_pair_sweep.ipynb"
)


@pytest.fixture(scope="module")
def notebook():
    """Load the sweep notebook once for all tests."""
    assert NOTEBOOK_PATH.exists(), f"Notebook not found: {NOTEBOOK_PATH}"
    return nbformat.read(str(NOTEBOOK_PATH), as_version=4)


@pytest.fixture(scope="module")
def code_cells(notebook):
    """Return only code cells, in order."""
    return [c for c in notebook.cells if c.cell_type == "code"]


class TestNotebookStructure:
    """Verify overall notebook structure."""

    def test_total_cell_count(self, notebook):
        assert len(notebook.cells) == 14

    def test_code_cell_count(self, code_cells):
        assert len(code_cells) == 7

    def test_markdown_cell_count(self, notebook):
        md = [c for c in notebook.cells if c.cell_type == "markdown"]
        assert len(md) == 7

    def test_cell_order(self, notebook):
        expected = [
            "markdown",  # 0: title
            "code",      # 1: setup
            "markdown",  # 2: config header
            "code",      # 3: configuration
            "code",      # 4: preflight (NEW)
            "markdown",  # 5: discover header
            "code",      # 6: discover
            "markdown",  # 7: sweep header
            "code",      # 8: main sweep
            "markdown",  # 9: results header
            "code",      # 10: summary
            "markdown",  # 11: profitable header
            "code",      # 12: profitable detail
            "markdown",  # 13: next steps
        ]
        actual = [c.cell_type for c in notebook.cells]
        assert actual == expected


class TestControllerCompatWiring:
    """Verify controller_compat flags are defined and threaded correctly."""

    def test_search_compat_defined(self, notebook):
        cell3 = notebook.cells[3].source
        assert "SEARCH_CONTROLLER_COMPAT = False" in cell3

    def test_stress_compat_removed(self, notebook):
        """STRESS_CONTROLLER_COMPAT was removed — stress uses same mode as search."""
        cell3 = notebook.cells[3].source
        assert "STRESS_CONTROLLER_COMPAT" not in cell3

    def test_search_compat_printed(self, notebook):
        cell3 = notebook.cells[3].source
        assert "controller_compat={SEARCH_CONTROLLER_COMPAT}" in cell3

    def test_create_objective_uses_search_compat(self, notebook):
        cell8 = notebook.cells[8].source
        assert "controller_compat=SEARCH_CONTROLLER_COMPAT" in cell8

    def test_dataset_summary_includes_search_compat(self, notebook):
        cell8 = notebook.cells[8].source
        assert '"search_controller_compat": SEARCH_CONTROLLER_COMPAT' in cell8


class TestPreflightIntegration:
    """Verify preflight checks are wired in."""

    def test_setup_imports_preflight(self, notebook):
        cell1 = notebook.cells[1].source
        assert "from pmm_lab.optuna.preflight import print_environment, run_preflight" in cell1

    def test_setup_calls_print_environment(self, notebook):
        cell1 = notebook.cells[1].source
        assert "print_environment()" in cell1

    def test_preflight_cell_exists(self, notebook):
        cell4 = notebook.cells[4].source
        assert "run_preflight" in cell4

    def test_preflight_forces_n_jobs_for_sqlite(self, notebook):
        cell4 = notebook.cells[4].source
        assert "N_JOBS = 1" in cell4
        assert "SQLite safety" in cell4

    def test_preflight_uses_get_storage_url(self, notebook):
        cell4 = notebook.cells[4].source
        assert "from pmm_lab.optuna.storage import get_storage_url" in cell4


class TestZeroTrialGuard:
    """Verify zero-trial handling in the sweep loop."""

    def test_no_completed_trials_status(self, notebook):
        cell8 = notebook.cells[8].source
        assert '"no_completed_trials"' in cell8

    def test_ranked_replaces_best_trial_check(self, notebook):
        cell8 = notebook.cells[8].source
        assert "if not ranked:" in cell8

    def test_no_study_best_value_access(self, notebook):
        """study.best_value raises if no trials complete; we should not call it."""
        cell8 = notebook.cells[8].source
        assert "study.best_value" not in cell8


class TestStalePairFiltering:
    """Verify stale-pair gate in discovery."""

    def test_max_stale_days_defined(self, notebook):
        cell3 = notebook.cells[3].source
        assert "MAX_STALE_DAYS = 7" in cell3

    def test_stale_exclusions_populated(self, notebook):
        cell6 = notebook.cells[6].source
        assert "stale_exclusions" in cell6
        assert "last_age_days" in cell6

    def test_insufficient_exclusions_populated(self, notebook):
        cell6 = notebook.cells[6].source
        assert "insufficient_exclusions" in cell6

    def test_stale_exclusions_printed(self, notebook):
        cell6 = notebook.cells[6].source
        assert "stale pair(s)" in cell6

    def test_summary_shows_exclusion_stats(self, notebook):
        cell10 = notebook.cells[10].source
        assert "stale_exclusions" in cell10
        assert "insufficient_exclusions" in cell10


class TestStressSkipGate:
    """Verify phase-1 score gate before stress testing."""

    def test_min_phase1_defined(self, notebook):
        cell3 = notebook.cells[3].source
        assert "MIN_PHASE1_BEST_FOR_STRESS = 0.0" in cell3

    def test_phase1_gate_in_sweep(self, notebook):
        cell8 = notebook.cells[8].source
        assert "MIN_PHASE1_BEST_FOR_STRESS" in cell8
        assert '"phase1_below_threshold"' in cell8

    def test_no_duplicate_completed_ranking(self, notebook):
        """completed/ranked should only be computed once (in phase 1)."""
        cell8 = notebook.cells[8].source
        lines = cell8.split("\n")
        count = sum(
            1 for line in lines
            if "completed = [t for t in study.trials" in line
        )
        assert count == 1, f"Expected 1 completed= line, found {count}"


class TestAmountReporting:
    """Verify amount-related info is reported."""

    def test_dataset_summary_has_amount_range(self, notebook):
        cell8 = notebook.cells[8].source
        assert '"total_amount_quote_search_min": 25.0' in cell8
        assert '"total_amount_quote_search_max": 1000.0' in cell8

    def test_dataset_summary_has_ideal_amount(self, notebook):
        cell8 = notebook.cells[8].source
        assert "total_amount_quote_ideal" in cell8

    def test_profitable_detail_shows_amount(self, notebook):
        cell12 = notebook.cells[12].source
        assert "Amount (quote)" in cell12
        assert "search range: 25.00" in cell12


class TestNoInvalidKwargs:
    """Verify removed/invalid kwargs are gone."""

    def test_no_dataset_hash_in_stop_ship(self, notebook):
        cell8 = notebook.cells[8].source
        # Find the run_stop_ship_checks call and verify no dataset_hash
        idx = cell8.index("run_stop_ship_checks(")
        closing = cell8.index(")", idx)
        call_text = cell8[idx:closing]
        assert "dataset_hash" not in call_text
