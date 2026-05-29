"""Phase 1 (audit 2026-05-29 §9 Phase 7) — the SIP migration runbook stays real.

Parses the runbook's verified-cutover section and asserts it references config
paths and CLI subcommands that actually exist at ``dev`` HEAD (catches doc rot).
"""
from __future__ import annotations

from pathlib import Path

_LAB = Path(__file__).resolve().parents[2]
_RUNBOOK = _LAB / "docs" / "sip_migration_runbook.md"


def test_runbook_references_existing_sip_config() -> None:
    body = _RUNBOOK.read_text(encoding="utf-8")
    assert "bowaka_v2_actual_sip_intended_realism.yml" in body
    assert (_LAB / "configs" / "bowaka_v2_actual_sip_intended_realism.yml").is_file()


def test_runbook_references_real_cli_subcommands() -> None:
    body = _RUNBOOK.read_text(encoding="utf-8")
    cli_src = (_LAB / "src" / "bowaka_v2_lab" / "cli.py").read_text(encoding="utf-8")
    for sub in ("verify-bayesian-fix", "verify-realism-stress"):
        assert sub in body, f"runbook missing {sub}"
        assert f'"{sub}"' in cli_src, f"{sub} is not a registered CLI subcommand"


def test_runbook_has_verified_cutover_section() -> None:
    body = _RUNBOOK.read_text(encoding="utf-8")
    assert "SIP cutover runbook (verified against the synthetic-SIP smoke" in body
    # The five cutover steps are present.
    for step in ("Step 1", "Step 2", "Step 3", "Step 4", "Step 5"):
        assert step in body, f"runbook missing {step}"
