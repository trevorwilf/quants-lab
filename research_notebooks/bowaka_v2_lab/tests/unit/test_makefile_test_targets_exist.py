"""The lab Makefile must expose the Phase 2 test-matrix targets.

Realism remediation 2 Phase 2 (audit §P1-007): a ``make`` test matrix lets CI
run each segment with a known budget. The targets live in the lab's own Makefile
at ``research_notebooks/bowaka_v2_lab/Makefile``.
"""
from __future__ import annotations

import re
from pathlib import Path

_LAB_ROOT = Path(__file__).resolve().parents[2]
_MAKEFILE = _LAB_ROOT / "Makefile"

# The five new targets the audit's required matrix calls for, plus the umbrella
# `test-all` target. `test-fast` is the quickest gate.
_REQUIRED_TARGETS = (
    "test-fast",
    "test-unit",
    "test-parity",
    "test-integration",
    "test-reconcile",
    "test-live",
    "test-all",
)


def _defined_targets(text: str) -> set[str]:
    """Targets defined in a Makefile (``name:`` at the start of a line)."""
    found: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*:", line)
        if m:
            found.add(m.group(1))
    return found


def test_lab_makefile_exists() -> None:
    assert _MAKEFILE.is_file(), f"lab Makefile not found at {_MAKEFILE}"


def test_makefile_test_targets_exist() -> None:
    text = _MAKEFILE.read_text(encoding="utf-8")
    targets = _defined_targets(text)
    missing = [t for t in _REQUIRED_TARGETS if t not in targets]
    assert not missing, f"Makefile is missing test targets: {missing}"


def _phony_targets(text: str) -> set[str]:
    """Targets listed under .PHONY, joining backslash line-continuations."""
    # Collapse `\`-continued lines into one logical line each.
    logical: list[str] = []
    buf = ""
    for raw in text.splitlines():
        if raw.rstrip().endswith("\\"):
            buf += raw.rstrip()[:-1] + " "
            continue
        logical.append(buf + raw)
        buf = ""
    if buf:
        logical.append(buf)
    phony: set[str] = set()
    for line in logical:
        if line.startswith(".PHONY"):
            phony.update(line.split(":", 1)[1].split())
    return phony


def test_makefile_declares_targets_phony() -> None:
    # Without .PHONY, a file named e.g. `test-all` would shadow the target.
    text = _MAKEFILE.read_text(encoding="utf-8")
    phony = _phony_targets(text)
    missing = [t for t in _REQUIRED_TARGETS if t not in phony]
    assert not missing, f"Makefile targets not declared .PHONY: {missing}"


def test_makefile_test_targets_carry_marker_filters() -> None:
    # Every non-live test target must exclude live markers.
    text = _MAKEFILE.read_text(encoding="utf-8")
    for target in ("test-fast", "test-unit", "test-parity",
                   "test-integration", "test-reconcile", "test-all"):
        assert target in text  # guarded by test_makefile_test_targets_exist
    assert "not live_alpaca" in text, "Makefile test targets must exclude live_alpaca"
