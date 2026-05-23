"""Realism remediation 2 — final consolidated report has a row per phase 0..10."""
from __future__ import annotations

from pathlib import Path

import pytest


REPORT = Path(__file__).resolve().parents[2] / "artifacts" / "2026-05-22-realism-remediation-validation.md"


@pytest.mark.parametrize("phase", list(range(11)))
def test_report_lists_every_phase(phase: int) -> None:
    if not REPORT.is_file():
        pytest.xfail(
            f"final validation report not generated yet: {REPORT}. "
            "Run Phase 11 to produce it."
        )
    text = REPORT.read_text(encoding="utf-8")
    # The per-phase outcome table opens each row with ``| <N> |``.
    assert f"| {phase} |" in text, (
        f"final-validation report missing a row for Phase {phase}; "
        f"the table must list phases 0..10"
    )
