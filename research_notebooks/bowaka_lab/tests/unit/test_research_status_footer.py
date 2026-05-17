"""Phase 8: research-grade flag triggers under each documented condition."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.reports.markdown import ReportInputs, build_markdown, research_status_flags


def test_iex_feed_flag():
    flags = research_status_flags(ReportInputs(run_id="bt", config_hash="sha256:c", data_feed="iex"))
    assert "iex_feed_exploratory" in flags


def test_current_universe_flag():
    flags = research_status_flags(ReportInputs(run_id="bt", config_hash="sha256:c", universe_mode="alpaca_current_assets"))
    assert "current_universe_survivorship_biased" in flags


def test_walk_forward_missing_flag():
    flags = research_status_flags(ReportInputs(run_id="bt", config_hash="sha256:c", has_walk_forward=False))
    assert "walk_forward_not_run" in flags


def test_no_flag_when_walk_forward_done_and_sip_and_point_in_time():
    flags = research_status_flags(
        ReportInputs(
            run_id="bt",
            config_hash="sha256:c",
            data_feed="sip",
            universe_mode="point_in_time",
            has_walk_forward=True,
        )
    )
    assert flags == []


def test_implementation_mismatch_flag_when_unresolved():
    rec = pd.DataFrame([{"classification": "implementation_mismatch"}])
    flags = research_status_flags(
        ReportInputs(
            run_id="bt",
            config_hash="sha256:c",
            data_feed="sip",
            universe_mode="point_in_time",
            has_walk_forward=True,
            reconciliation=rec,
        )
    )
    assert "paper_implementation_mismatch_unresolved" in flags


def test_research_grade_footer_present_when_flags_present():
    md = build_markdown(ReportInputs(run_id="bt", config_hash="sha256:c", data_feed="iex"))
    assert "research-grade exploratory evidence" in md


def test_paper_validation_candidate_when_all_clear():
    md = build_markdown(
        ReportInputs(
            run_id="bt",
            config_hash="sha256:c",
            data_feed="sip",
            universe_mode="point_in_time",
            has_walk_forward=True,
        )
    )
    assert "paper_validation_candidate" in md
