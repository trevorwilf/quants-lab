"""Shared bootstrap-cell source for bowaka_lab research notebooks.

Every notebook builder imports ``BOOTSTRAP`` from here so the bootstrap cell
matches across all 12 numbered notebooks plus ``run_backtest.ipynb``. The
exact text is also enforced by ``tests/unit/test_notebook_bootstrap_cell.py``.
"""

from __future__ import annotations

import nbformat


BOOTSTRAP = '''# Notebook bootstrap cell. Keep this in every bowaka_lab notebook.
from pathlib import Path
import sys

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "research_notebooks").exists():
    repo_root = repo_root.parent

bowaka_project = repo_root / "research_notebooks" / "bowaka_lab"
src_path = bowaka_project / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import bowaka_lab
from bowaka_lab.utils.env import load_project_dotenv

_loaded_env = load_project_dotenv()
print(f"bowaka_lab {bowaka_lab.__version__}")
print(
    f"bowaka_lab bootstrap: .env loaded from {_loaded_env}"
    if _loaded_env
    else "bowaka_lab bootstrap: no .env found (env vars must be set in shell)"
)
'''


DEFAULT_KERNEL = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}

DEFAULT_LANGUAGE_INFO = {"name": "python", "version": "3.12"}


def code_cell(source: str, tag: str | None = None) -> nbformat.NotebookNode:
    cell = nbformat.v4.new_code_cell(source)
    if tag is not None:
        cell.metadata["tags"] = [tag]
    return cell


def md_cell(source: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_markdown_cell(source)


def finalize(nb: nbformat.NotebookNode) -> nbformat.NotebookNode:
    nb.metadata["kernelspec"] = DEFAULT_KERNEL
    nb.metadata["language_info"] = DEFAULT_LANGUAGE_INFO
    return nb
