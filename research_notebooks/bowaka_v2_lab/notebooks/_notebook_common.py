"""Shared notebook bootstrap cell template + helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat


BOOTSTRAP_CELL_SOURCE = """\
# bowaka_v2_lab notebook bootstrap cell — DO NOT EDIT BY HAND.
# Adds the lab's src/ (and its bowaka_common dependency) to sys.path and pins
# the working directory to the repo root, so `import bowaka_v2_lab` and
# repo-root-relative CONFIG_PATH parameters resolve identically under jupyter,
# papermill, and the QuantsLab scheduler.
import os
import sys
from pathlib import Path

_lab_root = None
for _candidate in [Path.cwd(), *Path.cwd().parents]:
    if (_candidate / "src" / "bowaka_v2_lab" / "__init__.py").is_file():
        _lab_root = _candidate
        break
if _lab_root is None:
    raise RuntimeError(
        f"bowaka_v2_lab bootstrap: src/bowaka_v2_lab/ not found at or above {Path.cwd()}"
    )

# Pin CWD to the repo root (the directory holding research_notebooks/ and the
# Makefile) so repo-root-relative CONFIG_PATH values resolve regardless of how
# the notebook was launched (jupyter CWD = notebook dir, scheduler = repo root).
_repo_root = _lab_root
for _candidate in [_lab_root, *_lab_root.parents]:
    if (_candidate / "research_notebooks").is_dir() and (_candidate / "Makefile").is_file():
        _repo_root = _candidate
        break
os.chdir(_repo_root)

# Make the lab and its bowaka_common dependency importable from the working
# tree, even when the packages are not pip-installed. v1 bowaka_lab is
# deliberately excluded — v2 must not import v1.
for _src in (_lab_root / "src",
             _repo_root / "research_notebooks" / "bowaka_common" / "src"):
    if _src.is_dir() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import bowaka_v2_lab  # noqa: F401
print(f"bowaka_v2_lab {bowaka_v2_lab.__version__} (cwd={_repo_root})")
"""


def make_notebook(cells: list[dict]) -> nbformat.NotebookNode:
    """Build a notebook with the bootstrap cell as cell 0 and ``cells`` after."""
    nb = nbformat.v4.new_notebook()
    nb_cells = [nbformat.v4.new_code_cell(source=BOOTSTRAP_CELL_SOURCE)]
    for c in cells:
        if c["type"] == "markdown":
            nb_cells.append(nbformat.v4.new_markdown_cell(source=c["source"]))
        elif c["type"] == "code":
            nb_cells.append(nbformat.v4.new_code_cell(source=c["source"]))
    nb["cells"] = nb_cells
    nb["metadata"] = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
        "papermill": {
            "parameters": {"CONFIG_PATH": "research_notebooks/bowaka_v2_lab/configs/bowaka_v2_backtest_smoke.yml"},
        },
    }
    return nb


def write_notebook(nb: nbformat.NotebookNode, out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        nbformat.write(nb, fh)
