"""Phase 8 — qr.04 inspects data-quality CONTENT, not just file existence.

An empty ``checks`` list (the pre-Phase-2 placeholder) and a required-check
failure both fail ``qr.04_data_quality_report_present``.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.checklist import QUANT_REVIEWER_CHECKLIST

_QR04 = QUANT_REVIEWER_CHECKLIST["qr.04_data_quality_report_present"]


def _write_dq(rd: Path, doc: dict) -> None:
    (rd / "data_quality_report.json").write_text(json.dumps(doc), encoding="utf-8")


def test_empty_checks_list_fails_qr04(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    _write_dq(rd, {"schema_version": 2, "checks": [], "required_failures": []})
    status, evidence = _QR04(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)
    assert "empty checks" in evidence.get("detail", "")


def test_missing_dq_report_fails_qr04(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    status, evidence = _QR04(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)


def test_required_check_failure_fails_qr04(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    _write_dq(rd, {
        "schema_version": 2,
        "checks": [{"name": "coverage_missing", "status": "fail", "count": 9}],
        "required_failures": ["coverage_missing"],
    })
    status, evidence = _QR04(rd)
    assert status == "fail"
    assert "coverage_missing" in str(evidence.get("required_failures", []))


def test_populated_clean_dq_report_passes_qr04(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    _write_dq(rd, {
        "schema_version": 2,
        "checks": [{"name": "synthetic_data", "status": "warn", "count": 0}],
        "required_failures": [], "passed": 0, "warned": 1,
    })
    status, evidence = _QR04(rd)
    assert status == "pass"
    assert evidence["n_checks"] == 1
