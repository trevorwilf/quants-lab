"""Verify every import statement in the four notebooks resolves.

Extracts `import X` and `from X import Y` from all code cells and calls
importlib.import_module on each module path. Any failure is reported
per-notebook.
"""

import ast
import importlib
import json
from pathlib import Path

import pytest


NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "direction-custom"

NOTEBOOKS = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]


def _collect_imports(nb_path: Path) -> list[str]:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    concat_src = "\n\n".join(
        ("".join(c.get("source", [])) if isinstance(c.get("source"), list) else c.get("source", ""))
        for c in nb["cells"] if c["cell_type"] == "code"
    )
    tree = ast.parse(concat_src)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                modules.append(node.module)
    return modules


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_all_imports_resolve(name):
    modules = _collect_imports(NB_DIR / name)
    assert modules, f"{name}: no imports found — suspicious"
    failures = []
    for m in modules:
        try:
            importlib.import_module(m)
        except Exception as e:
            # Allow `datetime` imports, stdlib patterns, etc. to succeed.
            failures.append((m, type(e).__name__, str(e)))
    assert not failures, f"{name}: unresolvable imports: {failures}"
