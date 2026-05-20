"""Paper-log schema validators."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.paper_log_schema import validate_paper_record


def test_minimal_candidate_passes() -> None:
    rec = {"event_id": "x", "session_date": "2024-09-04", "symbol": "AAA",
            "scan_timestamp": "2024-09-04T14:00:00Z", "signal_strength": 1.0}
    assert validate_paper_record("candidate", rec) == []


def test_missing_fields_reported() -> None:
    rec = {"event_id": "x"}
    issues = validate_paper_record("candidate", rec)
    assert any("session_date" in i for i in issues)
    assert any("symbol" in i for i in issues)


def test_unknown_kind_rejected() -> None:
    issues = validate_paper_record("bogus", {})
    assert any("unknown" in i for i in issues)
