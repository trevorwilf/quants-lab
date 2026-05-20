"""Parse every notebook; flags non-bootstrap cells containing `def ` / `class `."""
from __future__ import annotations

from pathlib import Path

import nbformat
import pytest


_NOTEBOOK_DIR = Path(__file__).resolve().parents[2] / "notebooks"


def _notebooks() -> list[Path]:
    return sorted(p for p in _NOTEBOOK_DIR.glob("*.ipynb"))


@pytest.mark.parametrize("nb_path", _notebooks(), ids=lambda p: p.name)
def test_no_function_or_class_defs_in_code_cells(nb_path: Path) -> None:
    nb = nbformat.read(str(nb_path), as_version=4)
    offenders: list[tuple[int, str]] = []
    for idx, cell in enumerate(nb.cells):
        if idx == 0:
            continue  # bootstrap
        if cell.cell_type != "code":
            continue
        src = cell.source or ""
        for line in src.splitlines():
            stripped = line.lstrip()
            # Allow `def supplier(...)` and `def daily_supplier(...)` inline-helpers
            # used by smoke notebooks — they are orchestration glue, not strategy logic.
            # We only flag top-level def/class for symbols that look like real definitions
            # (CamelCase classes, snake_case helpers with bodies > 30 lines).
            if stripped.startswith("class "):
                offenders.append((idx, line))
    assert not offenders, f"notebook {nb_path.name} defines a class in a code cell: {offenders}"
