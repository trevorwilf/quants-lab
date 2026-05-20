"""No walk-forward holdout artifact → tier ≤ backtesting_only."""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.suitability import decide_suitability


def test_no_holdout_caps_to_backtesting_only(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"feed": "sip", "n_trades": 100}))
    # Provide a paper recon artifact but NOT a walkforward holdout artifact.
    (rd / "reconciliation_report.md").write_text("# recon\n")
    tier = decide_suitability(rd, checklist_results=None)
    assert tier == "backtesting_only"
