"""Phase 10: notebooks must be orchestration-only — no def/class outside bootstrap."""

from __future__ import annotations

import ast
from pathlib import Path

import nbformat
import pytest


@pytest.fixture(scope="module")
def notebook_paths(bowaka_root: Path) -> list[Path]:
    return sorted((bowaka_root / "notebooks").glob("*.ipynb"))


def _has_def_or_class(src: str) -> list[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def test_no_function_or_class_definitions_outside_bootstrap(notebook_paths):
    offenders: list[tuple[str, int, list[str]]] = []
    for p in notebook_paths:
        nb = nbformat.read(p, as_version=4)
        for idx, cell in enumerate(nb.cells):
            if idx == 0:
                continue  # bootstrap cell is allowed to be code
            if cell.cell_type != "code":
                continue
            names = _has_def_or_class(cell.source)
            if names:
                offenders.append((p.name, idx, names))
    if offenders:
        msg = "\n".join(f"{n} cell {idx}: {names}" for n, idx, names in offenders)
        pytest.fail("Logic belongs in src/, not notebook cells:\n" + msg)
