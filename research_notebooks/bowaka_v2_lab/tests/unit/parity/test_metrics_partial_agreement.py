"""Metrics: partial agreement — intersection rate, prod-only / lab-only buckets."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.schemas import NormalizedTrade


def _t(symbol: str, *, minute: int, pnl: float = 10.0) -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=symbol,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        entry_price=10.0, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, minute, tzinfo=_dt.UTC),
        exit_price=10.5, exit_reason="target", pnl_dollars=pnl,
    )


def test_partial_overlap_splits_prod_only_and_lab_only() -> None:
    # Shared: AAA@30, CCC@32. Prod-only: BBB@31. Lab-only: DDD@33.
    prod = [_t("AAA", minute=30), _t("BBB", minute=31, pnl=200.0), _t("CCC", minute=32)]
    lab = [_t("AAA", minute=30), _t("CCC", minute=32), _t("DDD", minute=33, pnl=-100.0)]
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=4, prod_trades=prod, prod_candidates=[],
        lab_trades=lab, lab_candidates=[],
    )
    # Jaccard: |intersect| / |union| = 2/4 = 0.5.
    assert abs(report.trade_intersection_rate - 0.5) < 1e-9
    assert report.prod_n_trades == 3
    assert report.lab_n_trades == 3
    assert {t.symbol for t in report.prod_only_trades} == {"BBB"}
    assert {t.symbol for t in report.lab_only_trades} == {"DDD"}
    # The 200 PnL prod-only ranks above any tied entries.
    assert report.prod_only_trades[0].symbol == "BBB"
    # 0.5 jaccard is below the 0.90 threshold; the verdict must FAIL.
    assert report.passes_audit_thresholds is False
    assert "trade_intersection_rate" in report.failing_metrics


def test_session_count_is_union_of_both_sides() -> None:
    prod = [_t("AAA", minute=30)]
    lab_t = NormalizedTrade(
        session_date=_dt.date(2026, 5, 20), symbol="ZZZ",
        entry_ts_minute=_dt.datetime(2026, 5, 20, 14, 30, tzinfo=_dt.UTC),
        entry_price=10.0, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 20, 14, 50, tzinfo=_dt.UTC),
        exit_price=10.1, exit_reason="target", pnl_dollars=10.0,
    )
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 20),
        universe_size=2, prod_trades=prod, prod_candidates=[],
        lab_trades=[lab_t], lab_candidates=[],
    )
    assert report.n_sessions == 2
