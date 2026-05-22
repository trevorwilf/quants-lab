"""Phase 10 — the realism reconciliation report aggregates rows correctly.

Drives ``build_reconcile_report`` / ``render_realism_reconciliation_report``
with hand-built :class:`ReconcileRow` records so the per-stage counts, the
systematic-bias detection, the residual distributions and the calibration
suggestions are all exercised without a full lab run.
"""
from __future__ import annotations

from bowaka_v2_lab.reconcile.report import (
    build_reconcile_report,
    render_realism_reconciliation_report,
)
from bowaka_v2_lab.reconcile.schemas import (
    LabDecision,
    PaperDecision,
    ReconcileRow,
)


def _row(cid: str, presence: str, **kw) -> ReconcileRow:
    return ReconcileRow(candidate_event_id=cid, symbol="AAA", presence=presence, **kw)


def test_stage_counts_aggregated() -> None:
    rows = [
        _row("c1", "both", decision_reason_match=True, fill_price_delta_bps=0.0),
        _row("c2", "both", decision_reason_match=False, fill_price_delta_bps=5.0),
        _row("c3", "paper_only"),
        _row("c4", "lab_only"),
    ]
    report = build_reconcile_report("2024-09-04", rows)
    assert report.n_both == 2
    assert report.n_paper_only == 1
    assert report.n_lab_only == 1
    dec = report.stage_counts["decision_reason"]
    assert dec == {"comparable": 2, "matched": 1, "mismatched": 1}
    fill = report.stage_counts["fill"]
    assert fill == {"comparable": 2, "matched": 1, "mismatched": 1}


def test_systematic_bias_lab_emits_more() -> None:
    """More lab-only than paper-only candidates -> a 'lab emits more' bias."""
    rows = [
        _row("c1", "lab_only"),
        _row("c2", "lab_only"),
        _row("c3", "lab_only"),
        _row("c4", "paper_only"),
    ]
    report = build_reconcile_report("2024-09-04", rows)
    assert any("lab emits more" in b for b in report.systematic_biases)


def test_systematic_bias_lab_overfills() -> None:
    """A positive mean fill-qty delta -> a 'lab over-fills' bias."""
    rows = [
        _row("c1", "both", fill_qty_delta=2.0),
        _row("c2", "both", fill_qty_delta=4.0),
    ]
    report = build_reconcile_report("2024-09-04", rows)
    assert any("over-fill" in b for b in report.systematic_biases)


def test_systematic_bias_paper_rejects_more() -> None:
    """Paper rejects more candidates than the lab -> that bias is surfaced."""
    rows = [
        _row(
            "c1", "both",
            paper_decision=PaperDecision(symbol="AAA", decision="rejected", reason="spread_too_wide"),
            lab_decision=LabDecision(symbol="AAA", decision="accepted", reason="all_gates_passed"),
            decision_reason_match=False,
        ),
        _row(
            "c2", "both",
            paper_decision=PaperDecision(symbol="AAA", decision="rejected", reason="adv_cap"),
            lab_decision=LabDecision(symbol="AAA", decision="accepted", reason="all_gates_passed"),
            decision_reason_match=False,
        ),
    ]
    report = build_reconcile_report("2024-09-04", rows)
    assert any("paper rejects more" in b for b in report.systematic_biases)


def test_fill_price_bias_drives_calibration_suggestion() -> None:
    """A consistent fill-price bias yields a numeric calibration suggestion."""
    rows = [
        _row("c1", "both", fill_price_delta_bps=8.0),
        _row("c2", "both", fill_price_delta_bps=12.0),
    ]
    report = build_reconcile_report("2024-09-04", rows)
    dist = report.residual_distributions["fill_price_delta_bps"]
    assert dist["n"] == 2
    assert dist["mean"] == 10.0
    # The suggestion proposes moving the model the other way (negative bps).
    assert any("bps" in s for s in report.calibration_suggestions)
    assert any("-10" in s for s in report.calibration_suggestions)


def test_scaffolding_only_report_notes_missing_logs() -> None:
    report = build_reconcile_report("2024-09-04", [], scaffolding_only=True, note="no logs")
    assert report.scaffolding_only is True
    assert any("no paper logs" in s for s in report.calibration_suggestions)


def test_render_writes_md_and_json(tmp_path) -> None:
    rows = [_row("c1", "both", decision_reason_match=True)]
    report = build_reconcile_report("2024-09-04", rows)
    md, json_dict = render_realism_reconciliation_report(report, out_dir=tmp_path)
    assert (tmp_path / "reconciliation_report.md").is_file()
    assert (tmp_path / "reconciliation_report.json").is_file()
    assert json_dict["session_date"] == "2024-09-04"
    assert "Residual Distributions" in md
