"""Metrics: exit_reason_match_rate + mismatch drilldown."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.schemas import NormalizedTrade


def _t(symbol: str, *, minute: int, reason: str) -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=symbol,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        entry_price=10.0, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, minute, tzinfo=_dt.UTC),
        exit_price=10.5, exit_reason=reason, pnl_dollars=5.0,
    )


def test_exit_reason_mismatch_rate_and_drilldown() -> None:
    prod = [
        _t("A", minute=30, reason="target"),
        _t("B", minute=31, reason="stop"),
        _t("C", minute=32, reason="eod"),
        _t("D", minute=33, reason="target"),
    ]
    lab = [
        _t("A", minute=30, reason="target"),
        _t("B", minute=31, reason="signal_fade_soft"),  # mismatch
        _t("C", minute=32, reason="stop"),              # mismatch
        _t("D", minute=33, reason="target"),
    ]
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=4, prod_trades=prod, prod_candidates=[],
        lab_trades=lab, lab_candidates=[],
    )
    # 2 of 4 matched trades agree -> 0.5.
    assert abs(report.exit_reason_match_rate - 0.5) < 1e-9
    syms = {row["symbol"] for row in report.exit_reason_mismatches}
    assert syms == {"B", "C"}
    # Mismatch rows carry both sides' reasons for the drilldown.
    by_sym = {row["symbol"]: row for row in report.exit_reason_mismatches}
    assert by_sym["B"]["prod_exit_reason"] == "stop"
    assert by_sym["B"]["lab_exit_reason"] == "signal_fade_soft"
