"""Per-scan inner loop wrapper.

Calls ``scanner.scan_loop.evaluate_one_scan`` and routes emitted candidate
events into the ``StrategyConsumer``.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

import pandas as pd

from ..scanner.scan_loop import ScanResult, evaluate_one_scan
from .strategy_consumer import StrategyConsumer, StrategyConsumerResult


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
    quote_supplier: Optional[Callable[[str, Any], Optional[dict]]] = None,
) -> tuple[ScanResult, list[StrategyConsumerResult]]:
    """Run one scan tick and consume each emitted candidate."""
    scan_result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe_snapshot, daily_cache=daily_cache,
        volume_curve=volume_curve, state=state, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
    )
    consumer_results: list[StrategyConsumerResult] = []
    for ev in scan_result.emitted:
        q = quote_supplier(ev["symbol"], scan_ts) if quote_supplier else None
        cr = consumer.consume(ev, decision_ts=scan_ts, historical_quote=q)
        consumer_results.append(cr)
    return scan_result, consumer_results
