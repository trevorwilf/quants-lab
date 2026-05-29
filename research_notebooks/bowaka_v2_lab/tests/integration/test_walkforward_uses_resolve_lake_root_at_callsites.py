"""Structural guard (hotfix 2026-05-29): no ``lake_root = md.get("shared_root")``.

Walks the AST of the modules that resolve the lake root and asserts that no
``lake_root`` assignment's RHS is a direct ``md.get("shared_root")`` call — the
bug class that produced ``Path('None')`` false-positive partition gates.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src" / "bowaka_v2_lab"
_MODULES = [
    _SRC / "optuna" / "walkforward_runner.py",
    _SRC / "optuna" / "holdout.py",
    _SRC / "scanner" / "scan_matrix.py",
]


def _is_md_get_shared_root(node: ast.AST) -> bool:
    """True iff the expression tree contains ``md.get("shared_root")``."""
    for sub in ast.walk(node):
        if (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr == "get"
            and isinstance(sub.func.value, ast.Name)
            and sub.func.value.id == "md"
            and sub.args
            and isinstance(sub.args[0], ast.Constant)
            and sub.args[0].value == "shared_root"
        ):
            return True
    return False


@pytest.mark.parametrize("module", _MODULES, ids=lambda p: p.name)
def test_no_lake_root_assigned_from_md_get_shared_root(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    offenders: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets_lake_root = any(
            isinstance(t, ast.Name) and t.id == "lake_root" for t in node.targets
        )
        if targets_lake_root and _is_md_get_shared_root(node.value):
            offenders.append(getattr(node, "lineno", -1))
    assert not offenders, (
        f"{module.name}: lake_root = md.get('shared_root') at lines {offenders} — "
        "use resolve_lake_root(cfg) (hotfix 2026-05-29)"
    )
