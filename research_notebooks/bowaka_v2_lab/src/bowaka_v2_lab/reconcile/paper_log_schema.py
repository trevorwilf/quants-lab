"""Canonical paper-log JSON shapes.

Two layers live here:

- **Phase-7 dict shapes** (``CANDIDATE_FIELDS`` / ``DECISION_FIELDS`` /
  ``ORDER_FIELDS`` / ``FILL_FIELDS`` + :func:`validate_paper_record`) — the
  original mismatch-category importer keys on these. Unchanged for backward
  compatibility with the existing reconcile suite.
- **Realism remediation 2 Phase 9 Pydantic models** — the expanded event
  taxonomy (``paper_candidate``, ``paper_decision``, ``paper_parent_submit``,
  ``paper_parent_ack``, ``paper_parent_fill``, ``paper_oco_attempt``,
  ``paper_oco_attached``, ``paper_child_fill``, ``paper_position_close``,
  ``paper_daily_summary``). Each carries a ``timestamp``, ``symbol``,
  ``parent_order_id``, ``child_order_ids[]`` and a ``source_log_file`` field so
  every record points back at the JSONL it was read from.

The Phase-10 reconciliation framework (``schemas``, ``comparators``, ``replay``,
``report``) keys its side-by-side rows on ``candidate_event_id`` and is
unaffected — the Phase-9 models live alongside them as a richer event
representation for the calibration utilities (``slippage_residuals``,
``oco_latency_calibrator``) and the synthetic-paper-log fixture.
"""
from __future__ import annotations

from typing import Any, List, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------
# Phase-7 dict shapes (unchanged).
# --------------------------------------------------------------------------
CANDIDATE_FIELDS = ("event_id", "session_date", "symbol", "scan_timestamp", "signal_strength")
DECISION_FIELDS = ("event_id", "candidate_event_id", "session_date", "symbol",
                    "decision", "reason", "decision_timestamp")
ORDER_FIELDS = ("parent_order_id", "symbol", "side", "qty", "limit_price", "submit_timestamp", "status")
FILL_FIELDS = ("parent_order_id", "symbol", "filled_qty", "avg_fill_price", "fill_timestamp")

_FIELD_SETS = {
    "candidate": frozenset(CANDIDATE_FIELDS),
    "decision":  frozenset(DECISION_FIELDS),
    "order":     frozenset(ORDER_FIELDS),
    "fill":      frozenset(FILL_FIELDS),
}


def validate_paper_record(kind: str, rec: Mapping[str, object]) -> list[str]:
    """Return a list of "missing field" issues for a Phase-7 paper record dict.

    Empty list ⇒ the record carries every canonical field for its ``kind``.
    """
    fields = _FIELD_SETS.get(kind)
    if fields is None:
        return [f"unknown kind {kind!r}"]
    missing = sorted(fields - set(rec.keys()))
    return [f"missing field {f!r}" for f in missing]


# --------------------------------------------------------------------------
# Realism remediation 2 Phase 9 — typed Pydantic event models.
# --------------------------------------------------------------------------
class _PaperEventBase(BaseModel):
    """Tolerant base for Phase-9 paper-log events.

    Paper logs evolve, so unknown keys are kept rather than rejected. Every
    event carries the four canonical correlation fields:

    - ``timestamp`` — UTC ISO-8601 string of when the event occurred.
    - ``symbol`` — the ticker the event is about.
    - ``parent_order_id`` — the parent order the event descends from (None for
      candidate / decision rows that pre-date order submission).
    - ``child_order_ids`` — child order ids (OCO take-profit + stop) attached
      to the parent (empty until attachment).
    - ``source_log_file`` — the JSONL file the record was read from (e.g.
      ``parent_fills.jsonl``); set by the importer and never user-supplied.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    timestamp: Optional[str] = None
    symbol: Optional[str] = None
    parent_order_id: Optional[str] = None
    child_order_ids: List[str] = Field(default_factory=list)
    source_log_file: Optional[str] = None


class PaperCandidateEvent(_PaperEventBase):
    """A ``paper_candidate`` event — a candidate-signal emission."""

    event_id: Optional[str] = None
    candidate_event_id: Optional[str] = None
    session_date: Optional[str] = None
    scan_timestamp: Optional[str] = None
    signal_strength: Optional[float] = None


class PaperDecisionEvent(_PaperEventBase):
    """A ``paper_decision`` event — accept / reject + reason for a candidate."""

    event_id: Optional[str] = None
    candidate_event_id: Optional[str] = None
    session_date: Optional[str] = None
    decision: Optional[str] = None
    reason: Optional[str] = None
    decision_timestamp: Optional[str] = None


class PaperParentSubmit(_PaperEventBase):
    """A ``paper_parent_submit`` event — parent order submitted to the broker."""

    candidate_event_id: Optional[str] = None
    side: Optional[str] = None
    qty: Optional[float] = None
    limit_price: Optional[float] = None
    submit_timestamp: Optional[str] = None
    order_style: Optional[str] = None  # "market" | "marketable_limit"


class PaperParentAck(_PaperEventBase):
    """A ``paper_parent_ack`` event — broker acknowledged the parent order."""

    candidate_event_id: Optional[str] = None
    ack_timestamp: Optional[str] = None
    status: Optional[str] = None  # "accepted" | "rejected" | ...


class PaperParentFill(_PaperEventBase):
    """A ``paper_parent_fill`` event — parent order (partially) filled."""

    candidate_event_id: Optional[str] = None
    filled_qty: Optional[float] = None
    avg_fill_price: Optional[float] = None
    fill_timestamp: Optional[str] = None
    is_partial: Optional[bool] = None


class PaperOCOAttempt(_PaperEventBase):
    """A ``paper_oco_attempt`` event — an attach attempt (success or failure)."""

    attempt_index: Optional[int] = None  # 1-based attempt counter
    attempt_timestamp: Optional[str] = None
    outcome: Optional[str] = None  # "success" | "failure"
    failure_reason: Optional[str] = None


class PaperOCOAttached(_PaperEventBase):
    """A ``paper_oco_attached`` event — the bracket is live at the broker."""

    attached_timestamp: Optional[str] = None
    stop_price: Optional[float] = None
    target_price: Optional[float] = None


class PaperChildFill(_PaperEventBase):
    """A ``paper_child_fill`` event — a child (stop / take-profit) order filled."""

    child_order_id: Optional[str] = None
    child_kind: Optional[str] = None  # "stop" | "take_profit"
    filled_qty: Optional[float] = None
    avg_fill_price: Optional[float] = None
    fill_timestamp: Optional[str] = None


class PaperPositionClose(_PaperEventBase):
    """A ``paper_position_close`` event — the lot is flat (PnL realized)."""

    position_id: Optional[str] = None
    exit_reason: Optional[str] = None  # "take_profit" | "stop" | "time_stop" | ...
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    exit_timestamp: Optional[str] = None


class PaperDailySummary(_PaperEventBase):
    """A ``paper_daily_summary`` event — end-of-day session summary row."""

    session_date: Optional[str] = None
    n_entries: Optional[int] = None
    n_exits: Optional[int] = None
    realized_pnl: Optional[float] = None
    end_of_day_timestamp: Optional[str] = None


#: One Pydantic model per Phase-9 event ``kind``. Used by the importer to
#: validate a row and by the comparators to type-check inputs.
PAPER_EVENT_MODELS: dict[str, type[_PaperEventBase]] = {
    "paper_candidate": PaperCandidateEvent,
    "paper_decision": PaperDecisionEvent,
    "paper_parent_submit": PaperParentSubmit,
    "paper_parent_ack": PaperParentAck,
    "paper_parent_fill": PaperParentFill,
    "paper_oco_attempt": PaperOCOAttempt,
    "paper_oco_attached": PaperOCOAttached,
    "paper_child_fill": PaperChildFill,
    "paper_position_close": PaperPositionClose,
    "paper_daily_summary": PaperDailySummary,
}


def validate_paper_event(kind: str, rec: Mapping[str, Any]) -> _PaperEventBase:
    """Validate ``rec`` against the typed Phase-9 event model for ``kind``.

    Raises ``KeyError`` if ``kind`` is unknown; ``pydantic.ValidationError`` if
    the record fails validation against the model's strict-typed fields.
    """
    model = PAPER_EVENT_MODELS[kind]
    return model.model_validate(rec)


__all__ = [
    # Phase-7 dict shapes.
    "CANDIDATE_FIELDS", "DECISION_FIELDS", "ORDER_FIELDS", "FILL_FIELDS",
    "validate_paper_record",
    # Phase-9 typed models.
    "PaperCandidateEvent", "PaperDecisionEvent",
    "PaperParentSubmit", "PaperParentAck", "PaperParentFill",
    "PaperOCOAttempt", "PaperOCOAttached", "PaperChildFill",
    "PaperPositionClose", "PaperDailySummary",
    "PAPER_EVENT_MODELS", "validate_paper_event",
]
