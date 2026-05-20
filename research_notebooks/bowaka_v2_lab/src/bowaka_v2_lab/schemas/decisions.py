"""Entry-decision and broker-reject decision builders.

The strategy emits an entry-decision record for every candidate it considers:
- ``accepted`` (with ``reason="all_gates_passed"``) when the order was placed.
- ``rejected`` (with a canonical reason) when the candidate was filtered.
- ``rejected`` with ``reason="broker_reject"`` when the broker refused
  the order even though the candidate passed all gates ([Report §15.1 P0]).

The simulator must emit broker_reject records via ``build_broker_reject_record``
for parity with paper / live event consumers.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .events import (
    ACCEPTED_REASON,
    CANDIDATE_EVENT_SCHEMA_VERSION,
    CANONICAL_REJECTION_REASONS,
    make_event_id,
    validate_entry_decision,
)


def _ensure_quote(q: Mapping[str, Any] | None) -> dict[str, Any]:
    base = {
        "bid": None, "ask": None, "mid": None, "spread_pct": None,
        "quote_timestamp": None, "quote_age_seconds": None,
    }
    if q:
        for k in base:
            if k in q:
                base[k] = q[k]
    return base


def _ensure_risk(r: Mapping[str, Any] | None) -> dict[str, Any]:
    base = {
        "bankroll": None, "gross_exposure_dollars": None, "gross_exposure_pct": None,
        "entries_today": None, "open_positions": None, "candidate_adv": None,
        "target_notional": None, "adv_participation_frac": None,
    }
    if r:
        for k in base:
            if k in r:
                base[k] = r[k]
    return base


def _ensure_order_plan(p: Mapping[str, Any] | None) -> dict[str, Any]:
    base = {
        "side": None, "order_style": None, "qty": None, "estimated_notional": None,
        "stop_pct": None, "target_pct": None, "max_hold_days": None,
    }
    if p:
        for k in base:
            if k in p:
                base[k] = p[k]
    return base


def _common_envelope(
    *,
    candidate_event: Mapping[str, Any],
    decision: str,
    reason: str,
    decision_ts: Any,
    entry_trigger: str,
) -> dict[str, Any]:
    session_date = candidate_event.get("session_date") or ""
    symbol = candidate_event.get("symbol") or ""
    scan_ts = candidate_event.get("scan_timestamp")
    if isinstance(decision_ts, datetime):
        decision_ts_str = decision_ts.isoformat()
    else:
        decision_ts_str = str(decision_ts)
    return {
        "schema_version": CANDIDATE_EVENT_SCHEMA_VERSION,
        "strategy": "bowaka_v2",
        "event_type": "entry_decision",
        "decision": decision,
        "reason": reason,
        "event_id": make_event_id(
            "bowaka_v2", session_date, symbol, decision_ts_str, suffix="entry",
        ),
        "candidate_event_id": candidate_event.get("event_id"),
        "session_date": session_date,
        "symbol": symbol,
        "entry_trigger": entry_trigger,
        "scan_timestamp": scan_ts,
        "decision_timestamp": decision_ts_str,
    }


def build_accepted_entry_decision(
    *,
    candidate_event: Mapping[str, Any],
    decision_ts: Any,
    entry_trigger: str,
    quote: Mapping[str, Any],
    risk_snapshot: Mapping[str, Any],
    order_plan: Mapping[str, Any],
) -> dict[str, Any]:
    rec = _common_envelope(
        candidate_event=candidate_event,
        decision="accepted",
        reason=ACCEPTED_REASON,
        decision_ts=decision_ts,
        entry_trigger=entry_trigger,
    )
    rec["quote"] = _ensure_quote(quote)
    rec["risk_snapshot"] = _ensure_risk(risk_snapshot)
    rec["order_plan"] = _ensure_order_plan(order_plan)
    return rec


def build_rejected_entry_decision(
    *,
    candidate_event: Mapping[str, Any],
    decision_ts: Any,
    entry_trigger: str,
    reason: str,
    quote: Mapping[str, Any] | None = None,
    risk_snapshot: Mapping[str, Any] | None = None,
    order_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if reason not in CANONICAL_REJECTION_REASONS:
        raise ValueError(
            f"reason {reason!r} is not in CANONICAL_REJECTION_REASONS"
        )
    rec = _common_envelope(
        candidate_event=candidate_event,
        decision="rejected",
        reason=reason,
        decision_ts=decision_ts,
        entry_trigger=entry_trigger,
    )
    rec["quote"] = _ensure_quote(quote)
    rec["risk_snapshot"] = _ensure_risk(risk_snapshot)
    rec["order_plan"] = _ensure_order_plan(order_plan)
    return rec


def build_broker_reject_record(
    candidate_event: Mapping[str, Any],
    *,
    decision_ts: Any,
    broker_status: str,
    raw_response_summary: str | Mapping[str, Any] | None,
    entry_trigger: str = "broker_submit",
    order_plan: Mapping[str, Any] | None = None,
    quote: Mapping[str, Any] | None = None,
    risk_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical broker_reject decision builder.

    Per [Report §15.1 P0] remediation: paper / live and sim must emit the
    same shape when the broker refuses an order. Without this builder, the
    sim silently dropped the candidate and reconciliation could not match
    paper rejections to sim non-events.
    """
    rec = build_rejected_entry_decision(
        candidate_event=candidate_event,
        decision_ts=decision_ts,
        entry_trigger=entry_trigger,
        reason="broker_reject",
        order_plan=order_plan,
        quote=quote,
        risk_snapshot=risk_snapshot,
    )
    rec["broker_status"] = broker_status
    rec["raw_response_summary"] = raw_response_summary
    return rec
