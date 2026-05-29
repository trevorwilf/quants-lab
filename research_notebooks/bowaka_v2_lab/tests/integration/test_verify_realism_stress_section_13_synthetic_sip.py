"""Phase 1 (audit 2026-05-29 §9 Phase 7) — verify-realism-stress Section 13 has
the synthetic-SIP rows and reports them PASS against the fixture.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.devtools.verify_realism_stress import main as vrs_main


def test_section_13_synthetic_sip_rows_pass(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    rc = vrs_main(["--skip-suite", "--out", str(out)])
    text = out.read_text(encoding="utf-8")

    assert "Section 13" in text
    for row in (
        "SIP synthetic end-to-end smoke completes",
        "SIP synthetic NBBO gate refuses missing quotes",
        "SIP synthetic feed-divergence report produces data",
        "real SIP partition present",
    ):
        assert row in text, f"Section 13 missing row: {row}"

    # The three synthetic rows must be PASS (the fixture is committed); the
    # real-SIP row is DEFERRED unless the operator has ingested SIP.
    for row in (
        "SIP synthetic end-to-end smoke completes",
        "SIP synthetic NBBO gate refuses missing quotes",
        "SIP synthetic feed-divergence report produces data",
    ):
        line = next(ln for ln in text.splitlines() if ln.startswith(f"| {row} "))
        assert "PASS" in line, line
    assert "OVERALL: PASS" in text
    assert rc == 0
