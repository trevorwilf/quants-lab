"""Every reason literal a producer emits must be in CANONICAL_REJECTION_REASONS.

The 2026-07-11 weekly study was invalidated (DEGRADED_FOLDS_PRESENT) because
the ``sizing.compounding`` floor-halt path emitted
``reason="compounding_floor_halt"`` without the string being registered in
``CANONICAL_REJECTION_REASONS`` — ``build_rejected_entry_decision`` raises on
any unregistered reason, which silently degrades the fold at runtime (the
halt only fires when a trial loses >= 50% of the bankroll, so no ordinary
test drive reaches it). The AST scan below fails at commit time instead:
it walks every producer call site and checks each string literal inside the
``reason=`` argument (including fallbacks like ``x or "kill_switch"``).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from bowaka_v2_lab.schemas.decisions import build_rejected_entry_decision
from bowaka_v2_lab.schemas.events import (
    CANONICAL_REJECTION_REASONS,
    validate_entry_decision,
)

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "bowaka_v2_lab"

_CANDIDATE_EVENT = {
    "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
    "session_date": "2024-09-04",
    "symbol": "AAA",
    "scan_timestamp": "2024-09-04T13:30:00Z",
}


def _reason_literals(call: ast.Call) -> list[str]:
    for kw in call.keywords:
        if kw.arg == "reason":
            return [
                n.value
                for n in ast.walk(kw.value)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            ]
    return []


def test_every_emitted_rejection_reason_is_canonical() -> None:
    offenders: list[str] = []
    call_sites = 0
    for py in SRC_ROOT.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name != "build_rejected_entry_decision":
                continue
            call_sites += 1
            for reason in _reason_literals(node):
                if reason not in CANONICAL_REJECTION_REASONS:
                    offenders.append(f"{py.relative_to(SRC_ROOT)}: {reason!r}")
    assert call_sites > 0, "no build_rejected_entry_decision call sites found — scan broken?"
    assert not offenders, (
        "rejection reasons emitted by producers but missing from "
        "CANONICAL_REJECTION_REASONS: " + ", ".join(offenders)
    )


def test_compounding_floor_halt_builds_and_validates() -> None:
    rec = build_rejected_entry_decision(
        candidate_event=_CANDIDATE_EVENT,
        decision_ts="2024-09-04T13:30:01Z",
        entry_trigger="marketable_limit",
        reason="compounding_floor_halt",
        quote={"bid": 10.0, "ask": 10.1, "mid": 10.05, "spread_pct": 0.01,
               "quote_timestamp": "2024-09-04T13:30:01Z", "quote_age_seconds": 0.5},
    )
    ok, problems = validate_entry_decision(rec)
    assert ok, problems


def test_unregistered_reason_raises_at_build_time() -> None:
    with pytest.raises(ValueError, match="CANONICAL_REJECTION_REASONS"):
        build_rejected_entry_decision(
            candidate_event=_CANDIDATE_EVENT,
            decision_ts="2024-09-04T13:30:01Z",
            entry_trigger="marketable_limit",
            reason="made_up_reason",
        )
