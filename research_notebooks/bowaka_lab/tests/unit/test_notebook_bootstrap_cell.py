"""Phase 10: every notebook starts with the §6.4 bootstrap cell."""

from __future__ import annotations

from pathlib import Path

import nbformat
import pytest


REQUIRED_PHRASES = (
    "Notebook bootstrap cell",
    "research_notebooks",
    "bowaka_lab",
    'src_path = bowaka_project / "src"',
    "sys.path.insert(0, str(src_path))",
)


@pytest.fixture(scope="module")
def notebook_paths(bowaka_root: Path) -> list[Path]:
    return sorted((bowaka_root / "notebooks").glob("*.ipynb"))


def test_twelve_notebooks_present(notebook_paths):
    assert len(notebook_paths) == 12


def test_first_cell_contains_bootstrap_phrases(notebook_paths):
    for p in notebook_paths:
        nb = nbformat.read(p, as_version=4)
        assert nb.cells, f"{p.name} is empty"
        first = nb.cells[0]
        assert first.cell_type == "code", f"{p.name} first cell must be code"
        src = first.source
        for phrase in REQUIRED_PHRASES:
            assert phrase in src, f"{p.name} bootstrap missing {phrase!r}"
