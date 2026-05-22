"""Execution-quality report (Realism Phase 6).

Builds ``execution_quality.parquet`` from the per-candidate fill records the
``StrategyConsumer`` produces. The report is a long ``(metric, value)`` table
covering:

- spread distribution — p50 / p90 / p99 (bps)
- quote-age distribution — p50 / p90 / p99 (seconds)
- slippage distribution — p50 / p90 / p99 (bps)
- fill rate, partial-fill rate, missing-quote count
- liquidity-participation distribution
- fees paid (commission + regulatory)
- quote source mix (``historical`` / ``synthetic_calibrated`` / ``synthetic_zero_spread``)
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

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
) -> list[dict[str, Any]]:
    """Build the ``(metric, value)`` rows for ``execution_quality.parquet``.

    ``fills`` is the list of fill records (filled and unfilled) the consumer
    emitted. ``missing_quote_count`` is the number of candidates rejected for a
    missing quote under ``require_real``.
    """
    fill_list = [dict(f) for f in fills]
    n_orders = len(fill_list)
    filled = [f for f in fill_list if f.get("filled")]
    n_filled = len(filled)
    partials = [f for f in filled if f.get("is_partial")]

    spreads_bps = [float(f.get("quote_spread_pct", 0.0) or 0.0) * 10_000.0 for f in fill_list]
    ages = [float(f.get("quote_age_seconds", 0.0) or 0.0) for f in fill_list]
    slippage_bps = [float(f.get("slippage_bps", 0.0) or 0.0) for f in filled]
    participation = [float(f.get("liquidity_participation_frac", 0.0) or 0.0) for f in filled]
    commission = sum(float(f.get("commission", 0.0) or 0.0) for f in filled)
    regulatory = sum(float(f.get("regulatory_fees", 0.0) or 0.0) for f in filled)

    # Quote source mix — count every order's resolved quote source.
    source_counts: dict[str, int] = {}
    for f in fill_list:
        src = str(f.get("quote_source", "unknown"))
        source_counts[src] = source_counts.get(src, 0) + 1

    rows: list[dict[str, Any]] = [
        {"metric": "orders_total", "value": float(n_orders)},
        {"metric": "fill_rate", "value": (n_filled / n_orders) if n_orders else 0.0},
        {"metric": "partial_fill_rate", "value": (len(partials) / n_filled) if n_filled else 0.0},
        {"metric": "missing_quote_count", "value": float(missing_quote_count)},
        {"metric": "spread_bps_p50", "value": _pct(spreads_bps, 0.50)},
        {"metric": "spread_bps_p90", "value": _pct(spreads_bps, 0.90)},
        {"metric": "spread_bps_p99", "value": _pct(spreads_bps, 0.99)},
        {"metric": "quote_age_seconds_p50", "value": _pct(ages, 0.50)},
        {"metric": "quote_age_seconds_p90", "value": _pct(ages, 0.90)},
        {"metric": "quote_age_seconds_p99", "value": _pct(ages, 0.99)},
        {"metric": "slippage_bps_p50", "value": _pct(slippage_bps, 0.50)},
        {"metric": "slippage_bps_p90", "value": _pct(slippage_bps, 0.90)},
        {"metric": "slippage_bps_p99", "value": _pct(slippage_bps, 0.99)},
        {"metric": "liquidity_participation_p50", "value": _pct(participation, 0.50)},
        {"metric": "liquidity_participation_p90", "value": _pct(participation, 0.90)},
        {"metric": "liquidity_participation_p99", "value": _pct(participation, 0.99)},
        {"metric": "fees_commission_total", "value": round(commission, 6)},
        {"metric": "fees_regulatory_total", "value": round(regulatory, 6)},
        {"metric": "fees_total", "value": round(commission + regulatory, 6)},
    ]
    for src, count in sorted(source_counts.items()):
        rows.append({"metric": f"source_mix.{src}", "value": float(count)})
    return rows


def build_execution_quality_frame(
    fills: Iterable[dict],
    *,
    missing_quote_count: int = 0,
) -> pd.DataFrame:
    """The ``execution_quality.parquet`` DataFrame — a ``(metric, value)`` table."""
    rows = build_execution_quality_rows(fills, missing_quote_count=missing_quote_count)
    return pd.DataFrame(rows, columns=["metric", "value"])
