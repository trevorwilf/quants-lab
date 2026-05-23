"""Match paper candidates → sim candidates by (symbol, scan_timestamp window).

Also hosts the **Phase-9 reconcile tolerance defaults** loaded from
``configs/reconcile_tolerances.yml`` and the helper :func:`load_reconcile_tolerances`
that the CLI / report / tests call to resolve the per-run tolerance dict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import pandas as pd
import yaml


# --------------------------------------------------------------------------
# Realism remediation 2 Phase 9 — reconcile tolerance defaults.
# --------------------------------------------------------------------------
#: Per-stage tolerance defaults — match the Phase-9 prompt and the shipped
#: ``configs/reconcile_tolerances.yml`` defaults. Overrideable by passing a
#: custom tolerances dict OR a file path to :func:`load_reconcile_tolerances`.
DEFAULT_RECONCILE_TOLERANCES: dict[str, float] = {
    "emission_jaccard_min": 0.85,
    "decision_reason_match_min": 0.90,
    "fill_price_tolerance_bps": 5.0,
    "fill_qty_tolerance_shares": 0.0,
    "fill_latency_p95_tolerance_ms": 200.0,
    "pnl_tolerance_dollars": 1.0,
    "exit_timing_tolerance_seconds": 60.0,
}


def _shipped_tolerances_path() -> Path:
    """The path to the shipped ``configs/reconcile_tolerances.yml`` file."""
    return (
        Path(__file__).resolve().parents[2]
        / "configs" / "reconcile_tolerances.yml"
    )


def load_reconcile_tolerances(
    overrides: Path | str | Mapping[str, Any] | None = None,
) -> dict[str, float]:
    """Resolve the per-run reconcile tolerance dict.

    Precedence: built-in :data:`DEFAULT_RECONCILE_TOLERANCES` < shipped
    ``configs/reconcile_tolerances.yml`` (if present) < ``overrides`` (file path
    or in-memory mapping).

    A missing or malformed override file is a soft failure — the defaults still
    apply, but only known keys are honoured (unknown keys are ignored).
    """
    out: dict[str, float] = dict(DEFAULT_RECONCILE_TOLERANCES)
    shipped = _shipped_tolerances_path()
    if shipped.is_file():
        try:
            data = yaml.safe_load(shipped.read_text(encoding="utf-8")) or {}
            for k in DEFAULT_RECONCILE_TOLERANCES:
                if k in data:
                    out[k] = float(data[k])
        except Exception:  # noqa: BLE001 — defaults are still safe
            pass
    if overrides is None:
        return out
    if isinstance(overrides, (str, Path)):
        try:
            data = yaml.safe_load(Path(overrides).read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            return out
    else:
        data = dict(overrides)
    for k in DEFAULT_RECONCILE_TOLERANCES:
        if k in data and data[k] is not None:
            out[k] = float(data[k])
    return out


@dataclass
class MatchEntry:
    paper_event_id: str | None
    sim_event_id: str | None
    symbol: str
    match_kind: str  # "match" | "miss" (paper has no sim) | "extra" (sim has no paper)
    scan_ts_delta_seconds: float | None = None


@dataclass
class ComparatorResult:
    matches: list[MatchEntry] = field(default_factory=list)
    n_match: int = 0
    n_miss: int = 0
    n_extra: int = 0


_TS_KEYS = ("scan_timestamp", "decision_timestamp", "submit_timestamp", "fill_timestamp")


def _record_ts(rec: dict) -> "pd.Timestamp | None":
    for k in _TS_KEYS:
        if rec.get(k):
            try:
                return pd.Timestamp(rec[k])
            except Exception:
                continue
    return None


def compare_candidates(
    paper: list[dict],
    sim: list[dict],
    *,
    window_seconds: int = 120,
) -> ComparatorResult:
    """Match paper candidates (or decisions / orders / fills) against sim by symbol + ts window.

    Falls back to the first available timestamp field (``scan_timestamp``,
    ``decision_timestamp``, ``submit_timestamp``, ``fill_timestamp``) so the
    same comparator works for all log kinds.
    """
    used_sim: set[int] = set()
    out = ComparatorResult()
    for p in paper:
        psym = p.get("symbol")
        pts = _record_ts(p)
        best_idx = -1
        best_delta = None
        for i, s in enumerate(sim):
            if i in used_sim:
                continue
            if s.get("symbol") != psym:
                continue
            sts = _record_ts(s)
            if pts is None or sts is None:
                continue
            delta = abs((sts - pts).total_seconds())
            if delta > window_seconds:
                continue
            if best_delta is None or delta < best_delta:
                best_delta = delta
                best_idx = i
        if best_idx >= 0:
            used_sim.add(best_idx)
            out.matches.append(MatchEntry(
                paper_event_id=p.get("event_id"),
                sim_event_id=sim[best_idx].get("event_id"),
                symbol=psym,
                match_kind="match",
                scan_ts_delta_seconds=best_delta,
            ))
            out.n_match += 1
        else:
            out.matches.append(MatchEntry(
                paper_event_id=p.get("event_id"),
                sim_event_id=None,
                symbol=psym,
                match_kind="miss",
            ))
            out.n_miss += 1
    for i, s in enumerate(sim):
        if i in used_sim:
            continue
        out.matches.append(MatchEntry(
            paper_event_id=None,
            sim_event_id=s.get("event_id"),
            symbol=s.get("symbol"),
            match_kind="extra",
        ))
        out.n_extra += 1
    return out
