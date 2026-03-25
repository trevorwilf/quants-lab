"""Smoke tests for the generated public screener notebooks."""

from __future__ import annotations

from pathlib import Path

import ast
import nbformat


# Navigate up from tests/unit/ to pmm_dynamic project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = _PROJECT_ROOT / "notebooks"
NOTEBOOKS = [
    NOTEBOOK_DIR / "pmm_dynamic_screener_nonkyc_public.ipynb",
    NOTEBOOK_DIR / "pmm_dynamic_screener_mexc_public.ipynb",
]



def test_public_screener_notebooks_exist_and_have_expected_structure():
    for path in NOTEBOOKS:
        assert path.exists(), f"Missing notebook: {path}"
        nb = nbformat.read(path, as_version=4)
        assert len(nb.cells) >= 14, f"Expected at least 14 cells in {path.name}, got {len(nb.cells)}"
        assert nb.cells[0].cell_type == "markdown"
        assert nb.cells[1].cell_type == "code"
        assert nb.cells[11].cell_type == "code"
        assert nb.cells[12].cell_type == "markdown"



def test_public_screener_notebook_code_cells_parse():
    for path in NOTEBOOKS:
        nb = nbformat.read(path, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == "code":
                ast.parse(cell.source)
