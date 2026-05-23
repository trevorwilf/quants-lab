"""Phase 9 — comparator flags a deliberately-mismatched fill (50 bps deviation).

Builds the same paper-vs-lab record set as the matched-tolerance test, then
deliberately perturbs ONE lab fill price by 50 bps. The fill-residual
comparator must surface that row as flagged, and the report's
``overall_passed`` must be False with a clear mismatch-flag describing the
fill-residual breach.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.reconcile import (
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


def test_synthetic_recon_flags_intentional_mismatch(lab_root: Path) -> None:
    """One lab fill perturbed by 50 bps → comparator flags it; report fails."""
    paper = import_paper_event_logs(
        lab_root / "tests" / "fixtures" / "paper_logs" / SESSION,
        session_date=SESSION,
    )
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

    # Lab side mirrors paper EXACTLY except the AAA fill is perturbed by 50 bps.
    lab_candidates = [
        LabCandidate(event_id=c.event_id, symbol=c.symbol,
                     session_date=c.session_date,
                     scan_timestamp=c.scan_timestamp,
                     signal_strength=c.signal_strength)
        for c in paper_candidates
    ]
    lab_decisions = [
        LabDecision(candidate_event_id=d.candidate_event_id, symbol=d.symbol,
                    session_date=d.session_date, decision=d.decision,
                    reason=d.reason, decision_timestamp=d.decision_timestamp)
        for d in paper_decisions
    ]
    perturbed_target_cid = (
        "bowaka_v2:2024-09-03:AAA:2024-09-03T13:45:00Z"
    )
    lab_fills: list[LabFill] = []
    for f in paper_fills:
        new_price = f.avg_fill_price
        if (
            f.candidate_event_id == perturbed_target_cid
            and f.avg_fill_price is not None
        ):
            # +50 bps deviation on the AAA fill — well past the 5 bps tolerance.
            new_price = round(f.avg_fill_price * (1.0 + 50.0 / 10_000.0), 4)
        lab_fills.append(LabFill(
            parent_order_id=f.parent_order_id,
            candidate_event_id=f.candidate_event_id,
            symbol=f.symbol, filled_qty=f.filled_qty,
            avg_fill_price=new_price, fill_timestamp=f.fill_timestamp,
        ))
    lab_exits = [
        LabExit(parent_order_id=e.parent_order_id, position_id=e.position_id,
                candidate_event_id=e.candidate_event_id, symbol=e.symbol,
                exit_reason=e.exit_reason, exit_price=e.exit_price,
                realized_pnl=e.realized_pnl, exit_timestamp=e.exit_timestamp)
        for e in paper_exits
    ]
    # Latency mirrors paper (so the latency comparator passes).
    ack_evs = paper.events_by_kind["paper_parent_ack"]
    fill_evs = paper.events_by_kind["paper_parent_fill"]
    paper_acks = {
        ev.candidate_event_id: ev.ack_timestamp
        for ev in ack_evs if ev.candidate_event_id and ev.ack_timestamp
    }
    paper_fills_ts = {
        ev.candidate_event_id: ev.fill_timestamp
        for ev in fill_evs if ev.candidate_event_id and ev.fill_timestamp
    }
    lab_acks = dict(paper_acks)
    lab_fills_ts = dict(paper_fills_ts)

    # OCO counts mirror paper (so the OCO comparator passes).
    oco_evs = paper.events_by_kind["paper_oco_attempt"]
    paper_oco_counts: dict[str, int] = {}
    for ev in oco_evs:
        cid = ev.candidate_event_id
        if cid:
            paper_oco_counts[cid] = paper_oco_counts.get(cid, 0) + 1

    tol = load_reconcile_tolerances()
    emi = emission_jaccard(
        paper_candidates, lab_candidates,
        threshold=tol["emission_jaccard_min"],
    )
    dec = decision_reason_confusion(
        paper_decisions, lab_decisions,
        threshold=tol["decision_reason_match_min"],
    )
    fills = fill_residuals(
        paper_fills, lab_fills,
        price_tolerance_bps=tol["fill_price_tolerance_bps"],
        qty_tolerance_shares=tol["fill_qty_tolerance_shares"],
    )
    latency = fill_latency_residuals(
        paper_acks, paper_fills_ts, lab_acks, lab_fills_ts,
        tolerance_p95_ms=tol["fill_latency_p95_tolerance_ms"],
    )
    oco = oco_attempt_count_diff(paper_oco_counts, dict(paper_oco_counts))
    exits = exit_reason_timing(
        paper_exits, lab_exits,
        timing_tolerance_seconds=tol["exit_timing_tolerance_seconds"],
    )
    pnls = pnl_residuals(
        paper_exits, lab_exits,
        pnl_tolerance_dollars=tol["pnl_tolerance_dollars"],
    )

    # The fill-residual comparator surfaces the perturbed AAA row.
    assert fills.n_flagged >= 1
    assert fills.passes is False
    aaa_rows = [r for r in fills.residuals if r.candidate_event_id == perturbed_target_cid]
    assert aaa_rows, "AAA fill residual row missing"
    assert aaa_rows[0].flagged is True
    # 50 bps deviation should be reflected in the bps residual.
    assert aaa_rows[0].price_delta_bps is not None
    assert abs(aaa_rows[0].price_delta_bps - 50.0) < 0.5  # exact bps with rounding tolerance
    # All other comparators still pass.
    assert emi.passes is True
    assert dec.passes is True
    assert latency.passes is True
    assert oco.passes is True
    assert exits.passes is True
    assert pnls.passes is True

    # Report: overall_passed must be False; a fill-residual mismatch flag is surfaced.
    report = build_phase9_recon_report(
        run_id="recon-mismatch-2024-09-03",
        session_dates=[SESSION],
        tolerances=tol,
        emission=emi, decision_reason=dec, fills=fills,
        fill_latency=latency, oco_attempts=oco,
        exit_reason_timing=exits, pnl=pnls,
    )
    assert report["overall_passed"] is False
    flags_text = " | ".join(report["mismatch_flags"])
    assert "fill residuals" in flags_text
    assert "flagged" in flags_text
    # Sanity: the bps p95 is well above the 5 bps tolerance.
    assert report["aggregate"]["fill_residuals"]["p95_abs_price_delta_bps"] >= 5.0
