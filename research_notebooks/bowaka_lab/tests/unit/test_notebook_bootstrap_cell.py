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
    """All notebooks under notebooks/. Includes the canonical 12 numbered
    notebooks (00_..11_) plus any additional turnkey notebooks shipped
    alongside (e.g. run_backtest.ipynb)."""
    return sorted((bowaka_root / "notebooks").glob("*.ipynb"))


@pytest.fixture(scope="module")
def numbered_notebook_paths(bowaka_root: Path) -> list[Path]:
    """The 12 Phase-10 numbered notebooks only."""
    return sorted((bowaka_root / "notebooks").glob("[0-9][0-9]_*.ipynb"))


def test_twelve_numbered_notebooks_present(numbered_notebook_paths):
    """Phase 10 [Report §18] requires twelve numbered notebooks 00 → 11."""
    assert len(numbered_notebook_paths) == 12


def test_first_cell_contains_bootstrap_phrases(notebook_paths):
    """Bootstrap rule applies to every notebook under notebooks/."""
    for p in notebook_paths:
        nb = nbformat.read(p, as_version=4)
        # The first cell of a notebook may be markdown (title). The bootstrap
        # cell is required to be the first *code* cell.
        first_code = next((c for c in nb.cells if c.cell_type == "code"), None)
        assert first_code is not None, f"{p.name} has no code cells"
        src = first_code.source
        for phrase in REQUIRED_PHRASES:
            assert phrase in src, f"{p.name} bootstrap missing {phrase!r}"


def _bootstrap_source(nb) -> str:
    first_code = next((c for c in nb.cells if c.cell_type == "code"), None)
    assert first_code is not None
    return first_code.source


def test_notebook_bootstrap_imports_load_project_dotenv(notebook_paths):
    """Every notebook's bootstrap must import the canonical loader."""
    expected = "from bowaka_lab.utils.env import load_project_dotenv"
    for p in notebook_paths:
        src = _bootstrap_source(nbformat.read(p, as_version=4))
        assert expected in src, f"{p.name} bootstrap missing {expected!r}"


def test_notebook_bootstrap_calls_load_project_dotenv(notebook_paths):
    """Every notebook's bootstrap must call ``load_project_dotenv(`` at least once."""
    for p in notebook_paths:
        src = _bootstrap_source(nbformat.read(p, as_version=4))
        assert "load_project_dotenv(" in src, f"{p.name} bootstrap does not call load_project_dotenv"


def test_notebook_has_no_duplicate_dotenv_loader_cells(notebook_paths):
    """Outside the bootstrap cell, no notebook may import dotenv or call
    load_dotenv. The bootstrap is the single source of .env discovery."""
    forbidden_patterns = ("from dotenv import load_dotenv", "import dotenv", "load_dotenv(")
    for p in notebook_paths:
        nb = nbformat.read(p, as_version=4)
        # Identify the bootstrap (first code cell) and scan the rest.
        first_code_idx = next(
            (i for i, c in enumerate(nb.cells) if c.cell_type == "code"), None
        )
        for idx, cell in enumerate(nb.cells):
            if cell.cell_type != "code" or idx == first_code_idx:
                continue
            src = cell.source or ""
            for pat in forbidden_patterns:
                assert pat not in src, (
                    f"{p.name} cell[{idx}] contains forbidden dotenv reference {pat!r}; "
                    "the bootstrap cell is the only place .env should be touched"
                )
