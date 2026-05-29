"""Metrics: ``evaluate_thresholds`` handles LOWER-is-better correctly."""
from __future__ import annotations

import datetime as _dt
from dataclasses import replace

from bowaka_v2_lab.parity.metrics import (
    DEFAULT_THRESHOLDS,
    compute_parity_metrics,
    evaluate_thresholds,
)
from bowaka_v2_lab.parity.schemas import NormalizedTrade


def _identical_report() -> "object":
    t = NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol="A",
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC),
        entry_price=10.0, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, 0, tzinfo=_dt.UTC),
        exit_price=10.5, exit_reason="target", pnl_dollars=5.0,
    )
    return compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=1, prod_trades=[t], prod_candidates=[],
        lab_trades=[t], lab_candidates=[],
    )


def test_passes_when_all_metrics_meet_or_beat_threshold() -> None:
    passes, failing = evaluate_thresholds(_identical_report())
    assert passes is True
    assert failing == []


def test_lower_is_better_metric_fails_when_exceeded() -> None:
    # Synthesize a report where every metric is at its threshold EXCEPT
    # fill_price_mae_bps which exceeds it; assert that specific metric is
    # the one flagged.
    base = _identical_report()
    bad = replace(base, fill_price_mae_bps=DEFAULT_THRESHOLDS["fill_price_mae_bps"] + 0.1)
    passes, failing = evaluate_thresholds(bad)
    assert passes is False
    assert failing == ["fill_price_mae_bps"]


def test_higher_is_better_metric_fails_when_below() -> None:
    base = _identical_report()
    bad = replace(base, trade_intersection_rate=0.5)
    passes, failing = evaluate_thresholds(bad)
    assert passes is False
    assert "trade_intersection_rate" in failing


def test_custom_thresholds_override_defaults() -> None:
    base = _identical_report()
    # Default fill_price_mae_bps threshold is 5.0; tighten to 0.5 — identical
    # streams give MAE=0.0 so it still passes; but a 1-bps MAE would fail.
    passes, _failing = evaluate_thresholds(base, thresholds={"fill_price_mae_bps": 0.5})
    assert passes is True
    bumped = replace(base, fill_price_mae_bps=0.6)
    passes2, failing2 = evaluate_thresholds(bumped, thresholds={"fill_price_mae_bps": 0.5})
    assert passes2 is False
    assert failing2 == ["fill_price_mae_bps"]
