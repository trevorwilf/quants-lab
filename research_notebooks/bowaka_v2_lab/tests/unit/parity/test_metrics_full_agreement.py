"""Metrics: identical trade streams give 1.0 across the board."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.schemas import NormalizedTrade


def _t(symbol: str, *, minute: int, entry: float, exit_p: float,
       pnl: float, reason: str = "target") -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=symbol,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        entry_price=entry, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, minute, tzinfo=_dt.UTC),
        exit_price=exit_p, exit_reason=reason, pnl_dollars=pnl,
    )


def test_full_agreement_yields_unit_metrics() -> None:
    prod = [
        _t("AAA", minute=30, entry=10.0, exit_p=10.5, pnl=50.0),
        _t("BBB", minute=31, entry=5.0, exit_p=4.5, pnl=-50.0, reason="stop"),
    ]
    lab = [
        _t("AAA", minute=30, entry=10.0, exit_p=10.5, pnl=50.0),
        _t("BBB", minute=31, entry=5.0, exit_p=4.5, pnl=-50.0, reason="stop"),
    ]
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=2, prod_trades=prod, prod_candidates=[],
        lab_trades=lab, lab_candidates=[],
    )
    assert report.prod_n_trades == 2
    assert report.lab_n_trades == 2
    assert report.trade_intersection_rate == 1.0
    assert report.fill_price_mae_bps == 0.0
    assert report.exit_reason_match_rate == 1.0
    assert report.daily_pnl_sign_match_rate == 1.0
    # Phase 0 (parity oracle): candidates absent on both sides -> NOT MEASURED
    # (was a false degenerate 1.0 that could mask a real candidate divergence).
    assert report.candidate_recall is None
    assert report.gate_match_rate is None
    assert report.passes_audit_thresholds is True
    assert report.failing_metrics == []
    assert report.prod_only_trades == []
    assert report.lab_only_trades == []


def test_empty_streams_are_vacuous_not_pass_l17() -> None:
    """L17: a parity run with NO trades on EITHER side is VACUOUS — the rates are
    "not measured" (None) and the run FAILS the audit (zero evidence cannot certify
    parity).

    L17 changelog: was ``test_empty_streams_yield_unit_metrics`` which asserted
    ``trade_intersection_rate == 1.0`` and ``passes_audit_thresholds is True`` —
    the vacuous PASS that masked e.g. the prod-backtester producing 0 trades.
    """
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=0, prod_trades=[], prod_candidates=[],
        lab_trades=[], lab_candidates=[],
    )
    # Rates are NOT MEASURED on empty streams (were a misleading 1.0).
    assert report.trade_intersection_rate is None
    assert report.exit_reason_match_rate is None
    assert report.daily_pnl_sign_match_rate is None
    # The vacuous run FAILS the audit (was a silent PASS).
    assert report.passes_audit_thresholds is False
    assert "no_trades_vacuous" in report.failing_metrics
