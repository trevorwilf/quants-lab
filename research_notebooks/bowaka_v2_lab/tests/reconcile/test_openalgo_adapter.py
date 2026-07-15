"""Unit tests for the openalgo -> reconciler paper-logs adapter.

Transform-only tests on a tiny synthetic openalgo-shaped fixture: they assert
the adapter's field mapping and that its output round-trips through the REAL
reconciler importer (``reconcile.replay.load_paper_session``). No fill / strategy
realism is claimed here — only the log-reshaping contract.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.reconcile.openalgo_adapter import (
    adapt_openalgo_logs,
    is_closure,
    session_from_candidate_id,
    synth_from_closure,
)


def _cid(session: str, symbol: str, ts: str) -> str:
    return f"bowaka_v2:{session}:{symbol}:{ts}"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _fixture_src(src: Path) -> None:
    """A 2-session openalgo data dir: 2 closed trades + 1 still-open entry."""
    c1 = _cid("2026-07-08", "AAA", "2026-07-08T14:00:00Z")
    c2 = _cid("2026-07-08", "BBB", "2026-07-08T14:05:00Z")  # rejected
    c3 = _cid("2026-07-09", "CCC", "2026-07-09T15:00:00Z")
    c4 = _cid("2026-07-08", "DDD", "2026-07-08T14:10:00Z")  # open (no closure)

    _write_jsonl(src / "candidate_events.jsonl", [
        {"event_id": c1, "session_date": "2026-07-08", "symbol": "AAA",
         "scan_timestamp": "2026-07-08T14:00:00Z", "features": {"signal_strength": 0.7}},
        {"event_id": c2, "session_date": "2026-07-08", "symbol": "BBB",
         "scan_timestamp": "2026-07-08T14:05:00Z", "features": {"signal_strength": 0.3}},
        {"event_id": c3, "session_date": "2026-07-09", "symbol": "CCC",
         "scan_timestamp": "2026-07-09T15:00:00Z", "features": {"signal_strength": 0.9}},
        {"event_id": c4, "session_date": "2026-07-08", "symbol": "DDD",
         "scan_timestamp": "2026-07-08T14:10:00Z", "features": {"signal_strength": 0.6}},
    ])
    _write_jsonl(src / "entry_decisions.jsonl", [
        {"event_id": c1 + ":entry", "candidate_event_id": c1, "session_date": "2026-07-08",
         "symbol": "AAA", "decision": "accepted", "reason": "all_gates_pass",
         "decision_timestamp": "2026-07-08T14:00:30Z"},
        {"event_id": c2 + ":entry", "candidate_event_id": c2, "session_date": "2026-07-08",
         "symbol": "BBB", "decision": "rejected", "reason": "spread_too_wide",
         "decision_timestamp": "2026-07-08T14:05:30Z"},
        {"event_id": c3 + ":entry", "candidate_event_id": c3, "session_date": "2026-07-09",
         "symbol": "CCC", "decision": "accepted", "reason": "all_gates_pass",
         "decision_timestamp": "2026-07-09T15:00:30Z"},
    ])
    _write_jsonl(src / "trade_ledger.jsonl", [
        # AAA — a completed round-trip. entry_fill carries the Tier-1 fields
        # (candidate_event_id + parent_submitted_at); ts is the fill time.
        {"event_type": "entry_fill", "ts": "2026-07-08T14:01:05Z", "symbol": "AAA",
         "order_id": "PID-AAA", "filled_qty": 100, "filled_avg_price": 5.0,
         "link_id": "OID-AAA", "candidate_event_id": c1,
         "parent_submitted_at": "2026-07-08T14:01:00Z"},  # submit->fill = 5s
        {"event_type": "bracket_attached", "ts": "2026-07-08T14:01:08Z", "symbol": "AAA",
         "link_id": "OID-AAA", "stop_id": "S1", "target_id": "T1",
         "stop_price": 4.05, "target_price": 7.23},  # fill->attach = 3s
        {"event_type": "closure", "record_type": "closure", "symbol": "AAA", "qty": 100,
         "entry_price": 5.0, "entry_timestamp": "2026-07-08T14:01:00Z",
         "exit_price": 6.0, "exit_timestamp": "2026-07-08T15:30:00Z",
         "realized_pnl": 100.0, "reason": "target_hit", "link_id": "OID-AAA",
         "candidate_event_id": c1},
        # CCC — a completed round-trip with NO entry_fill event: submit time falls
        # back to closure.entry_timestamp, and there's no fill_ts (no submit->fill).
        {"event_type": "closure", "record_type": "closure", "symbol": "CCC", "qty": 50,
         "entry_price": 10.0, "entry_timestamp": "2026-07-09T15:01:00Z",
         "exit_price": 9.0, "exit_timestamp": "2026-07-09T15:45:00Z",
         "realized_pnl": -50.0, "reason": "stop_hit", "link_id": "OID-CCC",
         "candidate_event_id": c3},
        # DDD — an open entry (no closure -> skipped for orders/fills/exits) but its
        # entry_fill still yields submit->fill latency (Tier-1 open-position support).
        {"event_type": "entry_fill", "ts": "2026-07-08T14:11:00Z", "symbol": "DDD",
         "order_id": "PID-DDD", "filled_qty": 200, "filled_avg_price": 3.0,
         "link_id": "OID-DDD", "candidate_event_id": c4,
         "parent_submitted_at": "2026-07-08T14:10:50Z"},  # submit->fill = 10s
    ])


def test_session_from_candidate_id():
    assert session_from_candidate_id("bowaka_v2:2026-07-08:TVRD:2026-07-08T15:51:56Z") == "2026-07-08"
    assert session_from_candidate_id("no-colons") is None
    assert session_from_candidate_id(None) is None


def test_synth_from_closure_maps_fields():
    closure = {
        "event_type": "closure", "record_type": "closure", "symbol": "AAA", "qty": 100,
        "entry_price": 5.0, "entry_timestamp": "2026-07-08T14:01:00Z",
        "exit_price": 6.0, "exit_timestamp": "2026-07-08T15:30:00Z",
        "realized_pnl": 100.0, "reason": "target_hit", "link_id": "OID-AAA",
        "candidate_event_id": "bowaka_v2:2026-07-08:AAA:2026-07-08T14:00:00Z",
    }
    assert is_closure(closure)
    session, order, fill, exit_ = synth_from_closure(closure)
    assert session == "2026-07-08"
    assert order["parent_order_id"] == "OID-AAA" and order["side"] == "buy"
    assert fill["avg_fill_price"] == 5.0 and fill["filled_qty"] == 100
    assert fill["parent_order_id"] == "OID-AAA"
    assert exit_["exit_price"] == 6.0 and exit_["exit_reason"] == "target_hit"
    assert exit_["realized_pnl"] == 100.0
    # every synthesised record shares the join key.
    assert order["candidate_event_id"] == fill["candidate_event_id"] == exit_["candidate_event_id"]


def test_adapt_end_to_end(tmp_path: Path):
    src = tmp_path / "openalgo_data"
    out = tmp_path / "paper_logs"
    _fixture_src(src)

    res = adapt_openalgo_logs(src, out)

    assert set(res.sessions) == {"2026-07-08", "2026-07-09"}
    assert res.n_closures == 2
    assert res.n_orders == res.n_fills == res.n_exits == 2
    assert res.n_open_skipped == 1  # DDD entry with no closure

    # files exist per session, in the layout discover_sessions/load_paper_session read.
    for s in ("2026-07-08", "2026-07-09"):
        for name in ("candidate_events", "entry_decisions", "orders", "fills", "exits"):
            assert (out / s / f"{name}.jsonl").is_file()


def test_adapt_output_roundtrips_through_reconciler(tmp_path: Path):
    """The adapter output must load cleanly via the reconciler's own importer."""
    from bowaka_v2_lab.reconcile.replay import load_paper_session

    src = tmp_path / "openalgo_data"
    out = tmp_path / "paper_logs"
    _fixture_src(src)
    adapt_openalgo_logs(src, out)

    sess = load_paper_session(out / "2026-07-08", "2026-07-08")
    # 2 candidates (AAA, BBB) + the open DDD = 3 candidates for the session.
    assert {c.symbol for c in sess.candidates} == {"AAA", "BBB", "DDD"}
    assert {d.symbol for d in sess.decisions} == {"AAA", "BBB"}
    # only the closed AAA lot yields an order/fill/exit.
    assert [o.parent_order_id for o in sess.orders] == ["OID-AAA"]
    assert sess.fills[0].avg_fill_price == 5.0
    assert sess.exits[0].exit_price == 6.0 and sess.exits[0].exit_reason == "target_hit"
    # candidate_event_id links the fill back to AAA's candidate.
    assert sess.fills[0].candidate_event_id == _cid("2026-07-08", "AAA", "2026-07-08T14:00:00Z")

    sess9 = load_paper_session(out / "2026-07-09", "2026-07-09")
    assert sess9.exits[0].exit_reason == "stop_hit"
    assert sess9.exits[0].realized_pnl == -50.0


def test_latency_capture(tmp_path: Path):
    src = tmp_path / "openalgo_data"
    out = tmp_path / "paper_logs"
    _fixture_src(src)
    res = adapt_openalgo_logs(src, out)

    s2f = res.latency_summary["submit_to_fill_seconds"]
    f2a = res.latency_summary["fill_to_attach_seconds"]
    # Tier 1: AAA (5s) + DDD (10s) have submit->fill; CCC has no fill event.
    assert s2f["n"] == 2
    assert s2f["max_s"] == 10.0
    assert s2f["median_s"] == 7.5
    # Tier 0: only AAA has an OCO attach event (fill->attach = 3s).
    assert f2a["n"] == 1
    assert f2a["max_s"] == 3.0
    # Phase-9 event rows: 3 submits (AAA, DDD, CCC-fallback), 2 fills (AAA, DDD),
    # 1 attach (AAA).
    assert res.n_parent_submits == 3
    assert res.n_parent_fills == 2
    assert res.n_oco_attached == 1


def test_phase9_latency_files_roundtrip(tmp_path: Path):
    """The Phase-9 latency files must load via the reconciler's typed reader."""
    from bowaka_v2_lab.reconcile.importer import import_paper_event_logs

    src = tmp_path / "openalgo_data"
    out = tmp_path / "paper_logs"
    _fixture_src(src)
    adapt_openalgo_logs(src, out)

    imp = import_paper_event_logs(out / "2026-07-08", session_date="2026-07-08")
    fills = imp.by_kind("paper_parent_fill")
    attached = imp.by_kind("paper_oco_attached")
    assert {f.symbol for f in fills} == {"AAA", "DDD"}
    assert [a.symbol for a in attached] == ["AAA"]
    # fill_timestamp / attached_timestamp populated — what latency reconciliation needs.
    aaa = next(f for f in fills if f.symbol == "AAA")
    assert aaa.fill_timestamp is not None and aaa.parent_order_id == "OID-AAA"
    assert attached[0].attached_timestamp is not None
