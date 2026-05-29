"""``scripts/run_full_test_matrix.sh --dry-run`` prints the plan and exits 0.

Realism remediation 2 Phase 2 (audit §P1-007): the CI test-matrix driver must be
exercisable without running the whole (slow) suite. ``--dry-run`` is hermetic — it
imports nothing and invokes no pytest — so it is safe to call from a test.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

import pytest

_LAB_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _LAB_ROOT / "scripts" / "run_full_test_matrix.sh"


def _wsl_available() -> bool:
    """True iff a working ``bash`` is reachable from this host.

    The matrix test invokes ``scripts/run_full_test_matrix.sh`` through
    ``bash.EXE``. On Windows hosts without a registered WSL distro,
    ``shutil.which("bash")`` still resolves the WSL launcher stub, which then
    fails with ``execvpe(/bin/bash) ... No such file or directory`` and exits
    1. Detect a *real* bash so the test skips cleanly in that case — the
    underlying matrix has its own coverage via the integration suite directly.
    """
    if platform.system() != "Windows":
        return shutil.which("bash") is not None
    try:
        r = subprocess.run(
            ["wsl", "-l", "-q"], capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0 and bool(r.stdout.strip())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _wsl_available(),
    reason="needs a working bash (WSL on Windows); the matrix runner has "
           "integration coverage elsewhere — this is the script-shape smoke test.",
)


def test_run_full_test_matrix_script_exists() -> None:
    assert _SCRIPT.is_file(), f"test-matrix driver not found at {_SCRIPT}"


@pytest.mark.integration
@pytest.mark.timeout(120)
def test_full_test_matrix_dry_run() -> None:
    bash = shutil.which("bash")
    if bash is None:  # pragma: no cover - bash absent (non-POSIX CI)
        pytest.skip("bash not available")

    proc = subprocess.run(
        [bash, str(_SCRIPT), "--dry-run"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    out = proc.stdout + proc.stderr

    assert proc.returncode == 0, f"--dry-run exited {proc.returncode}\n{out}"
    # The plan must name the three test segments and explicitly not run anything.
    assert "--dry-run" in out
    assert "planned test segments" in out
    for segment in ("unit_parity", "integration_reconcile", "bowaka_common"):
        assert segment in out, f"dry-run plan missing segment '{segment}'\n{out}"
    assert "dry-run complete" in out
    assert "no tests executed" in out
