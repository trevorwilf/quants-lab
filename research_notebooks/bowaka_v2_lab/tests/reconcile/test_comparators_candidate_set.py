"""Phase 10 — candidate-set diff comparator: paper-only / lab-only / both."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.comparators import diff_candidate_sets
from bowaka_v2_lab.reconcile.schemas import LabCandidate, PaperCandidate


def _paper(event_id: str, symbol: str) -> PaperCandidate:
    return PaperCandidate(event_id=event_id, symbol=symbol, session_date="2024-09-04")


def _lab(event_id: str, symbol: str) -> LabCandidate:
    return LabCandidate(event_id=event_id, symbol=symbol, session_date="2024-09-04")


def test_buckets_split_correctly() -> None:
    paper = [_paper("c:AAA", "AAA"), _paper("c:BBB", "BBB"), _paper("c:CCC", "CCC")]
    lab = [_lab("c:BBB", "BBB"), _lab("c:CCC", "CCC"), _lab("c:DDD", "DDD")]
    diff = diff_candidate_sets(paper, lab)
    assert diff.both == ["c:BBB", "c:CCC"]
    assert diff.paper_only == ["c:AAA"]
    assert diff.lab_only == ["c:DDD"]
    assert (diff.n_both, diff.n_paper_only, diff.n_lab_only) == (2, 1, 1)


def test_full_overlap() -> None:
    paper = [_paper("c:AAA", "AAA"), _paper("c:BBB", "BBB")]
    lab = [_lab("c:AAA", "AAA"), _lab("c:BBB", "BBB")]
    diff = diff_candidate_sets(paper, lab)
    assert diff.both == ["c:AAA", "c:BBB"]
    assert diff.paper_only == []
    assert diff.lab_only == []


def test_disjoint_sets() -> None:
    paper = [_paper("c:AAA", "AAA")]
    lab = [_lab("c:ZZZ", "ZZZ")]
    diff = diff_candidate_sets(paper, lab)
    assert diff.both == []
    assert diff.paper_only == ["c:AAA"]
    assert diff.lab_only == ["c:ZZZ"]


def test_empty_paper_all_lab_only() -> None:
    diff = diff_candidate_sets([], [_lab("c:AAA", "AAA"), _lab("c:BBB", "BBB")])
    assert diff.paper_only == []
    assert diff.lab_only == ["c:AAA", "c:BBB"]
    assert diff.both == []


def test_empty_lab_all_paper_only() -> None:
    diff = diff_candidate_sets([_paper("c:AAA", "AAA")], [])
    assert diff.paper_only == ["c:AAA"]
    assert diff.lab_only == []
    assert diff.both == []


def test_buckets_are_sorted() -> None:
    paper = [_paper("c:9", "X"), _paper("c:1", "X"), _paper("c:5", "X")]
    lab = [_paper("c:9", "X"), _paper("c:1", "X"), _paper("c:5", "X")]
    diff = diff_candidate_sets(paper, lab)
    assert diff.both == ["c:1", "c:5", "c:9"]
