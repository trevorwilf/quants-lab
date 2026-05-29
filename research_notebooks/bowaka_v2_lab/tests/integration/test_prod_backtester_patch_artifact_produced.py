"""The Phase 0 deliverable includes a patch artifact for the operator to apply
back to the live production source. Assert it exists and has non-trivial
content.
"""
from __future__ import annotations

from pathlib import Path

_LAB = Path(__file__).resolve().parents[2]


def test_patch_artifact_exists_and_documents_fix() -> None:
    patch = _LAB / "docs" / "production_backtester_fix.patch"
    md = _LAB / "docs" / "production_backtester_fix.md"
    assert patch.is_file(), "missing production_backtester_fix.patch"
    assert md.is_file(), "missing production_backtester_fix.md"
    patch_content = patch.read_text(encoding="utf-8")
    assert "bowaka_v2_backtest.py" in patch_content
    md_content = md.read_text(encoding="utf-8")
    assert "_synth" in md_content
    assert "live source" in md_content.lower() or "$BOWAKA_V2_SOURCE_ROOT" in md_content
