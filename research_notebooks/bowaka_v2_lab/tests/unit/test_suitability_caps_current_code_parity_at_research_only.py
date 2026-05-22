"""``current_code_parity`` is capped at ``research_only`` regardless of feed.

Realism remediation 2 Phase 1, Task 4 (audit §P0-001 / §P0-011). A
``current_code_parity`` run reproduces the live code warts and all — it is valid
only as paper-reconciliation evidence, never a parameter recommendation, so the
suitability tier is mechanically capped at ``research_only`` even on a SIP feed.
The pre-existing ``feed: iex`` cap is verified alongside.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.suitability import (
    decide_suitability,
    tier_for_simulation_contract,
)


def _run_dir(tmp_path: Path, *, feed: str, mode: str) -> Path:
    rd = tmp_path / f"run_{feed}_{mode}"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"feed": feed, "n_trades": 100}))
    (rd / "run_manifest.json").write_text(
        json.dumps({"simulation": {"mode": mode}})
    )
    return rd


def test_contract_cap_for_current_code_parity_is_research_only() -> None:
    """The contract-only cap for current_code_parity is research_only."""
    assert tier_for_simulation_contract("current_code_parity") == "research_only"


def test_current_code_parity_sip_capped_at_research_only(tmp_path: Path) -> None:
    """Even on a SIP feed, a current_code_parity run caps at research_only."""
    rd = _run_dir(tmp_path, feed="sip", mode="current_code_parity")
    assert decide_suitability(rd, checklist_results=None) == "research_only"


def test_current_code_parity_iex_capped_at_research_only(tmp_path: Path) -> None:
    """current_code_parity on IEX is research_only (both caps agree)."""
    rd = _run_dir(tmp_path, feed="iex", mode="current_code_parity")
    assert decide_suitability(rd, checklist_results=None) == "research_only"


def test_iex_feed_capped_at_research_only(tmp_path: Path) -> None:
    """The pre-existing feed: iex cap still holds (intended_realism + IEX)."""
    rd = _run_dir(tmp_path, feed="iex", mode="intended_realism")
    assert decide_suitability(rd, checklist_results=None) == "research_only"


def test_intended_realism_sip_not_capped_to_research_only(tmp_path: Path) -> None:
    """A SIP intended_realism run is NOT capped at research_only by contract.

    (It still caps at backtesting_only for lack of holdout/recon evidence — the
    point here is that the current_code_parity / IEX research_only cap does not
    fire for SIP + intended_realism.)
    """
    rd = _run_dir(tmp_path, feed="sip", mode="intended_realism")
    assert decide_suitability(rd, checklist_results=None) == "backtesting_only"
