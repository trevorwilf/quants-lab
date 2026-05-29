"""Phase 5 (audit 2026-05-29 §9 Phase 7) — verify-realism-stress report shape.

Run with --skip-suite (fast): every section header (9-14) is present and the
overall verdict is PASS (the SIP-readiness direct checks pass; deferred cells
count as PASS-equivalent). The full test-backed run is the operator's path.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.devtools.verify_realism_stress import main as vrs_main


def test_cli_overall_pass_skip_suite(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    rc = vrs_main(["--skip-suite", "--out", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    for sec in ("Section 9", "Section 10", "Section 11", "Section 12",
                "Section 13", "Section 14"):
        assert sec in text, f"report missing {sec}"
    assert "SIP_DATA_UNAVAILABLE" in text  # the deferred divergence cell
    assert "OVERALL: PASS" in text
    assert "| FAIL |" not in text
