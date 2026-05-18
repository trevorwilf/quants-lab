"""Report must include all sections per §20.1.

The original §20.1 spec called for 17 sections. We added a Walk-forward
optimization section (currently 14) so the weekly report surfaces Optuna
study results inline; that pushed the count to 18.
"""

from __future__ import annotations

import pandas as pd

from bowaka_lab.reports.markdown import SECTION_HEADERS, ReportInputs, build_markdown


def _empty_inputs() -> ReportInputs:
    return ReportInputs(
        run_id="bt_test",
        config_hash="sha256:abc",
        trades=pd.DataFrame(),
        counterfactuals=pd.DataFrame(),
        reconciliation=None,
    )


def test_all_section_headers_present():
    md = build_markdown(_empty_inputs())
    for header in SECTION_HEADERS:
        assert f"## {header}" in md, f"Missing section header: {header}"


def test_report_has_run_id_and_config_hash():
    inputs = _empty_inputs()
    md = build_markdown(inputs)
    assert "bt_test" in md
    assert "sha256:abc" in md


def test_section_count_is_18_after_walkforward_insert():
    assert len(SECTION_HEADERS) == 18
