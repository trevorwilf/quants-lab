"""validate_entry_decision rejects accepted decisions with non-all_gates_passed reason."""
from __future__ import annotations

from bowaka_v2_lab.schemas.events import (
    ACCEPTED_REASON,
    CANDIDATE_EVENT_SCHEMA_VERSION,
    validate_entry_decision,
)


def _minimum_decision(decision: str, reason: str) -> dict:
    return {
        "schema_version": CANDIDATE_EVENT_SCHEMA_VERSION,
        "strategy": "bowaka_v2",
        "event_type": "entry_decision",
        "decision": decision,
        "reason": reason,
        "event_id": "bowaka_v2:2024-09-04:AAA:entry:2024-09-04T13:30:00Z",
        "candidate_event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "session_date": "2024-09-04",
        "symbol": "AAA",
        "entry_trigger": "limit_at_mid",
        "scan_timestamp": "2024-09-04T13:30:00Z",
        "decision_timestamp": "2024-09-04T13:30:01Z",
        "quote": {"bid": 10.0, "ask": 10.1, "mid": 10.05, "spread_pct": 0.01,
                  "quote_timestamp": "2024-09-04T13:30:01Z", "quote_age_seconds": 0.5},
        "risk_snapshot": {"bankroll": 100000, "gross_exposure_dollars": 0,
                           "gross_exposure_pct": 0, "entries_today": 0,
                           "open_positions": 0, "candidate_adv": 10000000,
                           "target_notional": 5000, "adv_participation_frac": 0.0005},
        "order_plan": {"side": "buy", "order_style": "marketable_limit", "qty": 100,
                        "estimated_notional": 1005.0, "stop_pct": 0.02, "target_pct": 0.05,
                        "max_hold_days": 5},
    }


def test_accepted_with_correct_reason_passes() -> None:
    ok, problems = validate_entry_decision(_minimum_decision("accepted", ACCEPTED_REASON))
    assert ok, problems


def test_accepted_with_wrong_reason_fails() -> None:
    ok, problems = validate_entry_decision(_minimum_decision("accepted", "some_other_reason"))
    assert not ok
    assert any("all_gates_passed" in p for p in problems)


def test_rejected_with_canonical_reason_passes() -> None:
    ok, problems = validate_entry_decision(_minimum_decision("rejected", "stale_bar"))
    assert ok, problems


def test_rejected_with_non_canonical_reason_fails() -> None:
    ok, problems = validate_entry_decision(_minimum_decision("rejected", "made_up_reason"))
    assert not ok
    assert any("CANONICAL_REJECTION_REASONS" in p for p in problems)
