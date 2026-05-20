"""feed=iex forces tier=research_only."""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.suitability import decide_suitability


def test_iex_caps_to_research_only(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"feed": "iex", "n_trades": 100}))
    tier = decide_suitability(rd, checklist_results=None)
    assert tier == "research_only"


def test_sip_not_capped_by_feed(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"feed": "sip", "n_trades": 100}))
    # Without holdout/recon artifacts, capped at backtesting_only.
    tier = decide_suitability(rd, checklist_results=None)
    assert tier == "backtesting_only"
