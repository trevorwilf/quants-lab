"""Phase 4 (audit 2026-05-29 §9 Phase 6) — discover_sessions."""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.reconcile.importer import discover_sessions


def test_discover_sessions_filters_to_date_dirs_with_candidates(tmp_path: Path) -> None:
    (tmp_path / "2024-09-03").mkdir()
    (tmp_path / "2024-09-03" / "paper_candidates.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "2024-09-04").mkdir()  # date dir but no candidates file -> skipped
    (tmp_path / "not_a_date").mkdir()
    (tmp_path / "not_a_date" / "paper_candidates.jsonl").write_text("{}\n", encoding="utf-8")

    sessions = discover_sessions(tmp_path)
    assert [s.name for s in sessions] == ["2024-09-03"]


def test_missing_root_returns_empty(tmp_path: Path) -> None:
    assert discover_sessions(tmp_path / "does_not_exist") == []
