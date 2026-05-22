"""Phase 10 — the frozen synthetic paper-log fixture loads + validates cleanly.

Proves the on-disk ``tests/fixtures/paper_logs_synthetic/`` fixture parses into
the typed Phase-10 schemas and that ``load_paper_session`` filters to one
session correctly. No lab run here — just the paper-side loader.
"""
from __future__ import annotations

from bowaka_v2_lab.reconcile.replay import load_paper_session
from bowaka_v2_lab.reconcile.schemas import (
    PaperCandidate,
    PaperDecision,
    PaperExit,
    PaperFill,
    PaperOrder,
)

from .conftest import PAPER_LOGS_SYNTHETIC, SYNTHETIC_SESSION


def test_synthetic_fixture_loads() -> None:
    """The frozen fixture's seven log files load into typed records."""
    paper = load_paper_session(PAPER_LOGS_SYNTHETIC, SYNTHETIC_SESSION)
    assert len(paper.candidates) == 3
    assert len(paper.decisions) == 3
    assert len(paper.orders) == 1
    assert len(paper.fills) == 1
    assert len(paper.exits) == 1
    assert all(isinstance(c, PaperCandidate) for c in paper.candidates)
    assert all(isinstance(d, PaperDecision) for d in paper.decisions)
    assert all(isinstance(o, PaperOrder) for o in paper.orders)
    assert all(isinstance(f, PaperFill) for f in paper.fills)
    assert all(isinstance(x, PaperExit) for x in paper.exits)


def test_synthetic_fixture_records_link_by_candidate_id() -> None:
    """Decisions / orders / fills / exits all carry a candidate_event_id."""
    paper = load_paper_session(PAPER_LOGS_SYNTHETIC, SYNTHETIC_SESSION)
    for d in paper.decisions:
        assert d.candidate_event_id is not None
    for o in paper.orders:
        assert o.candidate_event_id is not None
    for f in paper.fills:
        assert f.candidate_event_id is not None
    for x in paper.exits:
        assert x.candidate_event_id is not None


def test_synthetic_fixture_other_session_is_empty() -> None:
    """Filtering to a session the fixture does not cover yields no records."""
    paper = load_paper_session(PAPER_LOGS_SYNTHETIC, "2099-01-01")
    assert paper.candidates == []
    assert paper.decisions == []
    assert paper.orders == []
    assert paper.fills == []
    assert paper.exits == []


def test_load_missing_directory_is_empty() -> None:
    """A non-existent paper-logs directory is not an error — just empty."""
    paper = load_paper_session("/no/such/paper/logs/dir", SYNTHETIC_SESSION)
    assert paper.candidates == []
    assert paper.decisions == []
