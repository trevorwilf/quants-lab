"""Tests that the retest and multi-exchange notebooks are wired for multi-window recent evaluation."""
import json
import ast
import pytest
from pathlib import Path

NOTEBOOK_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "pmm_dynamic"

NOTEBOOKS = [
    "pmm_dynamic_retest_sweep.ipynb",
    "pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
]


def _get_cell_sources(notebook_path):
    """Load notebook and return list of (cell_index, source_string) for code cells."""
    with open(notebook_path, encoding="utf-8") as f:
        nb = json.load(f)
    return [
        (i, "".join(c["source"]))
        for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code"
    ]


@pytest.fixture(params=NOTEBOOKS)
def notebook_cells(request):
    path = NOTEBOOK_DIR / request.param
    if not path.exists():
        pytest.skip(f"Notebook not found: {path}")
    return _get_cell_sources(path)


def _find_cell_containing(cells, text):
    for idx, src in cells:
        if text in src:
            return idx, src
    return None, None


class TestRecentInfoWindowsNotebookWiring:

    def test_config_cell_defines_blocking_window(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "RECENT_BLOCKING_WINDOW_DAYS")
        assert src is not None, "Config cell must define RECENT_BLOCKING_WINDOW_DAYS"
        assert "= 28" in src

    def test_config_cell_defines_informational_windows(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "RECENT_INFORMATIONAL_WINDOW_DAYS")
        assert src is not None, "Config cell must define RECENT_INFORMATIONAL_WINDOW_DAYS"
        assert "14" in src
        assert "7" in src

    def test_sweep_cell_creates_results_mapping(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "recent_window_results")
        assert src is not None, "Sweep cell must create recent_window_results mapping"
        assert "recent_window_results" in src

    def test_sweep_cell_preserves_28d_alias(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "recent_window_result =")
        assert src is not None, "Sweep cell must preserve recent_window_result alias"
        # Verify it's derived from the mapping
        assert "recent_window_results" in src

    def test_sweep_cell_stop_ship_uses_only_28d(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "run_stop_ship_checks")
        assert src is not None
        # Must pass recent_window_result (the 28d alias)
        assert "recent_window_result=recent_window_result" in src
        # Must NOT pass recent_window_results to stop-ship
        # (recent_window_results should go to generate_report, not run_stop_ship_checks)
        lines = src.split("\n")
        in_stop_ship = False
        for line in lines:
            if "run_stop_ship_checks(" in line:
                in_stop_ship = True
            if in_stop_ship:
                assert "recent_window_results=" not in line or "generate_report" in line, \
                    "recent_window_results must not be passed to run_stop_ship_checks"
                if ")" in line and "run_stop_ship_checks" not in line:
                    in_stop_ship = False

    def test_report_call_passes_multi_window(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "generate_report(")
        assert src is not None
        assert "recent_window_results=" in src, "generate_report must receive recent_window_results"

    def test_sweep_cell_uses_blocking_constant_for_split(self, notebook_cells):
        _, src = _find_cell_containing(notebook_cells, "split_for_release_gate")
        assert src is not None
        assert "RECENT_BLOCKING_WINDOW_DAYS" in src, "split_for_release_gate must use the blocking constant"
        assert "recent_days=28" not in src, "Must not hard-code recent_days=28 in split_for_release_gate"

    def test_all_code_cells_compile(self, notebook_cells):
        for idx, src in notebook_cells:
            try:
                ast.parse(src)
            except SyntaxError as e:
                pytest.fail(f"Cell {idx} has syntax error: {e}")
