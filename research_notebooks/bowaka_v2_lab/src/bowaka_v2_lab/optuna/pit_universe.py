"""Full per-fold PIT eligible-universe union (audit 2026-05-23 §6.6 / Phase 1).

Pre-remediation the preflight probed at most 100 symbols regardless of how many
symbols the per-fold PIT universe would actually trade. ``intended_realism``
now requires the preflight to cover the *full union* of eligible symbols across
every session in every validation + holdout window — anything less is a
silently capped preflight and the lab must fail closed.

The walk-forward folds trade the per-session PIT eligible set built by
:func:`universe.builder.build_pit_universe_for_sessions` (rebuilt every session
from the lake asset master + filters). The union across sessions is the set of
symbols the preflight must probe to be honest about coverage.
"""
from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Iterable, Mapping, Optional

import pandas as pd


def _log() -> logging.Logger:
    log = logging.getLogger("bowaka_v2_lab.optuna.pit_universe")
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


def _xnys_sessions(start: _dt.date, end: _dt.date, *, calendar: str = "XNYS") -> list[_dt.date]:
    """Return the list of trading sessions in the half-open ``[start, end)`` window.

    The walk-forward planner uses half-open windows (audit 2026-05-23 §P0-002);
    the union iteration matches that convention so a fold whose ``val_end ==
    final_holdout_start`` never accidentally includes the holdout's first
    session.
    """
    import exchange_calendars as xcals

    cal = xcals.get_calendar(calendar)
    # exchange_calendars' sessions_in_range is closed-closed; emulate half-open
    # by stepping back one day from the end. A single-day fold (start == end)
    # yields an empty list because the window is half-open.
    if start >= end:
        return []
    closed_end = pd.Timestamp(end) - pd.Timedelta(days=1)
    sessions = cal.sessions_in_range(pd.Timestamp(start), closed_end)
    return [pd.Timestamp(s).date() for s in sessions]


def fold_pit_symbol_union(
    lake_root: Any,
    *,
    feed: str,
    fold_start: _dt.date,
    fold_end: _dt.date,
    cfg: Optional[Mapping[str, Any]] = None,
    calendar: str = "XNYS",
    max_sessions: Optional[int] = None,
) -> set[str]:
    """Return the union of every PIT-eligible symbol across every session in
    the half-open window ``[fold_start, fold_end)``.

    Iterates exchange-calendar sessions; for each session builds the PIT
    eligible universe via :func:`build_pit_universe_for_sessions` (prior-day
    baselines, exchange/price/ADV filters, blocklist, instrument-class
    exclusions) and unions the symbols. **Never** capped by symbol count — only
    by the calendar (``max_sessions`` is a safety cap for very long windows so
    a hostile config can't make preflight unbounded; defaults to no cap).

    ``cfg`` is forwarded to :func:`build_pit_universe_for_sessions` (it
    provides the universe-filter config). If ``cfg`` is ``None`` the empty
    config is used; the resulting union reflects the lake's asset master
    intersected with the contract defaults.
    """
    from bowaka_common.marketdata import MarketDataStore
    from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols

    if lake_root is None:
        return set()
    sessions = _xnys_sessions(fold_start, fold_end, calendar=calendar)
    if max_sessions is not None and len(sessions) > max_sessions:
        # The union is monotone-decreasing in session count (more sessions =
        # bigger union), so a hard cap here would *under*-report coverage —
        # but for forensic safety we still warn. Default: no cap.
        _log().warning(
            "fold_pit_symbol_union: capping session count from %d to %d for "
            "[%s, %s); union may under-report coverage",
            len(sessions), max_sessions, fold_start, fold_end,
        )
        sessions = sessions[:max_sessions]
    if not sessions:
        return set()
    pit_cfg: Mapping[str, Any] = dict(cfg or {})
    store = MarketDataStore(lake_root)
    union: set[str] = set()
    pit = build_pit_universe_for_sessions(sessions, pit_cfg, store)
    for sd in sessions:
        union.update(eligible_symbols(pit.get(sd, {})))
    return union


def plan_pit_symbol_union(
    lake_root: Any,
    *,
    feed: str,
    plan,
    cfg: Optional[Mapping[str, Any]] = None,
    include_holdout: bool = True,
    calendar: str = "XNYS",
) -> set[str]:
    """Union the per-fold PIT eligible-universe across every validation fold
    (and optionally the final-holdout window).

    Preflight coverage telemetry is computed against this set: anything less
    than the union is a capped preflight and must be flagged with a waiver.
    """
    union: set[str] = set()
    for split in plan.splits:
        union |= fold_pit_symbol_union(
            lake_root, feed=feed,
            fold_start=split.val_start, fold_end=split.val_end,
            cfg=cfg, calendar=calendar,
        )
    if include_holdout:
        union |= fold_pit_symbol_union(
            lake_root, feed=feed,
            fold_start=plan.final_holdout_start, fold_end=plan.final_holdout_end,
            cfg=cfg, calendar=calendar,
        )
    return union


__all__ = [
    "fold_pit_symbol_union",
    "plan_pit_symbol_union",
]
