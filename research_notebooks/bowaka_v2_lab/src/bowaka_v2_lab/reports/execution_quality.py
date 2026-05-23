"""Execution-quality report (Realism Phase 6 + realism remediation 2 Phase 5).

Builds ``execution_quality.parquet`` from the per-candidate fill records the
``StrategyConsumer`` produces. The report is a long ``(metric, value)`` table
covering:

- quote coverage — fraction of orders with a real historical quote
- spread distribution — p50 / p95 (bps) + p90 / p99 (legacy)
- quote-age distribution — p50 / p95 (seconds) + p90 / p99 (legacy)
- slippage vs quote mid — p50 / p95 (bps)
- slippage vs quote ask (buy) or bid (sell) — p50 / p95 (bps)
- fill rate, partial-fill rate, no-fill rate
- rejected-by-* counts: spread, stale, missing-quote, price-chase, halt
- liquidity-participation distribution
- fees paid (commission + regulatory)
- quote source mix (``historical`` / ``synthetic_calibrated`` / ``synthetic_zero_spread``)
- execution_tier in use (T0 / T1 / T2 / T3 / T4)
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence

import pandas as pd


def _pct(values: Sequence[float], q: float) -> float:
    """The ``q``-quantile of ``values`` (0..1); ``0.0`` for an empty input."""
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return 0.0
    s = pd.Series(vals, dtype="float64")
    return float(s.quantile(q))


def build_execution_quality_rows(
    fills: Iterable[dict],
    *,
    missing_quote_count: int = 0,
    decisions: Optional[Iterable[Mapping[str, Any]]] = None,
    quote_coverage_rows: Optional[Iterable[Mapping[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """Build the ``(metric, value)`` rows for ``execution_quality.parquet``.

    ``fills`` is the list of fill records (filled and unfilled) the consumer
    emitted. ``missing_quote_count`` is the number of candidates rejected for a
    missing quote under ``require_real``. ``decisions`` (optional) is the
    consumer's decisions list — used to count rejected-by-* reasons for
    spread / stale-quote / price-chase / halt gates. ``quote_coverage_rows``
    (optional) is the per-candidate coverage trace — used to compute quote
    coverage as a fraction.
    """
    fill_list = [dict(f) for f in fills]
    n_orders = len(fill_list)
    filled = [f for f in fill_list if f.get("filled")]
    n_filled = len(filled)
    partials = [f for f in filled if f.get("is_partial")]
    no_fill = [f for f in fill_list if not f.get("filled")]

    spreads_bps = [float(f.get("quote_spread_pct", 0.0) or 0.0) * 10_000.0 for f in fill_list]
    ages = [float(f.get("quote_age_seconds", 0.0) or 0.0) for f in fill_list]
    slippage_bps = [float(f.get("slippage_bps", 0.0) or 0.0) for f in filled]
    slip_vs_mid = [float(f.get("slippage_vs_mid_bps", 0.0) or 0.0) for f in filled]
    slip_vs_ask = [float(f.get("slippage_vs_ask_bps", 0.0) or 0.0) for f in filled]
    participation = [float(f.get("liquidity_participation_frac", 0.0) or 0.0) for f in filled]
    commission = sum(float(f.get("commission", 0.0) or 0.0) for f in filled)
    regulatory = sum(float(f.get("regulatory_fees", 0.0) or 0.0) for f in filled)

    # Quote source mix — count every order's resolved quote source.
    source_counts: dict[str, int] = {}
    for f in fill_list:
        src = str(f.get("quote_source", "unknown"))
        source_counts[src] = source_counts.get(src, 0) + 1

    # Execution tier mix — count every order's modelled tier.
    tier_counts: dict[str, int] = {}
    for f in fill_list:
        tier = f.get("execution_tier")
        if tier:
            tier_counts[str(tier)] = tier_counts.get(str(tier), 0) + 1

    # Rejected-by-* breakdown from the decisions list (audit P0-006/P0-009).
    reject_reasons = (
        "spread_too_wide",
        "quote_stale",
        "missing_quote",
        "price_chase_band",
        "halt_or_pending_review",
        "halt_data_unavailable",
    )
    rej_counts: dict[str, int] = {r: 0 for r in reject_reasons}
    if decisions is not None:
        for d in decisions:
            if d.get("decision") != "rejected":
                continue
            reason = str(d.get("reason") or "")
            if reason in rej_counts:
                rej_counts[reason] += 1

    # Quote coverage from the coverage trace.
    quote_coverage_frac = 0.0
    if quote_coverage_rows is not None:
        cov = list(quote_coverage_rows)
        if cov:
            present = sum(1 for r in cov if bool(r.get("quote_present", False)))
            quote_coverage_frac = present / len(cov)

    rows: list[dict[str, Any]] = [
        {"metric": "orders_total", "value": float(n_orders)},
        {"metric": "fill_rate", "value": (n_filled / n_orders) if n_orders else 0.0},
        {"metric": "partial_fill_rate", "value": (len(partials) / n_filled) if n_filled else 0.0},
        {"metric": "no_fill_rate", "value": (len(no_fill) / n_orders) if n_orders else 0.0},
        {"metric": "missing_quote_count", "value": float(missing_quote_count)},
        {"metric": "quote_coverage_frac", "value": round(quote_coverage_frac, 6)},
        {"metric": "spread_bps_p50", "value": _pct(spreads_bps, 0.50)},
        {"metric": "spread_bps_p90", "value": _pct(spreads_bps, 0.90)},
        {"metric": "spread_bps_p95", "value": _pct(spreads_bps, 0.95)},
        {"metric": "spread_bps_p99", "value": _pct(spreads_bps, 0.99)},
        {"metric": "quote_age_seconds_p50", "value": _pct(ages, 0.50)},
        {"metric": "quote_age_seconds_p90", "value": _pct(ages, 0.90)},
        {"metric": "quote_age_seconds_p95", "value": _pct(ages, 0.95)},
        {"metric": "quote_age_seconds_p99", "value": _pct(ages, 0.99)},
        {"metric": "slippage_bps_p50", "value": _pct(slippage_bps, 0.50)},
        {"metric": "slippage_bps_p90", "value": _pct(slippage_bps, 0.90)},
        {"metric": "slippage_bps_p99", "value": _pct(slippage_bps, 0.99)},
        {"metric": "slippage_vs_mid_bps_p50", "value": _pct(slip_vs_mid, 0.50)},
        {"metric": "slippage_vs_mid_bps_p95", "value": _pct(slip_vs_mid, 0.95)},
        {"metric": "slippage_vs_ask_bps_p50", "value": _pct(slip_vs_ask, 0.50)},
        {"metric": "slippage_vs_ask_bps_p95", "value": _pct(slip_vs_ask, 0.95)},
        {"metric": "liquidity_participation_p50", "value": _pct(participation, 0.50)},
        {"metric": "liquidity_participation_p90", "value": _pct(participation, 0.90)},
        {"metric": "liquidity_participation_p99", "value": _pct(participation, 0.99)},
        {"metric": "fees_commission_total", "value": round(commission, 6)},
        {"metric": "fees_regulatory_total", "value": round(regulatory, 6)},
        {"metric": "fees_total", "value": round(commission + regulatory, 6)},
    ]
    for reason, count in sorted(rej_counts.items()):
        rows.append({"metric": f"rejected_by.{reason}", "value": float(count)})
    for src, count in sorted(source_counts.items()):
        rows.append({"metric": f"source_mix.{src}", "value": float(count)})
    for tier, count in sorted(tier_counts.items()):
        rows.append({"metric": f"execution_tier.{tier}", "value": float(count)})
    return rows


def build_execution_quality_frame(
    fills: Iterable[dict],
    *,
    missing_quote_count: int = 0,
    decisions: Optional[Iterable[Mapping[str, Any]]] = None,
    quote_coverage_rows: Optional[Iterable[Mapping[str, Any]]] = None,
) -> pd.DataFrame:
    """The ``execution_quality.parquet`` DataFrame — a ``(metric, value)`` table."""
    rows = build_execution_quality_rows(
        fills, missing_quote_count=missing_quote_count,
        decisions=decisions, quote_coverage_rows=quote_coverage_rows,
    )
    return pd.DataFrame(rows, columns=["metric", "value"])
