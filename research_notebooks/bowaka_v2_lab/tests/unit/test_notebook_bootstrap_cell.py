"""Every notebook's first cell matches the bootstrap template."""
from __future__ import annotations

from pathlib import Path

import nbformat
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "notebooks"))
from _notebook_common import BOOTSTRAP_CELL_SOURCE  # noqa: E402


_NOTEBOOK_DIR = Path(__file__).resolve().parents[2] / "notebooks"


def _notebooks() -> list[Path]:
    return sorted(p for p in _NOTEBOOK_DIR.glob("*.ipynb"))


@pytest.mark.parametrize("nb_path", _notebooks(), ids=lambda p: p.name)
def test_first_cell_is_bootstrap(nb_path: Path) -> None:
    nb = nbformat.read(str(nb_path), as_version=4)
    assert nb.cells, f"empty notebook: {nb_path}"
    first = nb.cells[0]
    assert first.cell_type == "code"
    assert first.source.strip() == BOOTSTRAP_CELL_SOURCE.strip()
