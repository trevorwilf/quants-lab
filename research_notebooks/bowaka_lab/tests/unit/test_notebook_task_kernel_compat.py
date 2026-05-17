"""Phase 10: NotebookTask must accept both `kernel` and `kernel_name` keys."""

from __future__ import annotations

import re
from pathlib import Path


def test_patched_kernel_resolution(repo_root: Path):
    target = repo_root / "app" / "tasks" / "notebook" / "notebook_task.py"
    if not target.exists():
        # In standalone runs the host repo may not be present. Skip silently.
        import pytest

        pytest.skip("NotebookTask file not present in this checkout")
    text = target.read_text(encoding="utf-8")
    # Must read both keys with `kernel` taking precedence.
    assert re.search(
        r"self\.kernel_name\s*=\s*task_config\.get\(\"kernel\",\s*task_config\.get\(\"kernel_name\",",
        text,
    ), "NotebookTask is not patched to accept both `kernel` and `kernel_name` keys"
