"""Canonical paper-log JSON shapes."""
from __future__ import annotations

from typing import Mapping


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
    fields = _FIELD_SETS.get(kind)
    if fields is None:
        return [f"unknown kind {kind!r}"]
    missing = sorted(fields - set(rec.keys()))
    return [f"missing field {f!r}" for f in missing]
