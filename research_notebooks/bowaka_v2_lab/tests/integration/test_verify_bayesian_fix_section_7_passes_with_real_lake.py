"""End-to-end gate (hotfix 2026-05-29): verify-bayesian-fix Section 7 reads PASS
against the operator's real lake — NOT DEFERRED (the lake-root false-positive is
gone) and NOT FAIL.

Opt-in: this runs a real 3-trial walk-forward short-run against the workstation
config (the full universe), which is a multi-minute-to-hours job. It is guarded
behind ``BOWAKA_RUN_REAL_LAKE_SECTION7=1`` so it never runs inside the routine
``make test-all`` (where the real lake is present and the study would otherwise
hang the suite). The operator sets the flag to run the decisive end-to-end gate.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from bowaka_common.marketdata.layout import bars_timeframe_root
from bowaka_common.marketdata.store import resolve_market_data_root

pytestmark = pytest.mark.integration


def _real_split_adjusted_lake_present() -> bool:
    root = resolve_market_data_root(None, create=False)
    split = bars_timeframe_root(
        root, "1d", vendor="alpaca", feed="iex", adjustment="split_adjusted",
    )
    return split.is_dir() and any(split.glob("symbol=*"))


@pytest.mark.timeout(7200)
@pytest.mark.skipif(
    os.environ.get("BOWAKA_RUN_REAL_LAKE_SECTION7") != "1",
    reason="opt-in: runs a real workstation short-run (set "
           "BOWAKA_RUN_REAL_LAKE_SECTION7=1 on a box with the lake + postgres)",
)
def test_section_7_passes_with_real_lake(tmp_path: Path) -> None:
    if not _real_split_adjusted_lake_present():
        pytest.skip("no split_adjusted IEX daily partition on the default lake")

    from bowaka_v2_lab.devtools.verify_bayesian_fix import main as verify_main

    report = tmp_path / "report.md"
    # Full run (Section 7 short-run included) against the workstation config.
    verify_main(["--n-trials", "3", "--out", str(report)])

    text = report.read_text(encoding="utf-8")
    # Isolate the Section 7 block.
    start = text.index("## Section 7")
    end = text.index("## Section 8", start) if "## Section 8" in text[start:] else len(text)
    section7 = text[start:end]
    assert "| FAIL |" not in section7, section7
    assert "DEFERRED" not in section7, (
        "Section 7 still DEFERRED — the lake-root false-positive carve-out is "
        "still firing; the hotfix did not land:\n" + section7
    )
    assert "PASS" in section7, section7
