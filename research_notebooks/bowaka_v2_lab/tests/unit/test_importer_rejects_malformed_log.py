"""Phase 9 — :func:`import_paper_event_logs` flags / rejects malformed rows.

The Phase-9 importer is *tolerant by default*: malformed rows are dropped and
recorded on ``drift_issues`` so the caller can surface them, but the reader
itself does not crash on one bad row. With ``strict=True`` the first bad row
raises ``pydantic.ValidationError`` immediately.

This test exercises both modes and the env-var fallback for
``$BOWAKA_V2_PAPER_LOGS_ROOT``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from bowaka_v2_lab.reconcile.importer import (
    PaperLogsNotFoundError,
    import_paper_event_logs,
    resolve_paper_logs_root,
)


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_missing_root_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """No path supplied and no env var → :class:`PaperLogsNotFoundError`."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    with pytest.raises(PaperLogsNotFoundError):
        import_paper_event_logs(None)


def test_root_is_not_a_directory(tmp_path: Path) -> None:
    """A file path (not a directory) raises :class:`PaperLogsNotFoundError`."""
    bogus = tmp_path / "i-am-a-file"
    bogus.write_text("hello", encoding="utf-8")
    with pytest.raises(PaperLogsNotFoundError):
        import_paper_event_logs(bogus)


def test_env_var_fallback_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When ``paper_logs_root`` is None, the env var is honoured."""
    monkeypatch.setenv("BOWAKA_V2_PAPER_LOGS_ROOT", str(tmp_path))
    result = import_paper_event_logs(None)
    assert result.paper_logs_root == tmp_path
    assert result.n_events == 0


def test_resolve_helper_explicit_beats_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit path wins over ``$BOWAKA_V2_PAPER_LOGS_ROOT``."""
    other = tmp_path / "explicit"
    other.mkdir()
    monkeypatch.setenv("BOWAKA_V2_PAPER_LOGS_ROOT", str(tmp_path))
    assert resolve_paper_logs_root(other) == other


def test_tolerant_mode_drops_malformed_row(tmp_path: Path) -> None:
    """A bad row is dropped + recorded on ``drift_issues``; good rows survive."""
    # paper_parent_fills.jsonl: one well-formed + one with a type-clash field.
    _write_jsonl(tmp_path / "paper_parent_fills.jsonl", [
        '{"symbol": "AAA", "parent_order_id": "po1", '
        '"timestamp": "2024-09-03T13:45:01Z", "filled_qty": 100, '
        '"avg_fill_price": 10.0, "candidate_event_id": "c:AAA"}',
        # avg_fill_price is a string that can't be parsed as float
        '{"symbol": "BBB", "parent_order_id": "po2", '
        '"timestamp": "2024-09-03T13:46:01Z", "filled_qty": 50, '
        '"avg_fill_price": "not-a-price", "candidate_event_id": "c:BBB"}',
    ])
    result = import_paper_event_logs(tmp_path)
    fills = result.events_by_kind["paper_parent_fill"]
    assert len(fills) == 1
    assert fills[0].symbol == "AAA"
    assert any("paper_parent_fills.jsonl" in issue for issue in result.drift_issues)


def test_strict_mode_raises_on_malformed(tmp_path: Path) -> None:
    """With ``strict=True`` the first bad row raises :class:`ValidationError`."""
    _write_jsonl(tmp_path / "paper_parent_fills.jsonl", [
        '{"symbol": "BBB", "parent_order_id": "po2", '
        '"timestamp": "2024-09-03T13:46:01Z", "filled_qty": 50, '
        '"avg_fill_price": "not-a-price"}',
    ])
    with pytest.raises(ValidationError):
        import_paper_event_logs(tmp_path, strict=True)


def test_non_dict_jsonl_row_recorded(tmp_path: Path) -> None:
    """A row whose top-level JSON is a list, not a dict, is dropped + flagged."""
    _write_jsonl(tmp_path / "paper_candidates.jsonl", [
        '[1, 2, 3]',
        '{"symbol": "AAA", "timestamp": "2024-09-03T13:45:00Z", '
        '"event_id": "e", "candidate_event_id": "c:AAA", '
        '"session_date": "2024-09-03", "scan_timestamp": "2024-09-03T13:45:00Z"}',
    ])
    result = import_paper_event_logs(tmp_path)
    assert len(result.events_by_kind["paper_candidate"]) == 1
    assert any(
        "row is not a JSON object" in issue for issue in result.drift_issues
    )


def test_session_filter_drops_other_dates(tmp_path: Path) -> None:
    """``session_date`` filter keeps only rows for that session."""
    _write_jsonl(tmp_path / "paper_candidates.jsonl", [
        '{"symbol": "AAA", "timestamp": "2024-09-03T13:45:00Z", '
        '"event_id": "e1", "candidate_event_id": "c:AAA", '
        '"session_date": "2024-09-03", "scan_timestamp": "2024-09-03T13:45:00Z"}',
        '{"symbol": "BBB", "timestamp": "2024-09-04T13:45:00Z", '
        '"event_id": "e2", "candidate_event_id": "c:BBB", '
        '"session_date": "2024-09-04", "scan_timestamp": "2024-09-04T13:45:00Z"}',
    ])
    result = import_paper_event_logs(tmp_path, session_date="2024-09-03")
    cs = result.events_by_kind["paper_candidate"]
    assert len(cs) == 1
    assert cs[0].symbol == "AAA"


def test_source_log_file_stamped(tmp_path: Path) -> None:
    """Every event carries the ``source_log_file`` the importer set."""
    _write_jsonl(tmp_path / "paper_parent_acks.jsonl", [
        '{"symbol": "AAA", "parent_order_id": "po1", '
        '"timestamp": "2024-09-03T13:45:01Z", '
        '"ack_timestamp": "2024-09-03T13:45:01Z", "status": "accepted"}',
    ])
    result = import_paper_event_logs(tmp_path)
    acks = result.events_by_kind["paper_parent_ack"]
    assert len(acks) == 1
    assert acks[0].source_log_file == "paper_parent_acks.jsonl"


def test_events_sorted_by_timestamp(tmp_path: Path) -> None:
    """Per-kind events come out in ascending timestamp order."""
    _write_jsonl(tmp_path / "paper_candidates.jsonl", [
        '{"symbol": "BBB", "timestamp": "2024-09-03T14:00:00Z", '
        '"event_id": "e2", "candidate_event_id": "c:BBB", '
        '"session_date": "2024-09-03", "scan_timestamp": "2024-09-03T14:00:00Z"}',
        '{"symbol": "AAA", "timestamp": "2024-09-03T13:45:00Z", '
        '"event_id": "e1", "candidate_event_id": "c:AAA", '
        '"session_date": "2024-09-03", "scan_timestamp": "2024-09-03T13:45:00Z"}',
    ])
    result = import_paper_event_logs(tmp_path)
    cs = result.events_by_kind["paper_candidate"]
    assert [c.symbol for c in cs] == ["AAA", "BBB"]


def test_synthetic_fixture_loads_clean(lab_root: Path) -> None:
    """The frozen synthetic 2024-09-03 fixture loads with zero drift."""
    fixture_dir = lab_root / "tests" / "fixtures" / "paper_logs" / "2024-09-03"
    result = import_paper_event_logs(fixture_dir, session_date="2024-09-03")
    assert result.drift_issues == []
    counts = {k: len(v) for k, v in result.events_by_kind.items()}
    assert counts == {
        "paper_candidate": 5,
        "paper_decision": 5,
        "paper_parent_submit": 3,
        "paper_parent_ack": 3,
        "paper_parent_fill": 3,
        "paper_oco_attempt": 4,
        "paper_oco_attached": 3,
        "paper_child_fill": 1,
        "paper_position_close": 3,
        "paper_daily_summary": 1,
    }
    assert result.n_events == sum(counts.values())
