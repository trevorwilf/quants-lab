"""build_broker_reject_record produces a schema-valid decision with reason=broker_reject."""
from __future__ import annotations

from bowaka_v2_lab.schemas.decisions import build_broker_reject_record
from bowaka_v2_lab.schemas.events import validate_entry_decision


def _candidate() -> dict:
    return {
        "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "session_date": "2024-09-04",
        "symbol": "AAA",
        "scan_timestamp": "2024-09-04T13:30:00Z",
    }


def test_broker_reject_record_is_rejected_with_canonical_reason() -> None:
    rec = build_broker_reject_record(
        _candidate(),
        decision_ts="2024-09-04T13:30:05Z",
        broker_status="rejected_insufficient_buying_power",
        raw_response_summary={"code": "INSUFFICIENT_BP"},
        order_plan={"side": "buy", "order_style": "marketable_limit",
                     "qty": 100, "estimated_notional": 1005.0,
                     "stop_pct": 0.02, "target_pct": 0.05, "max_hold_days": 5},
        quote={"bid": 10.0, "ask": 10.1, "mid": 10.05, "spread_pct": 0.01,
                "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 1.0},
        risk_snapshot={"bankroll": 100000, "gross_exposure_dollars": 0,
                        "gross_exposure_pct": 0, "entries_today": 0,
                        "open_positions": 0, "candidate_adv": 10000000,
                        "target_notional": 5000, "adv_participation_frac": 0.0005},
    )
    assert rec["decision"] == "rejected"
    assert rec["reason"] == "broker_reject"
    assert rec["broker_status"] == "rejected_insufficient_buying_power"
    assert rec["raw_response_summary"] == {"code": "INSUFFICIENT_BP"}
    ok, problems = validate_entry_decision(rec)
    assert ok, problems
