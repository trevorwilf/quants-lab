"""Phase 9 — every paper-log event roundtrips through its Pydantic model.

Validates each of the ten Phase-9 event ``kind`` Pydantic schemas
(:mod:`bowaka_v2_lab.reconcile.paper_log_schema`) by constructing a record,
dumping it to JSON-friendly form, parsing it back through the model and
verifying every canonical field survived.

Roundtrip covers the four correlation fields every event carries
(``timestamp``, ``symbol``, ``parent_order_id``, ``child_order_ids``,
``source_log_file``) plus the kind-specific payload.
"""
from __future__ import annotations

import json

import pytest

from bowaka_v2_lab.reconcile.paper_log_schema import (
    PAPER_EVENT_MODELS,
    PaperCandidateEvent,
    PaperChildFill,
    PaperDailySummary,
    PaperDecisionEvent,
    PaperOCOAttached,
    PaperOCOAttempt,
    PaperParentAck,
    PaperParentFill,
    PaperParentSubmit,
    PaperPositionClose,
    validate_paper_event,
)


_ROW_SAMPLES: dict[str, dict] = {
    "paper_candidate": {
        "timestamp": "2024-09-03T13:45:00Z",
        "symbol": "AAA",
        "parent_order_id": None,
        "child_order_ids": [],
        "source_log_file": "paper_candidates.jsonl",
        "event_id": "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z",
        "candidate_event_id": "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z",
        "session_date": "2024-09-03",
        "scan_timestamp": "2024-09-03T13:45:00Z",
        "signal_strength": 4.6,
    },
    "paper_decision": {
        "timestamp": "2024-09-03T13:45:01Z",
        "symbol": "AAA",
        "parent_order_id": None,
        "child_order_ids": [],
        "source_log_file": "paper_decisions.jsonl",
        "event_id": "decision-1",
        "candidate_event_id": "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z",
        "session_date": "2024-09-03",
        "decision": "accepted",
        "reason": "all_gates_passed",
        "decision_timestamp": "2024-09-03T13:45:01Z",
    },
    "paper_parent_submit": {
        "timestamp": "2024-09-03T13:45:01.300Z",
        "symbol": "AAA",
        "parent_order_id": "po_paper_AAA_001",
        "child_order_ids": [],
        "source_log_file": "paper_parent_submits.jsonl",
        "candidate_event_id": "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z",
        "side": "buy",
        "qty": 100,
        "limit_price": 10.16,
        "submit_timestamp": "2024-09-03T13:45:01.300Z",
        "order_style": "marketable_limit",
    },
    "paper_parent_ack": {
        "timestamp": "2024-09-03T13:45:01.450Z",
        "symbol": "AAA",
        "parent_order_id": "po_paper_AAA_001",
        "child_order_ids": [],
        "source_log_file": "paper_parent_acks.jsonl",
        "candidate_event_id": "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z",
        "ack_timestamp": "2024-09-03T13:45:01.450Z",
        "status": "accepted",
    },
    "paper_parent_fill": {
        "timestamp": "2024-09-03T13:45:01.580Z",
        "symbol": "AAA",
        "parent_order_id": "po_paper_AAA_001",
        "child_order_ids": [],
        "source_log_file": "paper_parent_fills.jsonl",
        "candidate_event_id": "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z",
        "filled_qty": 100,
        "avg_fill_price": 10.16,
        "fill_timestamp": "2024-09-03T13:45:01.580Z",
        "is_partial": False,
    },
    "paper_oco_attempt": {
        "timestamp": "2024-09-03T13:45:02.080Z",
        "symbol": "AAA",
        "parent_order_id": "po_paper_AAA_001",
        "child_order_ids": [],
        "source_log_file": "paper_oco_attempts.jsonl",
        "attempt_index": 1,
        "attempt_timestamp": "2024-09-03T13:45:02.080Z",
        "outcome": "failure",
        "failure_reason": "broker_busy",
    },
    "paper_oco_attached": {
        "timestamp": "2024-09-03T13:45:02.500Z",
        "symbol": "AAA",
        "parent_order_id": "po_paper_AAA_001",
        "child_order_ids": ["co_TP_AAA", "co_SL_AAA"],
        "source_log_file": "paper_oco_attached.jsonl",
        "attached_timestamp": "2024-09-03T13:45:02.500Z",
        "stop_price": 9.95,
        "target_price": 10.77,
    },
    "paper_child_fill": {
        "timestamp": "2024-09-03T14:55:00Z",
        "symbol": "CCC",
        "parent_order_id": "po_paper_CCC_002",
        "child_order_ids": ["co_SL_CCC"],
        "source_log_file": "paper_child_fills.jsonl",
        "child_order_id": "co_SL_CCC",
        "child_kind": "stop",
        "filled_qty": 120,
        "avg_fill_price": 8.39,
        "fill_timestamp": "2024-09-03T14:55:00Z",
    },
    "paper_position_close": {
        "timestamp": "2024-09-03T18:45:00Z",
        "symbol": "AAA",
        "parent_order_id": "po_paper_AAA_001",
        "child_order_ids": [],
        "source_log_file": "paper_position_closes.jsonl",
        "position_id": "pos_paper_AAA_001",
        "exit_reason": "take_profit",
        "exit_price": 10.77,
        "realized_pnl": 61.0,
        "exit_timestamp": "2024-09-03T18:45:00Z",
    },
    "paper_daily_summary": {
        "timestamp": "2024-09-03T20:00:00Z",
        "symbol": None,
        "parent_order_id": None,
        "child_order_ids": [],
        "source_log_file": "paper_daily_summary.jsonl",
        "session_date": "2024-09-03",
        "n_entries": 3,
        "n_exits": 3,
        "realized_pnl": 53.8,
        "end_of_day_timestamp": "2024-09-03T20:00:00Z",
    },
}


@pytest.mark.parametrize("kind", sorted(_ROW_SAMPLES))
def test_paper_event_roundtrip_per_kind(kind: str) -> None:
    """A canonical row for ``kind`` roundtrips through its Pydantic model."""
    sample = _ROW_SAMPLES[kind]
    # Forward: validate.
    event = validate_paper_event(kind, sample)
    assert isinstance(event, PAPER_EVENT_MODELS[kind])
    # The four correlation fields survived.
    assert event.timestamp == sample["timestamp"]
    assert event.symbol == sample["symbol"]
    assert event.parent_order_id == sample["parent_order_id"]
    assert list(event.child_order_ids) == list(sample["child_order_ids"])
    assert event.source_log_file == sample["source_log_file"]
    # Roundtrip: dump → reload → equal payload (JSON-only fields).
    dumped = event.model_dump(mode="json")
    reparsed = PAPER_EVENT_MODELS[kind].model_validate(dumped)
    assert reparsed.model_dump(mode="json") == dumped
    # And it's JSON-serialisable end-to-end.
    json.dumps(dumped)


def test_all_paper_event_models_registered() -> None:
    """Every Phase-9 ``kind`` is registered in ``PAPER_EVENT_MODELS``."""
    expected = {
        "paper_candidate", "paper_decision",
        "paper_parent_submit", "paper_parent_ack", "paper_parent_fill",
        "paper_oco_attempt", "paper_oco_attached", "paper_child_fill",
        "paper_position_close", "paper_daily_summary",
    }
    assert set(PAPER_EVENT_MODELS) == expected


def test_correlation_fields_default_safely() -> None:
    """An event built with only symbol still validates (correlation fields default)."""
    ev = PaperParentFill(symbol="AAA")
    assert ev.parent_order_id is None
    assert ev.child_order_ids == []
    assert ev.source_log_file is None


def test_child_order_ids_list_preserved() -> None:
    """child_order_ids is a list[str], not a single string."""
    ev = PaperOCOAttached(
        symbol="AAA",
        parent_order_id="po1",
        child_order_ids=["tp1", "sl1"],
    )
    assert ev.child_order_ids == ["tp1", "sl1"]


def test_validate_paper_event_rejects_unknown_kind() -> None:
    """An unknown kind raises KeyError (no fabrication)."""
    with pytest.raises(KeyError):
        validate_paper_event("paper_unknown_kind", {})


def test_pydantic_models_are_classes() -> None:
    """Sanity: every entry in ``PAPER_EVENT_MODELS`` is a Pydantic model class."""
    from pydantic import BaseModel

    for kind, model in PAPER_EVENT_MODELS.items():
        assert isinstance(model, type), kind
        assert issubclass(model, BaseModel), kind
