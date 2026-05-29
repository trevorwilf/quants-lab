"""Hotfix 2026-05-29 — the WSL skip tracks real bash capability, not registration.

``_wsl_available()`` must return True iff ``bash -c 'echo ok'`` actually returns
'ok' (a registered-but-broken WSL distro fails at execvpe time).
"""
from __future__ import annotations

import shutil
import subprocess

from tests.integration.test_full_test_matrix_dry_run import _wsl_available


def test_wsl_available_matches_real_bash_execution() -> None:
    if shutil.which("bash") is None:
        assert _wsl_available() is False
        return
    try:
        r = subprocess.run(
            ["bash", "-c", "echo ok"], capture_output=True, text=True, timeout=10,
        )
        real = r.returncode == 0 and r.stdout.strip() == "ok"
    except Exception:
        real = False
    assert _wsl_available() is real
