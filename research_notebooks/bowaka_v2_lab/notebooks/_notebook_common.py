"""Shared notebook bootstrap cell template + helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat


BOOTSTRAP_CELL_SOURCE = """\
# bowaka_v2_lab notebook bootstrap cell — DO NOT EDIT BY HAND.
# Adds the lab's src/ to sys.path so `import bowaka_v2_lab` works regardless of
# how the notebook is launched (jupyter / papermill / pytest).
import os
import sys
from pathlib import Path

_here = Path.cwd()
for _candidate in [_here, *_here.parents]:
    if (_candidate / "src" / "bowaka_v2_lab" / "__init__.py").is_file():
        sys.path.insert(0, str(_candidate / "src"))
        break
import bowaka_v2_lab  # noqa: F401
print("bowaka_v2_lab", bowaka_v2_lab.__version__)
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
