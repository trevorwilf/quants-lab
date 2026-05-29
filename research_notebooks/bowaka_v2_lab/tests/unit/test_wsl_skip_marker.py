"""Phase 0 (phases 4-7) — the WSL-only matrix test is skip-guarded.

``tests/integration/test_full_test_matrix_dry_run.py`` invokes a bash script;
on Windows-without-WSL it must skip cleanly rather than fail. Assert the module
carries a ``skipif`` pytestmark keyed on bash/WSL availability.
"""
from __future__ import annotations

import importlib


def test_matrix_dry_run_module_has_skipif_marker() -> None:
    mod = importlib.import_module(
        "tests.integration.test_full_test_matrix_dry_run"
    )
    assert hasattr(mod, "pytestmark")
    marks = mod.pytestmark if isinstance(mod.pytestmark, list) else [mod.pytestmark]
    names = {m.name for m in marks}
    assert "skipif" in names
    skipif = next(m for m in marks if m.name == "skipif")
    reason = str(skipif.kwargs.get("reason", "")).lower()
    assert "bash" in reason or "wsl" in reason


def test_wsl_available_is_callable() -> None:
    mod = importlib.import_module(
        "tests.integration.test_full_test_matrix_dry_run"
    )
    # the predicate must be importable and return a bool on this host
    assert isinstance(mod._wsl_available(), bool)
