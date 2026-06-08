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
    """Half-open ``[start, end)`` sessions for the PIT preflight (speedup §3).

    Delegates to :func:`calendar_sessions_half_open` so this module and the
    walk-forward runner share a single implementation.
    """
    from .calendar_sessions import calendar_sessions_half_open

    return calendar_sessions_half_open(start, end, calendar=calendar)


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


def eligible_per_session_map(
    lake_root: Any,
    sessions: Iterable[_dt.date],
    *,
    cfg: Optional[Mapping[str, Any]] = None,
) -> Optional[dict[_dt.date, set[str]]]:
    """Per-session PIT-eligible symbol sets for ``sessions``.

    Returns ``{session_date: {eligible symbols}}`` built the SAME way as
    :func:`fold_pit_symbol_union` (identical ``MarketDataStore`` + ``pit_cfg``
    construction, same :func:`build_pit_universe_for_sessions` +
    :func:`eligible_symbols`) but WITHOUT unioning across sessions.

    The coverage gates consume this as a *denominator filter* (audit 2026-06-07
    §6.6-compatible "denominator-only" fix): each gate scores its PASS/FAIL
    fraction over only the ``(symbol, session)`` pairs the live PIT scanner would
    actually evaluate on that session, while the FULL symbol union is still
    PROBED for telemetry — so the audit-2026-05-23 §6.6 uncapped-union invariant
    is preserved.

    Returns ``None`` (the legacy full-union gate) when ``lake_root`` is ``None``,
    there are no sessions, or the PIT build raises. Callers thread the result
    straight into ``build_data_quality_report(..., eligible_per_session=...)``;
    a ``None`` degrades to the full-union fraction and NEVER crashes.
    """
    sessions = list(sessions)
    if lake_root is None or not sessions:
        return None
    try:
        from bowaka_common.marketdata import MarketDataStore
        from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols

        pit_cfg: Mapping[str, Any] = dict(cfg or {})
        store = MarketDataStore(lake_root)
        pit = build_pit_universe_for_sessions(sessions, pit_cfg, store)
        return {sd: set(eligible_symbols(pit.get(sd, {}))) for sd in sessions}
    except Exception as exc:  # noqa: BLE001 — degrade to the legacy full-union gate
        _log().warning(
            "eligible_per_session_map: per-session PIT-eligible build failed "
            "(%s); coverage gates fall back to the full-union fraction "
            "(eligible_per_session=None)",
            exc,
        )
        return None


__all__ = [
    "fold_pit_symbol_union",
    "plan_pit_symbol_union",
    "eligible_per_session_map",
]
