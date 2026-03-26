"""Verify every code cell in pmm_dynamic_*.ipynb notebooks compiles without SyntaxError."""

from __future__ import annotations

import ast
from pathlib import Path

import nbformat
import pytest

# Navigate up from tests/unit/ to pmm_dynamic project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = _PROJECT_ROOT / "notebooks" / "pmm_dynamic"

# Collect all pmm_dynamic_*.ipynb notebooks
_NOTEBOOKS = sorted(NOTEBOOK_DIR.glob("pmm_dynamic_*.ipynb"))


@pytest.mark.parametrize(
    "notebook_path",
    _NOTEBOOKS,
    ids=[p.name for p in _NOTEBOOKS],
)
def test_notebook_code_cells_compile(notebook_path: Path) -> None:
    """Each code cell in the notebook must be valid Python (no SyntaxError)."""
    nb = nbformat.read(notebook_path, as_version=4)
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        try:
            ast.parse(cell.source)
        except SyntaxError as exc:
            pytest.fail(
                f"{notebook_path.name} cell {idx}: SyntaxError: {exc}"
            )
