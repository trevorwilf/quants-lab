"""Audit P0-006 — execution_quality report carries the required fields.

The Phase 5 audit acceptance lists the explicit fields the execution-quality
report must surface:

- quote coverage %, median/95p spread bps, median/95p quote age
- rejected counts by reason (spread, stale, missing-quote, price-chase, halt)
- fill rate, partial-fill rate, no-fill rate
- median/95p slippage vs quote mid, median/95p slippage vs quote ask (buy)
- execution_tier in use
"""
from __future__ import annotations

from bowaka_v2_lab.reports.execution_quality import build_execution_quality_rows


def test_execution_quality_report_has_required_fields() -> None:
    fills = [
        {
            "parent_order_id": "p1", "symbol": "AAA",
            "order_style": "marketable_limit", "filled": True,
            "filled_qty": 100, "requested_qty": 100,
            "avg_fill_price": 10.0, "notional": 1000.0,
            "slippage_bps": 5.0, "slippage_vs_mid_bps": 5.0, "slippage_vs_ask_bps": 0.0,
            "is_partial": False, "reason": None,
            "commission": 0.01, "regulatory_fees": 0.001,
            "liquidity_participation_frac": 0.02,
            "execution_tier": "T1_TOP_OF_BOOK", "fill_time_seconds": 0.0,
            "quote_source": "historical",
            "quote_spread_pct": 0.001, "quote_age_seconds": 0.5,
            "cost_stress": "base",
        },
        {
            "parent_order_id": "p2", "symbol": "BBB",
            "order_style": "marketable_limit", "filled": False,
            "filled_qty": 0, "requested_qty": 100,
            "avg_fill_price": 0.0, "notional": 0.0,
            "slippage_bps": 0.0, "slippage_vs_mid_bps": 0.0, "slippage_vs_ask_bps": 0.0,
            "is_partial": False, "reason": "marketable_limit_timeout",
            "commission": 0.0, "regulatory_fees": 0.0,
            "liquidity_participation_frac": 0.0,
            "execution_tier": "T1_TOP_OF_BOOK", "fill_time_seconds": 0.0,
            "quote_source": "historical",
            "quote_spread_pct": 0.001, "quote_age_seconds": 0.5,
            "cost_stress": "base",
        },
    ]
    decisions = [
        {"decision": "rejected", "reason": "spread_too_wide"},
        {"decision": "rejected", "reason": "quote_stale"},
        {"decision": "rejected", "reason": "missing_quote"},
        {"decision": "rejected", "reason": "price_chase_band"},
        {"decision": "rejected", "reason": "halt_or_pending_review"},
        {"decision": "rejected", "reason": "halt_data_unavailable"},
        {"decision": "accepted"},
    ]
    coverage_rows = [
        {"symbol": "AAA", "quote_present": True},
        {"symbol": "BBB", "quote_present": False},
        {"symbol": "CCC", "quote_present": True},
    ]

    rows = build_execution_quality_rows(
        fills, missing_quote_count=1,
        decisions=decisions, quote_coverage_rows=coverage_rows,
    )
    metrics = {r["metric"]: r["value"] for r in rows}

    # Quote coverage as a fraction.
    assert "quote_coverage_frac" in metrics
    assert abs(metrics["quote_coverage_frac"] - 2 / 3) < 1e-5

    # Spread / quote-age distributions (p50, p95).
    assert "spread_bps_p50" in metrics
    assert "spread_bps_p95" in metrics
    assert "quote_age_seconds_p50" in metrics
    assert "quote_age_seconds_p95" in metrics

    # Slippage distributions vs mid AND vs ask.
    assert "slippage_vs_mid_bps_p50" in metrics
    assert "slippage_vs_mid_bps_p95" in metrics
    assert "slippage_vs_ask_bps_p50" in metrics
    assert "slippage_vs_ask_bps_p95" in metrics

    # Fill / partial-fill / no-fill rates.
    assert "fill_rate" in metrics
    assert "partial_fill_rate" in metrics
    assert "no_fill_rate" in metrics
    assert metrics["fill_rate"] == 0.5
    assert metrics["no_fill_rate"] == 0.5

    # Rejected counts by reason.
    for reason in ("spread_too_wide", "quote_stale", "missing_quote",
                   "price_chase_band", "halt_or_pending_review",
                   "halt_data_unavailable"):
        key = f"rejected_by.{reason}"
        assert key in metrics, f"missing {key}"
        assert metrics[key] == 1.0

    # Execution tier in use.
    assert "execution_tier.T1_TOP_OF_BOOK" in metrics
    assert metrics["execution_tier.T1_TOP_OF_BOOK"] == 2.0
