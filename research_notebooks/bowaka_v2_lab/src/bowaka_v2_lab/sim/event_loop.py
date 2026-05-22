"""Per-scan inner loop wrapper.

Calls ``scanner.scan_loop.evaluate_one_scan`` and routes emitted candidate
events into the ``StrategyConsumer``.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

import pandas as pd

from ..scanner.scan_loop import ScanResult, evaluate_one_scan
from .strategy_consumer import StrategyConsumer, StrategyConsumerResult


def _call_quote_supplier(
    quote_supplier: Callable[..., Optional[dict]], symbol: str, scan_ts: Any, max_age: int
) -> Optional[dict]:
    """Call ``quote_supplier`` tolerating both the 2-arg and 3-arg signatures.

    Phase 6 quote suppliers take ``(symbol, ts, max_age_seconds)``; older test
    suppliers take ``(symbol, ts)``. Try the 3-arg form first, fall back to
    2-arg on a ``TypeError``.
    """
    try:
        return quote_supplier(symbol, scan_ts, max_age)
    except TypeError:
        return quote_supplier(symbol, scan_ts)


def run_one_scan(
    *,
    cfg: Mapping[str, Any],
    universe_snapshot: Mapping[str, Any],
    daily_cache: pd.DataFrame | None,
    volume_curve: pd.DataFrame | None,
    state: dict[str, Any],
    scan_ts: Any,
    bars_supplier: Callable[[str, Any], pd.DataFrame | None],
    consumer: StrategyConsumer,
    quote_supplier: Optional[Callable[..., Optional[dict]]] = None,
    forward_minute_supplier: Optional[Callable[[str, Any], pd.DataFrame | None]] = None,
) -> tuple[ScanResult, list[StrategyConsumerResult]]:
    """Run one scan tick and consume each emitted candidate.

    ``quote_supplier`` resolves the historical quote per candidate (Phase 6).
    ``forward_minute_supplier`` returns the minute path forward from ``scan_ts``
    so a marketable-limit fill can detect a timeout.
    """
    scan_result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe_snapshot, daily_cache=daily_cache,
        volume_curve=volume_curve, state=state, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
    )
    max_quote_age = int((cfg.get("execution") or {}).get("max_quote_age_seconds", 5))
    consumer_results: list[StrategyConsumerResult] = []
    for ev in scan_result.emitted:
        q = (
            _call_quote_supplier(quote_supplier, ev["symbol"], scan_ts, max_quote_age)
            if quote_supplier
            else None
        )
        # Realism Phase 6: record quote presence for the coverage gate. A row
        # counts as covered only when a real *historical* quote came back.
        is_historical = bool(q) and str((q or {}).get("source", "")) == "historical"
        scan_result.quote_coverage.append({
            "symbol": ev["symbol"],
            "scan_ts": str(scan_ts),
            "quote_present": is_historical,
            "quote_age_seconds": float((q or {}).get("quote_age_seconds", 0.0) or 0.0),
        })
        fwd = forward_minute_supplier(ev["symbol"], scan_ts) if forward_minute_supplier else None
        cr = consumer.consume(
            ev, decision_ts=scan_ts, historical_quote=q, forward_minute_bars=fwd
        )
        consumer_results.append(cr)
    return scan_result, consumer_results
