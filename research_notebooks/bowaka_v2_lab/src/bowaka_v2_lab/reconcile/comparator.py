"""Match paper candidates → sim candidates by (symbol, scan_timestamp window)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import pandas as pd


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
