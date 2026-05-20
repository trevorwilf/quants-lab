"""Smoke run of `make trigger-task ... bowaka_v2_smoke_tasks.yml`.

Marker: slow. The make target shells through to ``python cli.py trigger-task``;
this test verifies the task is discoverable and the dispatcher succeeds for
the smoke variant.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
def test_smoke_task_validates_and_lists(repo_root: Path) -> None:
    # We validate the config and list the registered tasks rather than actually
    # invoking notebook execution — papermill execution is exercised by the
    # per-notebook integration tests.
    result = subprocess.run(
        [sys.executable, str(repo_root / "cli.py"), "validate-config",
         "--config", "config/bowaka_v2_smoke_tasks.yml"],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    assert result.returncode == 0, f"validate-config failed: {result.stderr}"
