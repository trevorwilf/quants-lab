"""Phase 1: confirm Section 5 of the report renders the funnel correctly."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.reports.markdown import ReportInputs, build_markdown


_FUNNEL = {
    "universe_with_features": 11_119,
    "passed_universe_gates": 1_070,
    "candidates": 17,
    "rejected_by_signal_gates": 1_053,
    "excluded_by_instrument_class": 2,
    "per_session": {},
}


def test_section_5_funnel_renders_actual_values_when_inputs_populated():
    inputs = ReportInputs(
        run_id="bt_test",
        config_hash="sha256:abc",
        prefilter_funnel=_FUNNEL,
    )
    md = build_markdown(inputs)
    # The values must appear as integers in the Section 5 table.
    for stage_count in ("11119", "1070", "17", "1053", "2"):
        assert stage_count in md, f"missing funnel value {stage_count!r} in rendered markdown"


def test_section_5_funnel_renders_zeros_when_inputs_none():
    inputs = ReportInputs(run_id="bt_test", config_hash="sha256:abc", prefilter_funnel=None)
    md = build_markdown(inputs)
    # Back-compat: with no funnel data, all five stages render zero.
    section_5_header = "## 5. Prefilter funnel"
    assert section_5_header in md
    # Slice the markdown to just Section 5 and confirm a zero count is present.
    s5_start = md.index(section_5_header)
    s5 = md[s5_start : s5_start + 800]
    assert "0" in s5


def test_section_5_back_compat_with_prefilter_metadata_dict():
    """If a caller still uses the old ``prefilter_metadata`` field (n_ prefixed),
    Section 5 reads it. This preserves Phase-8 behavior."""
    metadata = {
        "n_universe_with_features": 500,
        "n_passed_universe_gates": 50,
        "n_candidates": 5,
        "n_rejected_by_signal_gates": 45,
        "n_excluded_by_instrument_class": 0,
    }
    inputs = ReportInputs(run_id="bt", config_hash="x", prefilter_metadata=metadata)
    md = build_markdown(inputs)
    for v in ("500", "50", "5", "45"):
        assert v in md
