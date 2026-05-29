"""Regime segmentation report (audit 2026-05-29 §9 Phase 5 task 5).

Buckets a finalist's trades by volatility, liquidity (ADV bucket), time-of-day
(the four scanner windows) and market trend, and reports n_trades / win_rate /
mean_pnl / sharpe per bucket. Informational only — no hard gate.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from ..sim.adv_buckets import bucket_for_adv

#: Scanner time-of-day windows (ET), as (label, start_hhmm, end_hhmm).
TOD_WINDOWS: tuple[tuple[str, int, int], ...] = (
    ("0945-1030", 945, 1030),
    ("1030-1200", 1030, 1200),
    ("1200-1400", 1200, 1400),
    ("1400-1530", 1400, 1530),
)


def _hhmm_et(ts: Any) -> Optional[int]:
    try:
        import pandas as pd

        t = pd.Timestamp(ts)
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        et = t.tz_convert("America/New_York")
        return et.hour * 100 + et.minute
    except Exception:
        return None


def _tod_bucket(ts: Any) -> str:
    hhmm = _hhmm_et(ts)
    if hhmm is None:
        return "unknown"
    for label, lo, hi in TOD_WINDOWS:
        if lo <= hhmm < hi:
            return label
    return "other"


def _volatility_bucket(atr_pct: Optional[float]) -> str:
    if atr_pct is None:
        return "unknown"
    a = float(atr_pct)
    if a < 0.02:
        return "low_vol"
    if a < 0.04:
        return "mid_vol"
    return "high_vol"


def _trend_bucket(spy_20d_return: Optional[float]) -> str:
    if spy_20d_return is None:
        return "unknown"
    r = float(spy_20d_return)
    if r > 0.02:
        return "up"
    if r < -0.02:
        return "down"
    return "flat"


def _bucket_stats(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pnls = [float(t.get("pnl", 0.0) or 0.0) for t in trades]
    n = len(pnls)
    if n == 0:
        return {"n_trades": 0, "win_rate": 0.0, "mean_pnl": 0.0, "sharpe": 0.0}
    wins = sum(1 for p in pnls if p > 0)
    mean = statistics.mean(pnls)
    std = statistics.stdev(pnls) if n > 1 else 0.0
    sharpe = (mean / std) if std > 0 else 0.0
    return {
        "n_trades": n,
        "win_rate": wins / n,
        "mean_pnl": float(mean),
        "sharpe": float(sharpe),
    }


def _segment(trades: Sequence[Mapping[str, Any]], key_fn) -> dict[str, Any]:
    buckets: dict[str, list] = {}
    for t in trades:
        buckets.setdefault(key_fn(t), []).append(t)
    return {b: _bucket_stats(ts) for b, ts in buckets.items()}


def segment_trades(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Bucket ``trades`` by each regime dimension.

    Trade keys read (all optional): ``entry_timestamp`` / ``entry_ts`` (ToD),
    ``adv_dollar`` (liquidity), ``atr_pct`` (volatility), ``spy_20d_return``
    (market trend), ``pnl``.
    """
    def _ts(t: Mapping[str, Any]) -> Any:
        return t.get("entry_timestamp", t.get("entry_ts"))

    return {
        "n_trades": len(trades),
        "by_time_of_day": _segment(trades, lambda t: _tod_bucket(_ts(t))),
        "by_liquidity": _segment(
            trades, lambda t: bucket_for_adv(float(t.get("adv_dollar", 0.0) or 0.0)).name,
        ),
        "by_volatility": _segment(trades, lambda t: _volatility_bucket(t.get("atr_pct"))),
        "by_trend": _segment(trades, lambda t: _trend_bucket(t.get("spy_20d_return"))),
    }


def write_regime_artifact(report: Mapping[str, Any], base_path: Path) -> Path:
    base_path = Path(base_path)
    base_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = base_path.with_suffix(".json")
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = ["# Regime segmentation", "", f"- total trades: {report.get('n_trades', 0)}", ""]
    for dim in ("by_time_of_day", "by_liquidity", "by_volatility", "by_trend"):
        lines.append(f"## {dim}")
        lines.append("")
        lines.append("| bucket | n | win_rate | mean_pnl | sharpe |")
        lines.append("|---|---:|---:|---:|---:|")
        for bucket, s in (report.get(dim) or {}).items():
            lines.append(
                f"| {bucket} | {s['n_trades']} | {s['win_rate']:.3f} | "
                f"{s['mean_pnl']:.4g} | {s['sharpe']:.3f} |"
            )
        lines.append("")
    base_path.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path


__all__ = ["TOD_WINDOWS", "segment_trades", "write_regime_artifact"]
