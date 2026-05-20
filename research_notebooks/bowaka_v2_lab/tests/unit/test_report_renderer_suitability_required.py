"""render_run_report raises if suitability tier not set."""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.reports.render_run_report import SUITABILITY_TIERS, render_run_report


def test_invalid_suitability_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="suitability must be one of"):
        render_run_report(tmp_path, suitability="totally_not_a_tier")


@pytest.mark.parametrize("tier", SUITABILITY_TIERS)
def test_each_canonical_tier_accepted(tmp_path: Path, tier: str) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    out = render_run_report(rd, suitability=tier)
    assert tier in out
