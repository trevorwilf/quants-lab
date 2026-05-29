"""Metrics: fill_price_mae_bps + largest fill diffs."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.schemas import NormalizedTrade


def _t(symbol: str, *, entry: float) -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=symbol,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC),
        entry_price=entry, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, 0, tzinfo=_dt.UTC),
        exit_price=entry * 1.05, exit_reason="target", pnl_dollars=5.0,
    )


def test_fill_price_mae_bps_averages_absolute_diffs() -> None:
    # AAA: 10.00 vs 10.01 -> +10 bps; BBB: 5.00 vs 4.99 -> -20 bps. MAE = 15 bps.
    prod = [_t("AAA", entry=10.00), _t("BBB", entry=5.00)]
    lab = [_t("AAA", entry=10.01), _t("BBB", entry=4.99)]
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=2, prod_trades=prod, prod_candidates=[],
        lab_trades=lab, lab_candidates=[],
    )
    assert abs(report.fill_price_mae_bps - 15.0) < 1e-9
    # MAE 15 bps > 5 bps threshold -> FAIL.
    assert report.passes_audit_thresholds is False
    assert "fill_price_mae_bps" in report.failing_metrics


def test_largest_fill_diffs_sorted_by_absolute_bps() -> None:
    prod = [_t("A", entry=10.0), _t("B", entry=10.0), _t("C", entry=10.0)]
    # Diffs: A +30 bps, B -100 bps, C +5 bps -> ordering by |bps|: B, A, C.
    lab = [_t("A", entry=10.03), _t("B", entry=9.90), _t("C", entry=10.005)]
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=3, prod_trades=prod, prod_candidates=[],
        lab_trades=lab, lab_candidates=[],
    )
    syms = [row["symbol"] for row in report.largest_fill_diffs]
    assert syms[:3] == ["B", "A", "C"]
    # Top row's bps value matches the |-100| diff.
    assert abs(abs(float(report.largest_fill_diffs[0]["fill_diff_bps"])) - 100.0) < 1e-6
