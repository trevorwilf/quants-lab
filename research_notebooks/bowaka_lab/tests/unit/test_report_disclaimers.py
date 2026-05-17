"""Phase 8: IEX + paper-reconciliation disclaimers verbatim."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.reports.markdown import IEX_DISCLAIMER, PAPER_DISCLAIMER, ReportInputs, build_markdown


def test_iex_run_includes_iex_disclaimer_verbatim():
    inputs = ReportInputs(run_id="bt", config_hash="sha256:c", data_feed="iex")
    md = build_markdown(inputs)
    assert IEX_DISCLAIMER in md


def test_sip_run_omits_iex_disclaimer():
    inputs = ReportInputs(run_id="bt", config_hash="sha256:c", data_feed="sip")
    md = build_markdown(inputs)
    assert IEX_DISCLAIMER not in md


def test_paper_reconciliation_run_includes_paper_disclaimer():
    rec = pd.DataFrame([{"classification": "candidate_match"}])
    inputs = ReportInputs(run_id="bt", config_hash="sha256:c", data_feed="iex", reconciliation=rec)
    md = build_markdown(inputs)
    assert PAPER_DISCLAIMER in md


def test_no_reconciliation_omits_paper_disclaimer():
    inputs = ReportInputs(run_id="bt", config_hash="sha256:c", data_feed="iex", reconciliation=None)
    md = build_markdown(inputs)
    assert PAPER_DISCLAIMER not in md
