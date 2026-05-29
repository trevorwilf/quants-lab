"""Phase 0 (phases 4-7) — Section 8 junit-counts parser."""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.devtools import verify_bayesian_fix as vbf


def test_parse_junit_testsuites_wrapper(tmp_path: Path) -> None:
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuites><testsuite name="pytest" tests="5" errors="0" '
        'failures="1" skipped="1"></testsuite></testsuites>'
    )
    p = tmp_path / "junit.xml"
    p.write_text(xml, encoding="utf-8")
    counts = vbf._parse_junit_counts(p)
    assert counts == {"tests": 5, "passed": 3, "failed": 1, "skipped": 1}


def test_parse_junit_bare_testsuite_root(tmp_path: Path) -> None:
    xml = '<testsuite tests="3" errors="1" failures="0" skipped="0"></testsuite>'
    p = tmp_path / "junit2.xml"
    p.write_text(xml, encoding="utf-8")
    counts = vbf._parse_junit_counts(p)
    assert counts == {"tests": 3, "passed": 2, "failed": 1, "skipped": 0}


def test_parse_junit_missing_file_returns_none(tmp_path: Path) -> None:
    assert vbf._parse_junit_counts(tmp_path / "does_not_exist.xml") is None
