"""Phase 0 — golden-bundle persist + diff round-trips and catches real drift."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.parity.golden import (
    diff_parity_bundles,
    persist_parity_bundle,
)
from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.schemas import NormalizedCandidate, NormalizedTrade


def _t(sym: str, minute: int, *, entry: float = 10.0, pnl: float = 5.0,
       reason: str = "target") -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=sym,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        entry_price=entry, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, minute, tzinfo=_dt.UTC),
        exit_price=entry + 0.5, exit_reason=reason, pnl_dollars=pnl,
    )


def _report(prod, lab, prod_c=(), lab_c=()):
    return compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=5, prod_trades=prod, prod_candidates=list(prod_c),
        lab_trades=lab, lab_candidates=list(lab_c),
    )


def test_identical_bundles_match(tmp_path) -> None:
    prod = [_t("AAA", 30), _t("BBB", 31, pnl=-3.0, reason="stop")]
    lab = list(prod)
    rep = _report(prod, lab)
    g = persist_parity_bundle(tmp_path / "g", report=rep, prod_trades=prod,
                              lab_trades=lab, lab_candidates=[])
    c = persist_parity_bundle(tmp_path / "c", report=rep, prod_trades=prod,
                              lab_trades=lab, lab_candidates=[])
    d = diff_parity_bundles(g, c)
    assert d["match"] is True
    assert d["report_diffs"] == [] and d["trade_diffs"] == [] and d["candidate_diffs"] == []


def test_sub_tolerance_price_change_still_matches(tmp_path) -> None:
    prod = [_t("AAA", 30, entry=10.0)]
    g = persist_parity_bundle(tmp_path / "g", report=_report(prod, prod),
                              prod_trades=prod, lab_trades=prod, lab_candidates=[])
    lab2 = [_t("AAA", 30, entry=10.0 + 1e-13)]  # below PRICE_TOL (1e-12)
    c = persist_parity_bundle(tmp_path / "c", report=_report(prod, lab2),
                              prod_trades=prod, lab_trades=lab2, lab_candidates=[])
    assert diff_parity_bundles(g, c)["match"] is True


def test_real_price_drift_is_caught(tmp_path) -> None:
    prod = [_t("AAA", 30, entry=10.0)]
    g = persist_parity_bundle(tmp_path / "g", report=_report(prod, prod),
                              prod_trades=prod, lab_trades=prod, lab_candidates=[])
    lab2 = [_t("AAA", 30, entry=10.01)]  # 0.01 >> tol
    c = persist_parity_bundle(tmp_path / "c", report=_report(prod, lab2),
                              prod_trades=prod, lab_trades=lab2, lab_candidates=[])
    d = diff_parity_bundles(g, c)
    assert d["match"] is False
    assert any(x.get("field") == "entry_price" and x["label"] == "lab_trades"
               for x in d["trade_diffs"])


def test_missing_trade_is_caught(tmp_path) -> None:
    prod = [_t("AAA", 30), _t("BBB", 31)]
    g = persist_parity_bundle(tmp_path / "g", report=_report(prod, prod),
                              prod_trades=prod, lab_trades=prod, lab_candidates=[])
    lab2 = [_t("AAA", 30)]  # BBB dropped
    c = persist_parity_bundle(tmp_path / "c", report=_report(prod, lab2),
                              prod_trades=prod, lab_trades=lab2, lab_candidates=[])
    d = diff_parity_bundles(g, c)
    assert d["match"] is False
    assert any(x.get("kind") == "missing_in_candidate" and x["label"] == "lab_trades"
               for x in d["trade_diffs"])


def test_exit_reason_drift_is_caught(tmp_path) -> None:
    prod = [_t("AAA", 30, reason="target")]
    g = persist_parity_bundle(tmp_path / "g", report=_report(prod, prod),
                              prod_trades=prod, lab_trades=prod, lab_candidates=[])
    lab2 = [_t("AAA", 30, reason="stop")]
    c = persist_parity_bundle(tmp_path / "c", report=_report(prod, lab2),
                              prod_trades=prod, lab_trades=lab2, lab_candidates=[])
    d = diff_parity_bundles(g, c)
    assert d["match"] is False
    assert any(x.get("field") == "exit_reason" for x in d["trade_diffs"])


def test_candidate_stream_drift_is_caught(tmp_path) -> None:
    prod = [_t("AAA", 30)]
    c1 = NormalizedCandidate(
        session_date=_dt.date(2026, 5, 19), symbol="AAA",
        candidate_ts_minute=_dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC),
        gate_passed=True, gate_rejection_reason=None,
    )
    c2 = NormalizedCandidate(
        session_date=_dt.date(2026, 5, 19), symbol="AAA",
        candidate_ts_minute=_dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC),
        gate_passed=False, gate_rejection_reason="adv_gate",
    )
    g = persist_parity_bundle(tmp_path / "g", report=_report(prod, prod, lab_c=[c1]),
                              prod_trades=prod, lab_trades=prod, lab_candidates=[c1])
    c = persist_parity_bundle(tmp_path / "c", report=_report(prod, prod, lab_c=[c2]),
                              prod_trades=prod, lab_trades=prod, lab_candidates=[c2])
    d = diff_parity_bundles(g, c)
    assert d["match"] is False
    assert any(x.get("field") == "gate_passed" for x in d["candidate_diffs"])
