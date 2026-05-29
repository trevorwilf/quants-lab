"""End-to-end SIP cutover smoke (audit 2026-05-29 §9 Phase 7).

Exercises the full SIP cutover gate surface against the committed synthetic-SIP
fixture, driven by the smoke config — so when real SIP data lands the cutover is
a config flip, not a debugging session. The assertions cover the cutover-CRITICAL
plumbing (the gates that would wall a real migration):

  - intended_realism + sip full-fold preflight passes (daily split_adjusted
    partition + NBBO quote coverage + minute coverage + PIT universe),
  - the NBBO gate hard-fails when quotes are absent,
  - the halt-feed reader picks up the seeded LULD event,
  - the IEX-vs-SIP feed-divergence report produces data,
  - promotion evidence under feed=sip: reviewable + parameter-recommendation
    allowed, NO IEX_PARTIAL_TAPE cap, paper still blocked (no reconciliation).

The 3-trial objective richness is data-dependent (synthetic bars need not find
alpha) and is NOT the cutover risk — the gates above are. They run in seconds.
"""
from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

import pytest

from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.data.halt_feed import read_halt_events
from bowaka_v2_lab.data.lineage import resolve_lake_root
from bowaka_v2_lab.optuna.preflight import (
    FoldWindow,
    PreflightError,
    check_nbbo_quote_coverage,
    run_full_fold_preflight,
)
from bowaka_v2_lab.optuna.promotion_gates import evaluate_promotion_evidence
from bowaka_v2_lab.reports.feed_divergence import compute_feed_divergence
from bowaka_v2_lab.sim.schedule import scan_times_for_session

pytestmark = pytest.mark.integration

_LAB = Path(__file__).resolve().parents[2]
_FIX = _LAB / "tests" / "fixtures" / "sip_synthetic_lake"
_CFG = _LAB / "configs" / "test_fixtures" / "bowaka_v2_synthetic_sip_intended_realism_smoke.yml"
_SYMS = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE"]
_FOLDS = [FoldWindow(fold_id="val_2025-08-04", kind="validation",
                     start=dt.date(2025, 8, 4), end=dt.date(2025, 8, 22))]


def _cfg() -> dict:
    cfg = load_config(_CFG)
    cfg["market_data"]["shared_root"] = str(_FIX)  # absolute, CWD-independent
    return cfg


def test_smoke_config_resolves_to_fixture_lake() -> None:
    assert resolve_lake_root(_cfg()) == _FIX


@pytest.mark.timeout(120)
def test_intended_realism_sip_preflight_passes_end_to_end() -> None:
    cfg = _cfg()
    run_full_fold_preflight(
        cfg=cfg, folds=_FOLDS, symbols=_SYMS, lake_root=str(_FIX), feed="sip",
        dataset_hash="d" * 64, config_hash="c" * 64,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        min_quote_coverage_pct=80.0, mode="intended_realism",
    )  # must NOT raise


def test_nbbo_gate_passes_with_quotes_and_refuses_without(tmp_path: Path) -> None:
    res = check_nbbo_quote_coverage(
        sim_mode="intended_realism", feed="sip", lake_root=str(_FIX),
        universe=_SYMS, fold_windows=_FOLDS, min_coverage_pct=80.0,
    )
    assert res.passed and res.coverage_pct >= 80.0

    copy = tmp_path / "no_quotes"
    shutil.copytree(_FIX, copy)
    shutil.rmtree(copy / "quotes")
    with pytest.raises(PreflightError) as exc:
        check_nbbo_quote_coverage(
            sim_mode="intended_realism", feed="sip", lake_root=str(copy),
            universe=_SYMS, fold_windows=_FOLDS, min_coverage_pct=80.0,
        )
    assert "nbbo" in str(exc.value).lower() or "quote" in str(exc.value).lower()


def test_halt_feed_reader_picks_up_seeded_luld() -> None:
    halts = read_halt_events(str(_FIX), "AAAA", dt.date(2025, 8, 1), dt.date(2025, 8, 29))
    assert len(halts) >= 1
    assert halts[0].reason == "LULD"


def test_feed_divergence_report_produces_data() -> None:
    rep = compute_feed_divergence(
        sip_root=_FIX, iex_root=_FIX, symbols=["AAAA", "BBBB"],
        sessions=["2025-08-25", "2025-08-26"],
    )
    assert rep["status"] == "ok"
    assert rep["n_rows"] >= 2
    # IEX volume is 0.6x SIP by construction -> non-zero ADV divergence.
    assert max(rep["per_feature_divergence"].values()) > 0.0


def test_promotion_evidence_under_sip_has_no_iex_cap() -> None:
    ev = evaluate_promotion_evidence(
        study_valid=True, invalid_reasons=[], feed="sip",
        simulation_mode="intended_realism", risk_control_drift=False,
        paper_reconciliation_artifact_present=False, best_params={"a": 1},
        requested_tier="paper_candidate", reconcile_report=None,
    )
    assert ev.reviewable_for_research is True
    assert ev.parameter_recommendation_allowed is True   # SIP unlocks this
    assert ev.promotable_to_paper is False               # no reconciliation
    assert "IEX_PARTIAL_TAPE" not in ev.caps_applied
    assert "RECONCILE_MISSING" in ev.caps_applied
