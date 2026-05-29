"""Phase 0 (phases 4-7) — verify-bayesian-fix Section 4 assembles 3 rows.

Section 4 drives the current-code-parity full-fold preflight integration tests
via ``_run_pytest_file``. The unit test monkeypatches that runner so it does
not actually shell out — it asserts the section's Check assembly logic.
"""
from __future__ import annotations

from bowaka_v2_lab.devtools import verify_bayesian_fix as vbf


def test_section4_three_rows_all_pass_when_underlying_pass(monkeypatch) -> None:
    monkeypatch.setattr(vbf, "_run_pytest_file", lambda path: True)
    checks = vbf._section4()
    assert len(checks) == 3
    assert all(c.section == "4" for c in checks)
    assert all(c.passed for c in checks)


def test_section4_rows_fail_when_underlying_fail(monkeypatch) -> None:
    monkeypatch.setattr(vbf, "_run_pytest_file", lambda path: False)
    checks = vbf._section4()
    assert len(checks) == 3
    assert all(c.section == "4" for c in checks)
    assert all(not c.passed for c in checks)
