"""Phase 8 — qr.06 fails when realism-mode quote coverage is below threshold.

``qr.06_quote_coverage_acceptable`` reads the ``quote_coverage`` check the
backtester appends to ``data_quality_report.json`` at finalize. When that check
is ``fail`` (realism mode, coverage below ``min_quote_coverage_pct``) the
promotion gate fails too.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.checklist import QUANT_REVIEWER_CHECKLIST

_QR06 = QUANT_REVIEWER_CHECKLIST["qr.06_quote_coverage_acceptable"]


def _dq_with_quote_coverage(rd: Path, *, coverage: float, threshold: float,
                            status: str) -> None:
    doc = {
        "schema_version": 2,
        "checks": [{
            "name": "quote_coverage",
            "status": status,
            "count": 10,
            "threshold": {"min_quote_coverage_pct": threshold},
            "evidence": {
                "historical_quote_coverage_pct": coverage,
                "min_quote_coverage_pct": threshold,
                "candidates_total": 100,
                "candidates_with_quote": int(coverage),
                "detail": "quote coverage probe",
            },
        }],
        "required_failures": ["quote_coverage"] if status == "fail" else [],
    }
    (rd / "data_quality_report.json").write_text(json.dumps(doc), encoding="utf-8")


def test_coverage_below_threshold_fails_qr06(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    # 60% coverage against a 98% floor — the finalize check is ``fail``.
    _dq_with_quote_coverage(rd, coverage=60.0, threshold=98.0, status="fail")
    status, evidence = _QR06(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)
    assert evidence["historical_quote_coverage_pct"] == 60.0
    assert evidence["min_quote_coverage_pct"] == 98.0


def test_coverage_above_threshold_passes_qr06(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    _dq_with_quote_coverage(rd, coverage=99.5, threshold=98.0, status="pass")
    status, evidence = _QR06(rd)
    assert status == "pass"
    assert evidence["historical_quote_coverage_pct"] == 99.5


def test_no_quote_coverage_check_is_unknown(tmp_path: Path) -> None:
    """A DQ report without a quote_coverage check cannot assert coverage."""
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "data_quality_report.json").write_text(
        json.dumps({"schema_version": 2, "checks": [], "required_failures": []}),
        encoding="utf-8",
    )
    status, evidence = _QR06(rd)
    assert status == "unknown"
    assert isinstance(evidence, dict)
