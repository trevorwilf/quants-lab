"""SIP-vs-IEX feature divergence report (audit 2026-05-29 §9 Phase 7 task 4).

A thin, status-aware wrapper over
:func:`bowaka_v2_lab.research.feature_divergence.compute_feature_divergence`.
When SIP data is unavailable (today's IEX-only lake) the report header carries
``status: "SIP_DATA_UNAVAILABLE"`` and zero rows; once SIP partitions land the
report becomes substantive without a code change.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional, Sequence

from ..research.feature_divergence import compute_feature_divergence


def _sip_present(sip_store: Any, symbols: Sequence[str], start: Any, end: Any,
                 *, timeframe: str = "1m") -> bool:
    """True iff ANY symbol has SIP bars in the window."""
    for sym in symbols:
        try:
            if timeframe == "1d":
                df = sip_store.daily_bars(sym, start, end, feed="sip")
            else:
                df = sip_store.minute_bars(sym, start, end, feed="sip")
        except Exception:  # noqa: BLE001 — a missing partition is "not present"
            df = None
        if df is not None and not getattr(df, "empty", True):
            return True
    return False


def feed_divergence_report(
    *,
    iex_store: Any,
    sip_store: Any,
    symbols: Sequence[str],
    start: _dt.date,
    end: _dt.date,
    timeframe: str = "1m",
    **compute_kwargs: Any,
) -> dict[str, Any]:
    """IEX-vs-SIP feature divergence with an explicit availability status.

    Returns a dict with ``status`` in ``{"ok", "SIP_DATA_UNAVAILABLE"}``,
    ``rows`` (per-(symbol, feature) divergence), and (when computed)
    ``max_divergence``.
    """
    base = {
        "schema_version": 1,
        "symbols": list(symbols),
        "start": _dt.date.fromisoformat(str(start)[:10]).isoformat()
        if not isinstance(start, _dt.date) else start.isoformat(),
        "timeframe": timeframe,
    }
    if not symbols or not _sip_present(sip_store, symbols, start, end, timeframe=timeframe):
        return {**base, "status": "SIP_DATA_UNAVAILABLE", "rows": [],
                "n_rows": 0, "max_divergence": 0.0}

    report = compute_feature_divergence(
        iex_store=iex_store, sip_store=sip_store, symbols=list(symbols),
        start=start, end=end, timeframe=timeframe, **compute_kwargs,
    )
    return {
        **base,
        "status": "ok",
        "rows": [r.as_row() for r in report.per_symbol_rows],
        "n_rows": len(report.per_symbol_rows),
        "max_divergence": report.max_divergence(),
        "skipped": list(report.skipped),
    }


def write_feed_divergence_report(report: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


__all__ = ["feed_divergence_report", "write_feed_divergence_report"]
