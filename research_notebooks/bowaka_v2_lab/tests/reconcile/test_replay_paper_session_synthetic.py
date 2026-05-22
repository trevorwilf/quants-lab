"""Phase 10 — replay the frozen synthetic paper session against the lab.

Exercises the whole reconciliation path end-to-end: load the synthetic
paper-log fixture, run the lab in ``current_code_parity`` mode over a tiny
synthetic lake for the same session, join the records side-by-side and render
the realism reconciliation report. No real paper data, no network.
"""
from __future__ import annotations

from bowaka_v2_lab.reconcile.replay import replay_paper_session
from bowaka_v2_lab.reconcile.report import (
    build_reconcile_report,
    render_realism_reconciliation_report,
)

from .conftest import PAPER_LOGS_SYNTHETIC, SYNTHETIC_SESSION

# These tests run against the FROZEN SYNTHETIC paper-log fixture — they need no
# real paper logs, so they carry no ``live_paper`` marker and run under the
# default ``-m "not live_paper"`` selection.


def test_replay_runs_end_to_end(parity_lake_config, tmp_path) -> None:
    """The replay path produces side-by-side rows keyed by candidate_event_id."""
    result = replay_paper_session(
        SYNTHETIC_SESSION, PAPER_LOGS_SYNTHETIC, parity_lake_config,
        run_dir=tmp_path / "lab_run",
    )
    # The lab ran and the synthetic paper logs were loaded -> a real recon.
    assert result.scaffolding_only is False
    assert result.note is None
    assert result.lab_run_dir is not None
    # Synthetic fixture has 3 paper candidates; the lab emits one per symbol.
    assert result.n_paper_candidates == 3
    assert result.n_lab_candidates >= 1
    assert len(result.rows) >= 3
    # Every row carries a candidate id and a valid presence bucket.
    for row in result.rows:
        assert row.candidate_event_id
        assert row.presence in ("both", "paper_only", "lab_only")


def test_replay_rows_keyed_unique_by_candidate(parity_lake_config, tmp_path) -> None:
    """Each candidate_event_id appears in exactly one reconcile row."""
    result = replay_paper_session(
        SYNTHETIC_SESSION, PAPER_LOGS_SYNTHETIC, parity_lake_config,
        run_dir=tmp_path / "lab_run",
    )
    ids = [r.candidate_event_id for r in result.rows]
    assert len(ids) == len(set(ids)), f"duplicate candidate ids: {ids}"


def test_replay_both_bucket_overlap(parity_lake_config, tmp_path) -> None:
    """The synthetic fixture's AAA/BBB candidates overlap the lab's -> 'both'.

    The fixture stamps AAA/BBB candidates at the lab's first scan timestamp,
    so those two candidates land in the 'both' bucket and CCC (lab never
    scans it) lands in 'paper_only'.
    """
    result = replay_paper_session(
        SYNTHETIC_SESSION, PAPER_LOGS_SYNTHETIC, parity_lake_config,
        run_dir=tmp_path / "lab_run",
    )
    both = {r.candidate_event_id for r in result.rows if r.presence == "both"}
    paper_only = {r.candidate_event_id for r in result.rows if r.presence == "paper_only"}
    assert "bowaka_v2:2024-09-04:AAA:2024-09-04T13:45:00Z" in both
    assert "bowaka_v2:2024-09-04:BBB:2024-09-04T13:45:00Z" in both
    # CCC is in the paper logs but the lab never produces it.
    assert "bowaka_v2:2024-09-04:CCC:2024-09-04T14:30:00Z" in paper_only


def test_replay_decision_and_fill_comparators_populated(parity_lake_config, tmp_path) -> None:
    """For 'both' rows the decision / fill comparators are computed."""
    result = replay_paper_session(
        SYNTHETIC_SESSION, PAPER_LOGS_SYNTHETIC, parity_lake_config,
        run_dir=tmp_path / "lab_run",
    )
    by_id = {r.candidate_event_id: r for r in result.rows}
    aaa = by_id["bowaka_v2:2024-09-04:AAA:2024-09-04T13:45:00Z"]
    bbb = by_id["bowaka_v2:2024-09-04:BBB:2024-09-04T13:45:00Z"]
    # AAA: paper accepted, lab accepted -> decision-reason match True.
    assert aaa.decision_reason_match is True
    # BBB: paper rejected/spread_too_wide, lab accepted -> mismatch.
    assert bbb.decision_reason_match is False
    # AAA fill landed on both sides -> a signed bps delta is computed.
    assert aaa.fill_price_delta_bps is not None
    # AAA order qty differs (paper 100 vs lab 98) -> a non-None size delta.
    assert aaa.order_size_delta is not None


def test_replay_report_renders_markdown_and_json(parity_lake_config, tmp_path) -> None:
    """build + render the realism reconciliation report from the replay rows."""
    result = replay_paper_session(
        SYNTHETIC_SESSION, PAPER_LOGS_SYNTHETIC, parity_lake_config,
        run_dir=tmp_path / "lab_run",
    )
    report = build_reconcile_report(
        result.session_date, result.rows,
        scaffolding_only=result.scaffolding_only, note=result.note,
    )
    out_dir = tmp_path / "recon_out"
    md, json_dict = render_realism_reconciliation_report(report, out_dir=out_dir)

    assert "Paper-vs-Lab Reconciliation Report" in md
    assert "## Stage Match Counts" in md
    assert "## Systematic Biases" in md
    assert "## Suggested Calibration Adjustments" in md
    assert (out_dir / "reconciliation_report.md").is_file()
    assert (out_dir / "reconciliation_report.json").is_file()
    # JSON carries the per-stage counts.
    assert "stage_counts" in json_dict
    assert json_dict["session_date"] == SYNTHETIC_SESSION.isoformat()
    assert json_dict["stage_counts"]["candidate_set"]["paper_only"] >= 1
