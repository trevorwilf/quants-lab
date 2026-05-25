"""Precomputed per-fold runtime context for the walk-forward Optuna study.

Speedup report §5.2 / §10.2 / §11.2 Phase 2. Per-fold setup that does NOT
depend on the trial-tuned parameters is pulled OUT of the per-trial loop and
computed ONCE at study start. The contexts are immutable; every trial reuses
the same precomputed sessions, scan times, PIT universe snapshots, eligible
symbols, daily-feature cache, and per-fold supplier callables.

Trial-tuned parameters (signals.*, sizing.*, risk.*, execution.*, exits.*)
do not affect ANY of these inputs. The
:data:`CONTEXT_AFFECTING_PREFIXES` guard refuses any study whose search
space would tune a context-affecting key, so a future careless override
cannot silently invalidate the cache.

The neighbor-rerun and final-holdout flows also use precomputed contexts
(rebuilt once for their respective windows) — never the per-trial path.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

import pandas as pd

from ..config.paths import BowakaV2Paths
from ..data.suppliers import (
    build_daily_cache_from_lake,
    make_forward_minute_supplier,
    make_lake_suppliers,
    make_quote_supplier,
    resolve_intraday_window_policy,
)
from ..sim.schedule import scan_times_for_session
from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols
from .calendar_sessions import calendar_sessions_half_open
from .errors import OptunaStudyInvalidError
from .holdout_guard import HoldoutGuard
from .search_space import resolve_search_space


#: Keys whose value influences the PIT universe / daily baselines / scan
#: cadence / minute-window policy — i.e. the inputs a :class:`FoldRuntimeContext`
#: caches. Any search space that names one of these (as a tunable parameter)
#: is rejected at study start so the precomputed cache cannot silently drift
#: from the per-trial setup.
CONTEXT_AFFECTING_PREFIXES: tuple[str, ...] = (
    "universe.",
    "historical_features.",
    "market_data.",
    "data.",
    "session.scanner_start",
    "session.scanner_end",
    "session.scan_interval_seconds",
    "simulation.intraday_window_policy",
)


@dataclass(frozen=True)
class FoldSupplierBundle:
    """The four per-fold supplier callables, frozen for the study lifetime."""

    minute: Callable[[str, Any], "pd.DataFrame | None"]
    daily: Callable[[str, _dt.date], "pd.DataFrame | None"]
    quote: Callable[..., Optional[dict]]
    forward_minute: Callable[[str, Any], "pd.DataFrame | None"]


@dataclass(frozen=True)
class FoldRuntimeContext:
    """Immutable per-fold cache of every trial-invariant setup."""

    fold_id: str
    val_start: _dt.date
    val_end: _dt.date
    sessions: tuple[_dt.date, ...]
    scan_times_by_session: Mapping[_dt.date, tuple[Any, ...]]
    universe_by_session: Mapping[_dt.date, Any]
    eligible_symbols_by_session: Mapping[_dt.date, tuple[str, ...]]
    daily_cache_by_session: Mapping[_dt.date, pd.DataFrame]
    suppliers: FoldSupplierBundle
    lake_root: Any
    feed: str
    symbols: tuple[str, ...]
    paths: BowakaV2Paths
    holdout_guard: HoldoutGuard


def assert_search_space_does_not_affect_context(
    overrides: Optional[Mapping[str, Any]] = None,
) -> None:
    """Raise :class:`OptunaStudyInvalidError` if any tunable parameter would
    invalidate a precomputed :class:`FoldRuntimeContext`.

    The default search space (no overrides) does not tune any
    context-affecting key; a future careless override that *would* tune one
    is the only way this guard fires. Keep this check before
    :func:`build_fold_contexts` so the precomputed cache is always valid.
    """
    spec = resolve_search_space(dict(overrides or {}))
    offenders = sorted(
        name for name in spec
        if any(name == p.rstrip(".") or name.startswith(p) for p in CONTEXT_AFFECTING_PREFIXES)
    )
    if offenders:
        raise OptunaStudyInvalidError(
            "search space tunes context-affecting key(s) "
            f"{offenders!r}: precomputed FoldRuntimeContext is only safe when "
            "trial parameters do not influence the PIT universe, daily "
            "baselines, scan cadence, or minute-window policy. Either drop the "
            "override or rebuild the context per trial (speedup report §5.2)."
        )


def _build_one_fold_context(
    *,
    fold_id: str,
    val_start: _dt.date,
    val_end: _dt.date,
    base_cfg: Mapping[str, Any],
    lake_root: Any,
    feed: str,
    symbols: tuple[str, ...],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
) -> Optional[FoldRuntimeContext]:
    """Build a :class:`FoldRuntimeContext` for one ``(val_start, val_end)``
    window. Returns ``None`` for an empty session window (so the caller can
    skip the fold rather than carrying an empty context)."""
    from bowaka_common.marketdata import MarketDataStore

    sessions = calendar_sessions_half_open(val_start, val_end)
    if not sessions:
        return None
    cfg = dict(base_cfg)
    intraday_policy = resolve_intraday_window_policy(cfg)
    minute_sup, daily_sup = make_lake_suppliers(
        lake_root, feed=feed, intraday_window_policy=intraday_policy,
    )
    quote_sup = make_quote_supplier(
        lake_root, feed=feed,
        default_max_age_seconds=float(
            (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
        ),
    )
    forward_sup = make_forward_minute_supplier(lake_root, feed=feed)
    universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
    daily_cache: dict[_dt.date, pd.DataFrame] = {}
    eligible: dict[_dt.date, tuple[str, ...]] = {}
    scan_times: dict[_dt.date, tuple[Any, ...]] = {}
    for s in sessions:
        sess_syms = list(eligible_symbols(universe.get(s, {})) or symbols)
        eligible[s] = tuple(sess_syms)
        daily_cache[s] = build_daily_cache_from_lake(lake_root, sess_syms, s, feed=feed)
        scan_times[s] = tuple(scan_times_for_session(s, cfg))
    return FoldRuntimeContext(
        fold_id=fold_id,
        val_start=val_start, val_end=val_end,
        sessions=tuple(sessions),
        scan_times_by_session=scan_times,
        universe_by_session=universe,
        eligible_symbols_by_session=eligible,
        daily_cache_by_session=daily_cache,
        suppliers=FoldSupplierBundle(
            minute=minute_sup, daily=daily_sup,
            quote=quote_sup, forward_minute=forward_sup,
        ),
        lake_root=lake_root,
        feed=feed,
        symbols=tuple(symbols),
        paths=paths,
        holdout_guard=holdout_guard,
    )


def build_fold_contexts(
    base_cfg: Mapping[str, Any],
    plan,
    *,
    lake_root: Any,
    feed: str,
    symbols: list[str] | tuple[str, ...],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
) -> tuple[Optional[FoldRuntimeContext], ...]:
    """Build one :class:`FoldRuntimeContext` per validation split.

    Each entry is ``None`` when the corresponding split has no XNYS sessions
    in its half-open window — the per-trial loop still records the fold (as
    an empty result) but skips the backtest.
    """
    syms = tuple(symbols)
    contexts: list[Optional[FoldRuntimeContext]] = []
    for i, split in enumerate(plan.splits):
        fold_id = f"f{i}_{split.val_start.isoformat()}"
        ctx = _build_one_fold_context(
            fold_id=fold_id,
            val_start=split.val_start, val_end=split.val_end,
            base_cfg=base_cfg, lake_root=lake_root, feed=feed,
            symbols=syms, paths=paths, holdout_guard=holdout_guard,
        )
        contexts.append(ctx)
    return tuple(contexts)


def build_holdout_context(
    base_cfg: Mapping[str, Any],
    plan,
    *,
    lake_root: Any,
    feed: str,
    symbols: list[str] | tuple[str, ...],
    paths: BowakaV2Paths,
    holdout_guard: HoldoutGuard,
) -> Optional[FoldRuntimeContext]:
    """Build a :class:`FoldRuntimeContext` for the final-holdout window."""
    return _build_one_fold_context(
        fold_id=f"holdout_{plan.final_holdout_start.isoformat()}",
        val_start=plan.final_holdout_start,
        val_end=plan.final_holdout_end,
        base_cfg=base_cfg, lake_root=lake_root, feed=feed,
        symbols=tuple(symbols), paths=paths, holdout_guard=holdout_guard,
    )


__all__ = [
    "CONTEXT_AFFECTING_PREFIXES",
    "FoldRuntimeContext",
    "FoldSupplierBundle",
    "assert_search_space_does_not_affect_context",
    "build_fold_contexts",
    "build_holdout_context",
]
