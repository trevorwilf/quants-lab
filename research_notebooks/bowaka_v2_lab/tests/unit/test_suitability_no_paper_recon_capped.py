"""No paper-recon residual artifact → tier ≤ backtesting_only."""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.suitability import decide_suitability


def test_no_paper_recon_caps_to_backtesting_only(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"feed": "sip", "n_trades": 100}))
    (rd / "walkforward_holdout.json").write_text("{}")
    tier = decide_suitability(rd, checklist_results=None)
    assert tier == "backtesting_only"


def test_both_artifacts_still_caps_to_backtesting_only(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"feed": "sip", "n_trades": 100}))
    (rd / "walkforward_holdout.json").write_text("{}")
    (rd / "reconciliation_report.md").write_text("# recon\n")
    # Even with both evidence types, this lab caps at backtesting_only (Report §21).
    tier = decide_suitability(rd, checklist_results=None)
    assert tier == "backtesting_only"
