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
import time as _time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

import pandas as pd

from ..config.paths import BowakaV2Paths
from ..utils.profile_counters import counters_enabled, current_profile_counters
from ..data.cached_suppliers import (
    make_cached_lake_suppliers,
    make_cached_supplier_callables,
)
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
    """Immutable per-fold cache of every trial-invariant setup.

    Speedup report v2 §4 P4 / §5.6 / Phase 3 task 2 — when the
    ``optuna.acceleration.startup_dq_cache.enabled`` flag is on,
    ``startup_dq_report`` carries the invariant subset of the DQ report
    (filtered via ``build_data_quality_report(..., classify_filter="invariant")``)
    plus a ``_cache_key`` stamped with the lake root, feed, symbols hash,
    sessions, simulation mode, gating-relevant market_data flags,
    config_hash, code_hash, and :data:`DQ_CHECK_INVARIANCE_VERSION`. The
    per-trial ``run_backtest`` reads this when it can, then composes a
    trial-dependent half computed fresh from the trial's tuned ``cfg``.

    ``startup_dq_failure`` is the cached
    :func:`evaluate_startup_dq` verdict against the invariant subset; it
    is ``None`` when the invariant half does not gate the run on its own.
    Trial-dependent failures still surface via the merged report at trial
    time.
    """

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
    startup_dq_report: Optional[dict[str, Any]] = None
    startup_dq_failure: Optional[str] = None


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
    cached_suppliers: bool = False,
) -> Optional[FoldRuntimeContext]:
    """Build a :class:`FoldRuntimeContext` for one ``(val_start, val_end)``
    window. Returns ``None`` for an empty session window (so the caller can
    skip the fold rather than carrying an empty context).

    Speedup report §5.3 / §11.2 Phase 3 — when ``cached_suppliers`` is
    ``True`` the per-fold supplier callables are backed by
    :class:`CachedSessionMarketData` (LRU partition cache, identical
    boundary semantics). Default ``False`` preserves the legacy path.
    """
    from bowaka_common.marketdata import MarketDataStore

    sessions = calendar_sessions_half_open(val_start, val_end)
    if not sessions:
        return None
    cfg = dict(base_cfg)
    intraday_policy = resolve_intraday_window_policy(cfg)
    quote_max_age = float(
        (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
    )
    if cached_suppliers:
        adapter = make_cached_lake_suppliers(
            lake_root, feed=feed,
            intraday_window_policy=intraday_policy,
            default_max_age_seconds=quote_max_age,
        )
        callables = make_cached_supplier_callables(adapter)
        minute_sup = callables["minute"]
        daily_sup = callables["daily"]
        quote_sup = callables["quote"]
        forward_sup = callables["forward_minute"]
    else:
        minute_sup, daily_sup = make_lake_suppliers(
            lake_root, feed=feed, intraday_window_policy=intraday_policy,
        )
        quote_sup = make_quote_supplier(
            lake_root, feed=feed, default_max_age_seconds=quote_max_age,
        )
        forward_sup = make_forward_minute_supplier(lake_root, feed=feed)
    # Speedup report v2 §4 P1 / §5.3 / Phase 1 — opt into the batch daily
    # cache (one parquet read per symbol over the full span, in-memory slices
    # per session) via ``optuna.acceleration.batch_daily_cache.enabled``.
    # Default ``False`` preserves the legacy per-session loop; the batch path
    # produces a bit-for-bit-equal ``dict[date, DataFrame]`` (proven by the
    # parity tests in tests/parity/test_batch_daily_cache_*).
    batch_flag = bool(
        ((cfg.get("optuna") or {}).get("acceleration") or {})
        .get("batch_daily_cache", {}).get("enabled", False)
    )
    _ctx_t_start = _time.perf_counter()
    universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
    daily_cache: dict[_dt.date, pd.DataFrame] = {}
    eligible: dict[_dt.date, tuple[str, ...]] = {}
    scan_times: dict[_dt.date, tuple[Any, ...]] = {}
    for s in sessions:
        sess_syms = list(eligible_symbols(universe.get(s, {})) or symbols)
        eligible[s] = tuple(sess_syms)
        scan_times[s] = tuple(scan_times_for_session(s, cfg))
        if not batch_flag:
            daily_cache[s] = build_daily_cache_from_lake(lake_root, sess_syms, s, feed=feed)
    if batch_flag:
        from ..data.daily_cache_batch import build_daily_cache_for_sessions_from_lake

        daily_cache = build_daily_cache_for_sessions_from_lake(
            lake_root, eligible, sessions, feed=feed,
        )
    # Speedup report v2 §4 P3 / §5.7 / Phase 4 — opt into the session
    # minute-window cache. ``CachedSessionMarketData`` (Phase 3) is a strict
    # superset of what this replaces for the minute supplier, so the gate
    # AND condition (``cached_suppliers`` + flag) gives the Phase 4 path
    # priority for the minute supplier only. Default OFF — adoption is
    # benchmark-only until the parity tests prove the swap.
    session_window_flag = bool(
        ((cfg.get("optuna") or {}).get("acceleration") or {})
        .get("session_minute_window_cache", {}).get("enabled", False)
    )
    if session_window_flag and cached_suppliers:
        from ..scanner.session_minute_window_supplier import (
            make_session_minute_window_supplier,
        )

        minute_sup = make_session_minute_window_supplier(
            MarketDataStore(lake_root), sessions, eligible,
            feed=feed, intraday_policy=intraday_policy,
            max_bar_age_seconds=None,  # legacy parity — see cache docstring
        )
    _ctx_t_end = _time.perf_counter()
    if counters_enabled():
        try:
            current_profile_counters().inc(
                fold_context_build_seconds=_ctx_t_end - _ctx_t_start,
            )
        except LookupError:
            pass

    # Speedup report v2 §4 P4 / §5.6 / Phase 3 task 2 — build the invariant
    # half of the startup DQ report once per fold so per-trial backtests
    # do not rebuild it. Default OFF; the per-trial flow continues to call
    # ``build_data_quality_report`` in full unless the flag is set AND the
    # cache key matches the trial's config.
    startup_dq_report: Optional[dict[str, Any]] = None
    startup_dq_failure: Optional[str] = None
    cache_flag = bool(
        ((cfg.get("optuna") or {}).get("acceleration") or {})
        .get("startup_dq_cache", {}).get("enabled", False)
    )
    if cache_flag:
        from ..data.data_quality import (
            DQ_CHECK_INVARIANCE_VERSION,
            build_data_quality_report,
            evaluate_startup_dq,
        )
        from ..data.lineage import build_dataset_lineage
        import hashlib as _hashlib

        try:
            lineage = build_dataset_lineage(
                cfg=cfg, symbols=symbols,
                start=sessions[0], end=sessions[-1],
                lab_config_hash="fold_dq_cache",
            )
            invariant_half = build_data_quality_report(
                cfg=cfg, lineage=lineage, requested_symbols=symbols,
                sessions=sessions,
                daily_bars_supplier=daily_sup,
                minute_bars_supplier=minute_sup,
                scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
                daily_cache_by_session=daily_cache,
                session_minute_supplier=None,
                classify_filter="invariant",
            )
            md = cfg.get("market_data") or {}
            sim = cfg.get("simulation") or {}
            symbols_hash = _hashlib.sha256(
                ",".join(sorted(symbols)).encode("utf-8")
            ).hexdigest()[:16]
            invariant_half["_cache_key"] = {
                "lake_root": str(lake_root),
                "feed": feed,
                "symbols_hash": symbols_hash,
                "sessions": [s.isoformat() for s in sessions],
                "simulation_mode": (
                    sim.get("mode") if isinstance(sim, dict) else None
                ),
                "market_data_keys": {
                    "require_adjusted_daily_bars":
                        md.get("require_adjusted_daily_bars"),
                    "require_split_adjustment": md.get("require_split_adjustment"),
                    "max_bar_age_seconds": md.get("max_bar_age_seconds"),
                    "max_quote_age_seconds": md.get("max_quote_age_seconds"),
                },
                "dq_check_invariance_version": DQ_CHECK_INVARIANCE_VERSION,
            }
            startup_dq_report = invariant_half
            sim_mode = (sim.get("mode") if isinstance(sim, dict)
                        else "smoke_fixture") or "smoke_fixture"
            startup_dq_failure = evaluate_startup_dq(
                invariant_half, simulation_mode=str(sim_mode),
            )
        except Exception as exc:  # noqa: BLE001 — caching is best-effort
            # Cache build failure must not abort the fold; the per-trial path
            # rebuilds the full report from scratch.
            startup_dq_report = None
            startup_dq_failure = None

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
        startup_dq_report=startup_dq_report,
        startup_dq_failure=startup_dq_failure,
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
    cached_suppliers: bool = False,
) -> tuple[Optional[FoldRuntimeContext], ...]:
    """Build one :class:`FoldRuntimeContext` per validation split.

    Each entry is ``None`` when the corresponding split has no XNYS sessions
    in its half-open window — the per-trial loop still records the fold (as
    an empty result) but skips the backtest.

    ``cached_suppliers=True`` opts each context's supplier callables into
    the Phase 3 LRU-cached adapter (default ``False``).
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
            cached_suppliers=cached_suppliers,
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
    cached_suppliers: bool = False,
) -> Optional[FoldRuntimeContext]:
    """Build a :class:`FoldRuntimeContext` for the final-holdout window."""
    return _build_one_fold_context(
        fold_id=f"holdout_{plan.final_holdout_start.isoformat()}",
        val_start=plan.final_holdout_start,
        val_end=plan.final_holdout_end,
        base_cfg=base_cfg, lake_root=lake_root, feed=feed,
        symbols=tuple(symbols), paths=paths, holdout_guard=holdout_guard,
        cached_suppliers=cached_suppliers,
    )


__all__ = [
    "CONTEXT_AFFECTING_PREFIXES",
    "FoldRuntimeContext",
    "FoldSupplierBundle",
    "assert_search_space_does_not_affect_context",
    "build_fold_contexts",
    "build_holdout_context",
]
