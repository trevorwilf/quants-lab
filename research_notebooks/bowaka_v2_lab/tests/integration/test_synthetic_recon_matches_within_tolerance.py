"""Phase 9 — synthetic paper log matched against the same-shape lab side.

Drives the seven Phase-9 aggregate comparators end-to-end against a synthetic
lab record set hand-built to mirror the frozen
``tests/fixtures/paper_logs/2024-09-03/`` paper log within tolerance. The
report's ``overall_passed`` flag must come back True.

This test exercises the WHOLE Phase-9 reconciliation stack:

1. :func:`import_paper_event_logs` loads + validates the synthetic paper logs.
2. Hand-built lab events (same candidates, decisions, fills, exits and OCO
   attempts as the paper log — within tolerance, NOT byte-identical) feed into
   the seven aggregate comparators.
3. :func:`build_phase9_recon_report` aggregates the comparator outputs.
4. The report passes: emission Jaccard at 1.0, decision-reason match at 1.0,
   no fill / latency / PnL / exit / OCO flags.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.reconcile import (
    PaperEventImportResult,
    build_phase9_recon_report,
    decision_reason_confusion,
    emission_jaccard,
    exit_reason_timing,
    fill_latency_residuals,
    fill_residuals,
    import_paper_event_logs,
    load_reconcile_tolerances,
    oco_attempt_count_diff,
    pnl_residuals,
    render_phase9_recon_report,
)
from bowaka_v2_lab.reconcile.schemas import (
    LabCandidate,
    LabDecision,
    LabExit,
    LabFill,
    PaperCandidate,
    PaperDecision,
    PaperExit,
    PaperFill,
)


SESSION = "2024-09-03"


def _paper_records(lab_root: Path) -> PaperEventImportResult:
    return import_paper_event_logs(
        lab_root / "tests" / "fixtures" / "paper_logs" / SESSION,
        session_date=SESSION,
    )


def _build_lab_mirror(paper: PaperEventImportResult) -> dict:
    """Hand-build the lab-side records to mirror the paper log within tolerance.

    The lab is allowed to wobble inside the default tolerances:

    - fill prices may differ up to ``fill_price_tolerance_bps`` (5 bps)
    - fill qty: 0 share tolerance — must match exactly
    - latency p95 tolerance 200 ms — lab acks/fills can drift up to that
    - PnL tolerance $1 — lab exits drift up to that
    - exit timing tolerance 60 s — lab exits can drift up to that

    The synthetic lab here picks small positive drift on AAA fill (+2 bps),
    identical fill on DDD, identical qty everywhere, and PnL within $0.50 of
    paper. Every other field mirrors the paper log.
    """
    cand_evs = paper.events_by_kind["paper_candidate"]
    dec_evs = paper.events_by_kind["paper_decision"]
    fill_evs = paper.events_by_kind["paper_parent_fill"]
    exit_evs = paper.events_by_kind["paper_position_close"]
    ack_evs = paper.events_by_kind["paper_parent_ack"]
    oco_evs = paper.events_by_kind["paper_oco_attempt"]

    lab_candidates: list[LabCandidate] = [
        LabCandidate(event_id=str(c.event_id), symbol=str(c.symbol),
                     session_date=SESSION, scan_timestamp=c.scan_timestamp,
                     signal_strength=c.signal_strength)
        for c in cand_evs
    ]
    lab_decisions: list[LabDecision] = [
        LabDecision(candidate_event_id=d.candidate_event_id, symbol=str(d.symbol),
                    session_date=SESSION, decision=d.decision, reason=d.reason,
                    decision_timestamp=d.decision_timestamp)
        for d in dec_evs
    ]
    # Lab fills mirror paper but AAA is +2 bps; CCC partial qty matches paper
    # exactly (120); DDD identical.
    lab_fills: list[LabFill] = []
    for f in fill_evs:
        new_price = f.avg_fill_price
        if f.symbol == "AAA" and f.avg_fill_price is not None:
            # +2 bps drift on the AAA fill price (within 5 bps tolerance).
            new_price = round(f.avg_fill_price * (1.0 + 2.0 / 10_000.0), 4)
        lab_fills.append(LabFill(
            parent_order_id=str(f.parent_order_id),
            candidate_event_id=f.candidate_event_id,
            symbol=str(f.symbol),
            filled_qty=f.filled_qty,
            avg_fill_price=new_price,
            fill_timestamp=f.fill_timestamp,
        ))
    # Lab exits mirror paper but +$0.30 PnL drift on AAA (within $1 tolerance).
    lab_exits: list[LabExit] = []
    for e in exit_evs:
        new_pnl = e.realized_pnl
        if e.symbol == "AAA" and e.realized_pnl is not None:
            new_pnl = round(e.realized_pnl + 0.30, 2)
        lab_exits.append(LabExit(
            parent_order_id=e.parent_order_id,
            candidate_event_id=e.candidate_event_id,
            position_id=e.position_id,
            symbol=str(e.symbol),
            exit_reason=e.exit_reason,
            exit_price=e.exit_price,
            realized_pnl=new_pnl,
            exit_timestamp=e.exit_timestamp,
        ))
    # Lab latency: identical ack→fill timestamps as paper (so latency diff = 0).
    lab_acks = {
        ev.candidate_event_id: ev.ack_timestamp
        for ev in ack_evs if ev.candidate_event_id and ev.ack_timestamp
    }
    lab_fills_ts = {
        ev.candidate_event_id: ev.fill_timestamp
        for ev in fill_evs if ev.candidate_event_id and ev.fill_timestamp
    }
    # OCO attempts: same per-candidate count as paper.
    paper_oco_counts: dict[str, int] = {}
    lab_oco_counts: dict[str, int] = {}
    for ev in oco_evs:
        cid = ev.candidate_event_id
        if cid:
            paper_oco_counts[cid] = paper_oco_counts.get(cid, 0) + 1
            lab_oco_counts[cid] = lab_oco_counts.get(cid, 0) + 1
    return {
        "lab_candidates": lab_candidates,
        "lab_decisions": lab_decisions,
        "lab_fills": lab_fills,
        "lab_exits": lab_exits,
        "lab_acks": lab_acks,
        "lab_fills_ts": lab_fills_ts,
        "paper_oco_counts": paper_oco_counts,
        "lab_oco_counts": lab_oco_counts,
    }


def _paper_views(paper: PaperEventImportResult) -> dict:
    """Project the Phase-9 typed paper events down to the Phase-10 paper schemas.

    The Phase-9 comparators are agnostic about the schema dialect — they read
    the typed fields they need (``event_id``, ``symbol``, ``decision``,
    ``avg_fill_price``, etc.). Mapping the Phase-9 records into the existing
    Phase-10 ``Paper*`` schemas reuses the strict-typed surface the rest of
    the suite already covers.
    """
    paper_candidates = [
        PaperCandidate(event_id=str(c.event_id), symbol=str(c.symbol),
                       session_date=SESSION,
                       scan_timestamp=c.scan_timestamp,
                       signal_strength=c.signal_strength)
        for c in paper.events_by_kind["paper_candidate"]
    ]
    paper_decisions = [
        PaperDecision(candidate_event_id=d.candidate_event_id, symbol=str(d.symbol),
                      session_date=SESSION, decision=d.decision, reason=d.reason,
                      decision_timestamp=d.decision_timestamp)
        for d in paper.events_by_kind["paper_decision"]
    ]
    paper_fills = [
        PaperFill(parent_order_id=str(f.parent_order_id),
                  candidate_event_id=f.candidate_event_id, symbol=str(f.symbol),
                  filled_qty=f.filled_qty, avg_fill_price=f.avg_fill_price,
                  fill_timestamp=f.fill_timestamp)
        for f in paper.events_by_kind["paper_parent_fill"]
    ]
    paper_exits = [
        PaperExit(parent_order_id=e.parent_order_id, position_id=e.position_id,
                  candidate_event_id=e.candidate_event_id, symbol=str(e.symbol),
                  exit_reason=e.exit_reason, exit_price=e.exit_price,
                  realized_pnl=e.realized_pnl, exit_timestamp=e.exit_timestamp)
        for e in paper.events_by_kind["paper_position_close"]
    ]
    paper_acks = {
        ev.candidate_event_id: ev.ack_timestamp
        for ev in paper.events_by_kind["paper_parent_ack"]
        if ev.candidate_event_id and ev.ack_timestamp
    }
    paper_fills_ts = {
        ev.candidate_event_id: ev.fill_timestamp
        for ev in paper.events_by_kind["paper_parent_fill"]
        if ev.candidate_event_id and ev.fill_timestamp
    }
    return {
        "paper_candidates": paper_candidates,
        "paper_decisions": paper_decisions,
        "paper_fills": paper_fills,
        "paper_exits": paper_exits,
        "paper_acks": paper_acks,
        "paper_fills_ts": paper_fills_ts,
    }


def test_synthetic_recon_matches_within_tolerance(
    lab_root: Path, tmp_path: Path
) -> None:
    """End-to-end: synthetic paper vs synthetic lab → every comparator passes."""
    paper = _paper_records(lab_root)
    p = _paper_views(paper)
    l = _build_lab_mirror(paper)
    tol = load_reconcile_tolerances()

    emi = emission_jaccard(
        p["paper_candidates"], l["lab_candidates"],
        threshold=tol["emission_jaccard_min"],
    )
    dec = decision_reason_confusion(
        p["paper_decisions"], l["lab_decisions"],
        threshold=tol["decision_reason_match_min"],
    )
    fills = fill_residuals(
        p["paper_fills"], l["lab_fills"],
        price_tolerance_bps=tol["fill_price_tolerance_bps"],
        qty_tolerance_shares=tol["fill_qty_tolerance_shares"],
    )
    latency = fill_latency_residuals(
        p["paper_acks"], p["paper_fills_ts"], l["lab_acks"], l["lab_fills_ts"],
        tolerance_p95_ms=tol["fill_latency_p95_tolerance_ms"],
    )
    oco = oco_attempt_count_diff(l["paper_oco_counts"], l["lab_oco_counts"])
    exits = exit_reason_timing(
        p["paper_exits"], l["lab_exits"],
        timing_tolerance_seconds=tol["exit_timing_tolerance_seconds"],
    )
    pnls = pnl_residuals(
        p["paper_exits"], l["lab_exits"],
        pnl_tolerance_dollars=tol["pnl_tolerance_dollars"],
    )

    # Spot-check each comparator passes individually.
    assert emi.jaccard == 1.0
    assert emi.passes is True
    assert dec.match == 1.0
    assert dec.passes is True
    assert fills.n_flagged == 0
    assert fills.passes is True
    assert latency.passes is True
    assert oco.passes is True
    assert exits.passes is True
    assert pnls.passes is True

    # Report aggregates them and the overall must come back PASSED.
    report = build_phase9_recon_report(
        run_id="recon-2024-09-03",
        session_dates=[SESSION],
        tolerances=tol,
        emission=emi,
        decision_reason=dec,
        fills=fills,
        fill_latency=latency,
        oco_attempts=oco,
        exit_reason_timing=exits,
        pnl=pnls,
    )
    assert report["overall_passed"] is True
    assert report["mismatch_flags"] == []
    # Per-stage pass map: everything True.
    for stage, passed in report["passes_by_stage"].items():
        assert passed is True, f"stage {stage} did not pass: {report['aggregate'][stage]}"

    # Render to disk and re-parse — the JSON survives a roundtrip.
    out_dir = tmp_path / "recon" / "recon-2024-09-03"
    json_path, md_path = render_phase9_recon_report(
        run_id="recon-2024-09-03",
        session_dates=[SESSION],
        tolerances=tol,
        out_dir=out_dir,
        emission=emi, decision_reason=dec, fills=fills,
        fill_latency=latency, oco_attempts=oco,
        exit_reason_timing=exits, pnl=pnls,
    )
    assert json_path.is_file()
    assert md_path.is_file()
    import json
    on_disk = json.loads(json_path.read_text(encoding="utf-8"))
    assert on_disk["overall_passed"] is True
    text = md_path.read_text(encoding="utf-8")
    assert "Paper-vs-Sim Reconciliation Report" in text
    assert "no mismatches above tolerance" in text
