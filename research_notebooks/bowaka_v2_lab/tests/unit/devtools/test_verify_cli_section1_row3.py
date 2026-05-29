"""Phase 0 (phases 4-7) — Section 1 gains the end-to-end status=failed row.

Row 3 proves a 3-trial+ all--1.5 study writes a status=failed artifact and
raises OptunaStudyInvalidError. Rows 1-2 are the direct study-validity checks.
"""
from __future__ import annotations

from bowaka_v2_lab.devtools import verify_bayesian_fix as vbf


def test_section1_has_three_rows_including_status_failed(monkeypatch) -> None:
    monkeypatch.setattr(vbf, "_run_pytest_file", lambda path: True)
    checks = vbf._section1(run_test_backed=True)
    assert len(checks) >= 3
    # the final row is the end-to-end status=failed proof
    assert "status=failed" in checks[2].name
    assert checks[2].passed


def test_section1_omits_row3_when_test_backed_disabled() -> None:
    checks = vbf._section1(run_test_backed=False)
    assert len(checks) == 2
    assert all("status=failed" not in c.name for c in checks)
