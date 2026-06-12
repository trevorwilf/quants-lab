"""Suitability tiers per [Report §9.11].

HARD CAP per [Report §1.2, §21]: any of these conditions caps the tier at
``backtesting_only`` or below:
- ``feed == "iex"``      → ``research_only``
- no walk-forward holdout evidence in run_dir
- no paper-recon residual artifact in run_dir

This is mechanical: the promotion code in this lab can NEVER claim higher than
``backtesting_only`` because SIP walk-forward + paper-vs-sim reconciliation are
explicit prerequisites for higher tiers and the lab does not produce both.

Realism remediation 2 Phase 10 (audit §P1-010): IEX is a partial-tape feed.
Any artifact with ``feed: iex`` therefore carries TWO labels — the existing
``suitability_tier: research_only`` and a new ``feed_caveat:
partial_tape_features`` field — to make it unambiguous that RVOL_so_far,
projected_full_day_rvol, range_expansion_so_far and ADV on IEX are IEX-
specific and not portable to SIP. Any attempt to set
``suitability_tier`` above ``research_only`` on a ``feed: iex`` study now
raises :class:`IEXPromotionBlocked`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Mapping, Optional

SUITABILITY_TIERS = ("research_only", "backtesting_only", "paper_candidate", "live_candidate")
SuitabilityTier = Literal["research_only", "backtesting_only", "paper_candidate", "live_candidate"]

#: Ordered tiers — index reflects rank (research_only = 0; live_candidate = 3).
#: Used by :func:`assert_not_above_research_only_for_iex` to refuse any IEX
#: promotion above ``research_only``.
_TIER_RANK: dict[str, int] = {
    "research_only": 0,
    "backtesting_only": 1,
    "paper_candidate": 2,
    "live_candidate": 3,
}

#: Mechanical caveat label attached to every IEX artifact (audit §P1-010).
#: The label is consumed by :func:`feed_caveat_for` and surfaced in the run
#: report's IEX banner; downstream tooling can filter on it.
FEED_CAVEAT_PARTIAL_TAPE = "partial_tape_features"


class IEXPromotionBlocked(RuntimeError):
    """Raised when promotion code tries to advance a ``feed: iex`` artifact above
    ``research_only`` (realism remediation 2 Phase 10 / audit §P1-010).

    IEX is partial-tape; RVOL / range-expansion / ADV computed on IEX are NOT
    consolidated. Promoting an IEX result past ``research_only`` would
    silently treat IEX-specific parameters as SIP-portable — exactly the
    failure mode the audit calls out. The block is mechanical: code that
    raises this exception has tried to do something the lab explicitly
    forbids.
    """


def feed_caveat_for(feed: Optional[str]) -> Optional[str]:
    """Return the caveat label for ``feed`` (or ``None`` when there is no caveat).

    Today only IEX carries a caveat (``partial_tape_features``); SIP and other
    feeds return ``None``. Realism remediation 2 Phase 10 (audit §P1-010).
    """
    if str(feed or "").lower() == "iex":
        return FEED_CAVEAT_PARTIAL_TAPE
    return None


def assert_not_above_research_only_for_iex(
    *,
    feed: Optional[str],
    proposed_tier: str,
    context: str = "",
) -> None:
    """Refuse a ``feed: iex`` artifact whose proposed tier exceeds ``research_only``.

    Raises :class:`IEXPromotionBlocked` when ``feed == "iex"`` and
    ``proposed_tier`` ranks above ``research_only``. ``context`` is an
    optional human-readable label for the artifact (e.g. the study name) so
    the exception message points the operator at the right run.

    Used by every code path that *writes* a tier onto an IEX artifact —
    `decide_suitability` (this module), `OptunaStudy.mark_promotion_eligible`,
    and the walk-forward runner. The cap rule itself (Phase 1) still applies;
    this assertion is the explicit refusal that turns an accidental override
    into an immediate, well-labeled error.
    """
    if str(feed or "").lower() != "iex":
        return
    if proposed_tier not in _TIER_RANK:
        # An unknown tier name is not an IEX-specific defect; let the caller
        # decide how to handle it. Return without raising so callers can use
        # this gate uniformly without pre-validating the tier string.
        return
    if _TIER_RANK[proposed_tier] > _TIER_RANK["research_only"]:
        suffix = f" ({context})" if context else ""
        raise IEXPromotionBlocked(
            f"refusing to set suitability_tier={proposed_tier!r} on a feed='iex' "
            f"artifact{suffix}: IEX is partial-tape (RVOL / range-expansion / ADV "
            f"are IEX-specific and NOT consolidated). The IEX cap is "
            f"'research_only'; rerun on the SIP feed and produce paper-recon "
            f"evidence to advance. See docs/audits/2026-05-22_realism_audit.md §P1-010."
        )

#: The three simulation contracts a run/study can declare (realism remediation 2
#: Phase 0). The contract is exactly ``simulation.mode`` — it names *which
#: strategy* the simulator reproduced.
SIMULATION_CONTRACTS = (
    "current_code_parity", "intended_realism", "fast_realism", "smoke_fixture",
)
SimulationContract = Literal[
    "current_code_parity", "intended_realism", "fast_realism", "smoke_fixture",
]

#: Mechanical tier *cap* per simulation contract (realism remediation 2 Phase 0,
#: audit §P0-001 / §P0-011). A run can never be suitable above this cap from the
#: contract alone:
#:
#: - ``smoke_fixture``       — synthetic plumbing data; never research-grade.
#: - ``current_code_parity`` — reproduces the live code *warts and all*; valid
#:   only as paper-reconciliation evidence, not parameter recommendation.
#: - ``fast_realism``        — §10i Path 4 search mode: honest (participation/
#:   depth) fills but a synthetic zero-spread quote optimism, so its results are
#:   SEARCH / screening evidence only — caps at ``research_only``. Promote a
#:   finalist by re-validating it under ``intended_realism``.
#: - ``intended_realism``    — the only contract that *can* support a higher
#:   tier, and only with SIP data + real quotes + adjusted baselines + paper
#:   reconciliation (gated elsewhere). On its own it caps at ``backtesting_only``.
_CONTRACT_TIER_CAP: dict[str, str] = {
    "smoke_fixture": "research_only",
    "current_code_parity": "research_only",
    "fast_realism": "research_only",
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

    # PB.6 — a run that consumed the REAL trade tape (fill_model="tape_replay" on
    # entries or exits) uses the honest-fill model that is NOT yet validated
    # against the tape (PB.5). Cap it at research_only regardless of mode/feed
    # until that validation lands and the model is deliberately promoted into IR.
    if (manifest.get("fill_model") or {}).get("consumes_trade_tape"):
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


def build_suitability_artifact(
    *,
    feed: Optional[str],
    simulation_contract: Optional[str] = None,
    tier: Optional[str] = None,
) -> dict[str, object]:
    """Build the mechanical suitability + feed-caveat envelope for an artifact.

    Returns a dict carrying ``suitability_tier``, ``feed``, and (when applicable)
    ``feed_caveat: 'partial_tape_features'``. Realism remediation 2 Phase 10
    (audit §P1-010): every run / study artifact carries this envelope so
    downstream consumers (reports, paper-recon, promotion) can read the IEX
    caveat without re-deriving it.

    Raises :class:`IEXPromotionBlocked` when the caller *explicitly* passes a
    ``tier`` above ``research_only`` on a ``feed: iex`` artifact. A
    contract-default tier above ``research_only`` (e.g. the ``intended_realism``
    default of ``backtesting_only``) is silently clamped to ``research_only``
    on IEX — that is the mechanical IEX cap, not a caller mistake.
    """
    out: dict[str, object] = {"feed": feed}
    is_iex = str(feed or "").lower() == "iex"
    # An explicit caller-supplied tier above research_only on IEX is the only
    # case that raises: the caller is asking for something the lab forbids.
    if is_iex and tier is not None:
        assert_not_above_research_only_for_iex(
            feed=feed, proposed_tier=str(tier),
            context=f"simulation_contract={simulation_contract!r}",
        )
    # Resolve the tier: explicit > contract default > research_only.
    if tier is not None:
        resolved_tier = str(tier)
    elif simulation_contract is not None and simulation_contract in _CONTRACT_TIER_CAP:
        resolved_tier = _CONTRACT_TIER_CAP[simulation_contract]
    else:
        resolved_tier = "research_only"
    # IEX cap — research_only mechanically. A contract default above the cap is
    # clamped (no raise); a caller's explicit override raised above.
    if is_iex:
        resolved_tier = "research_only"
    out["suitability_tier"] = resolved_tier
    caveat = feed_caveat_for(feed)
    if caveat is not None:
        out["feed_caveat"] = caveat
    if simulation_contract is not None:
        out["simulation_contract"] = simulation_contract
    return out
