"""Phase 5 (audit 2026-05-29 §9 Phase 7) — the SIP migration runbook ships."""
from __future__ import annotations

from pathlib import Path

_LAB_ROOT = Path(__file__).resolve().parents[2]


def test_runbook_present_with_six_steps() -> None:
    runbook = _LAB_ROOT / "docs" / "sip_migration_runbook.md"
    assert runbook.is_file()
    body = runbook.read_text(encoding="utf-8")
    assert "# SIP migration runbook" in body
    # The six operator steps are present.
    for n in range(1, 7):
        assert f"{n}. " in body, f"runbook missing step {n}"
