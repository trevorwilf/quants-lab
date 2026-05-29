"""Phase 0 (phases 4-7) — Section 5 has 4 rows (2 resolver + sentinel + manifest)."""
from __future__ import annotations

from bowaka_v2_lab.devtools import verify_bayesian_fix as vbf


def test_section5_four_rows(monkeypatch) -> None:
    monkeypatch.setattr(vbf, "_run_pytest_file", lambda path: True)
    checks = vbf._section5(run_test_backed=True)
    assert len(checks) == 4
    names = [c.name for c in checks]
    assert any("sentinel" in n for n in names)
    assert any("manifest" in n for n in names)
    assert all(c.section == "5" for c in checks)


def test_section5_two_resolver_rows_when_test_backed_disabled() -> None:
    checks = vbf._section5(run_test_backed=False)
    assert len(checks) == 2
    assert all("resolver" in c.name for c in checks)
