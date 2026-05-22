"""Suitability tiers per [Report §9.11].

HARD CAP per [Report §1.2, §21]: any of these conditions caps the tier at
``backtesting_only`` or below:
- ``feed == "iex"``      → ``research_only``
- no walk-forward holdout evidence in run_dir
- no paper-recon residual artifact in run_dir

This is mechanical: the promotion code in this lab can NEVER claim higher than
``backtesting_only`` because SIP walk-forward + paper-vs-sim reconciliation are
explicit prerequisites for higher tiers and the lab does not produce both.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

SUITABILITY_TIERS = ("research_only", "backtesting_only", "paper_candidate", "live_candidate")
SuitabilityTier = Literal["research_only", "backtesting_only", "paper_candidate", "live_candidate"]

#: The three simulation contracts a run/study can declare (realism remediation 2
#: Phase 0). The contract is exactly ``simulation.mode`` — it names *which
#: strategy* the simulator reproduced.
SIMULATION_CONTRACTS = ("current_code_parity", "intended_realism", "smoke_fixture")
SimulationContract = Literal["current_code_parity", "intended_realism", "smoke_fixture"]

#: Mechanical tier *cap* per simulation contract (realism remediation 2 Phase 0,
#: audit §P0-001 / §P0-011). A run can never be suitable above this cap from the
#: contract alone:
#:
#: - ``smoke_fixture``       — synthetic plumbing data; never research-grade.
#: - ``current_code_parity`` — reproduces the live code *warts and all*; valid
#:   only as paper-reconciliation evidence, not parameter recommendation.
#: - ``intended_realism``    — the only contract that *can* support a higher
#:   tier, and only with SIP data + real quotes + adjusted baselines + paper
#:   reconciliation (gated elsewhere). On its own it caps at ``backtesting_only``.
_CONTRACT_TIER_CAP: dict[str, str] = {
    "smoke_fixture": "research_only",
    "current_code_parity": "research_only",
    "intended_realism": "backtesting_only",
}


def simulation_contract_of(cfg_or_mode: object) -> str:
    """Resolve the simulation contract from a config dict or a bare mode string.

    The contract IS ``simulation.mode``. Accepts the full lab-config dict, the
    ``simulation`` sub-dict, or the mode string itself. An unrecognised value
    raises ``ValueError`` — a run artifact must declare a known contract.
    """
    mode: object
    if isinstance(cfg_or_mode, str):
        mode = cfg_or_mode
    elif isinstance(cfg_or_mode, dict):
        sim = cfg_or_mode.get("simulation", cfg_or_mode)
        mode = sim.get("mode") if isinstance(sim, dict) else None
    else:
        mode = None
    if mode not in SIMULATION_CONTRACTS:
        raise ValueError(
            f"unknown simulation contract {mode!r}; expected one of {SIMULATION_CONTRACTS}"
        )
    return str(mode)


def tier_for_simulation_contract(simulation_contract: str) -> str:
    """Mechanical tier cap for a simulation contract (realism remediation 2 Phase 0).

    This is the *contract-only* cap — the audit's mechanical mapping (IEX and
    ``current_code_parity`` capped at ``research_only``). The full
    :func:`decide_suitability` verdict applies additional caps (feed, missing
    evidence) and never exceeds this one.
    """
    if simulation_contract not in _CONTRACT_TIER_CAP:
        raise ValueError(
            f"unknown simulation contract {simulation_contract!r}; "
            f"expected one of {SIMULATION_CONTRACTS}"
        )
    return _CONTRACT_TIER_CAP[simulation_contract]


def _summary(run_dir: Path) -> dict:
    p = Path(run_dir) / "summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _has_walkforward_holdout_artifact(run_dir: Path) -> bool:
    """Check for a walk-forward holdout evidence file in run_dir or sibling optuna dir."""
    rd = Path(run_dir)
    for cand in (rd / "walkforward_holdout.json", rd.parent / "optuna" / "walkforward_holdout.json"):
        if cand.is_file():
            return True
    return False


def _has_paper_recon_artifact(run_dir: Path) -> bool:
    rd = Path(run_dir)
    for cand in (
        rd / "reconciliation_report.md",
        rd / "slippage_residuals.parquet",
        rd.parent / "reconcile" / "reconciliation_report.md",
    ):
        if cand.is_file():
            return True
    return False


def _run_manifest(run_dir: Path) -> dict:
    p = Path(run_dir) / "run_manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def decide_suitability(run_dir: Path, checklist_results: dict | None = None) -> SuitabilityTier:
    """Mechanical suitability decision.

    Returns the highest tier consistent with available evidence, subject to the
    documented hard caps. Never returns ``paper_candidate`` or ``live_candidate``
    from this lab's evidence alone (Report §1.2 / §21).
    """
    rd = Path(run_dir)
    summary = _summary(rd)
    feed = summary.get("feed", "iex")

    # Check for blocking gate failures (anything that's "fail" in the checklist).
    if checklist_results:
        for item_id, (status, _ev) in checklist_results.items():
            if status == "fail":
                return "research_only"

    # Simulation-contract cap (realism remediation 2 Phase 0, audit §P0-001/-011):
    # a current_code_parity / smoke_fixture run can never exceed research_only.
    manifest = _run_manifest(rd)
    sim_mode = (manifest.get("simulation") or {}).get("mode")
    if sim_mode in _CONTRACT_TIER_CAP and _CONTRACT_TIER_CAP[sim_mode] == "research_only":
        return "research_only"

    # IEX → research_only hard cap.
    if feed == "iex":
        return "research_only"

    # Without walk-forward holdout evidence → backtesting_only at best.
    has_wf = _has_walkforward_holdout_artifact(rd)
    has_recon = _has_paper_recon_artifact(rd)
    if not has_wf or not has_recon:
        return "backtesting_only"

    # Even with both evidence types, this lab's mechanical verdict caps at
    # backtesting_only — promoting requires an out-of-band operator decision per §21.
    return "backtesting_only"
