"""Comprehensive event-driven backtester orchestrator.

Per [Report §9.2] pseudo-code:
1. Begin session (recompute gross_exposure_dollars from open_positions)
2. For each scan_ts in scan_times:
   - evaluate_one_scan → emitted candidate events
   - For each candidate: consume → emit decision; on accept → add position
3. End-of-session mark-to-market on each open position
4. Evaluate exits on each open position using daily/minute bars
5. End session — roll forward open positions
6. Write artifacts at end of run (16-file contract per [Report §18.1])
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Mapping, Optional

import numpy as np
import pandas as pd

_log = logging.getLogger("bowaka_v2_lab.sim.backtester")
#: §10g per-scan-speed audit — fire the matrix-miss warning once per process
#: (the ``matrix_session_miss`` profile counter tallies every miss).
_MATRIX_MISS_WARNED = False

from bowaka_common.artifacts.code_manifest import build_code_manifest, code_manifest_hash
from bowaka_common.artifacts.dataset_manifest import build_dataset_manifest
from bowaka_common.artifacts.run_manifest import build_run_manifest

from ..config.config_diff import (
    unannotated_mismatches,
    write_config_diff,
    write_empty_config_diff,
)
from ..config.hashing import canonical_run_hash, canonical_strategy_hash
from ..config.models import SimulationConfig
from ..config.paths import BowakaV2Paths
from ..data.data_quality import (
    DQ_CHECK_INVARIANCE_VERSION,
    StartupDataQualityError,
    build_data_quality_report,
    evaluate_startup_dq,
    merge_dq_reports,
)
from ..data.lineage import build_dataset_lineage
from ..reference import actual_contract_hash, contract_available, load_actual_contract
from ..scanner.scan_context import build_scan_session_context
from ..universe.builder import UniverseRecord, to_scanner_snapshot
from ..universe.persist import write_universe_artifacts
from ..utils.atomic_io import append_jsonl, atomic_write_json, write_parquet
from ..utils.ids import generate_run_id
from ..utils.profile_counters import counters_enabled as _profile_counters_enabled
from ..utils.profile_counters import current_profile_counters as _profile_counters_current
from ..utils.time import require_aware_timestamp
from .broker import SimulatedBroker
from .event_loop import (
    CadenceConfig,
    Event,
    EventQueue,
    EventType,
    preload_session_events,
    run_one_scan,
)
from .exit_driver import drive_session_exits_daily, drive_session_exits_minute
from .exits import FadeTelemetry, walk_lot_exit
from .metrics import build_summary
from .portfolio import Portfolio, Position, ProtectionState
from .protection import ProtectionConfig, ProtectionStateMachine
from .schedule import scan_times_for_session


@dataclass
class BacktestResult:
    run_id: str
    run_dir: Path
    summary: dict
    trades: list[dict]
    decisions: list[dict]
    candidate_events: list[dict]
    portfolio: Portfolio

    # Speedup report §5.1 / §11.2 Phase 1 — the in-memory artifacts the
    # walk-forward objective consumes. Populated whether artifact_mode is
    # ``full`` or ``objective_minimal`` so a single converter
    # (``fold_result_from_backtest_result``) works for both modes without
    # re-reading parquet/json. ``None`` only when the field is not collected
    # for a given run (defensive default).
    daily_equity: list[dict] = field(default_factory=list)
    execution_quality_rows: list[dict] = field(default_factory=list)
    quote_coverage_rows: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    fills: list[dict] = field(default_factory=list)
    positions: list[dict] = field(default_factory=list)
    exit_analysis: Optional[dict] = None
    #: ``ProfileCounters.snapshot()`` when counters were active during the
    #: run; ``None`` otherwise (the default).
    profile_counters: Optional[dict] = None
    #: The ``artifact_mode`` the run executed in — useful for downstream
    #: assertions / tests.
    artifact_mode: str = "full"


_REQUIRED_ARTIFACTS = (
    "run_manifest.json",
    "config_snapshot.json",
    "dataset_manifest.json",
    "code_manifest.json",
    "data_quality_report.json",
    "candidate_events.jsonl",
    "candidate_events.parquet",
    "gate_dump.parquet",
    "entry_decisions.parquet",
    "orders.parquet",
    "fills.parquet",
    "positions.parquet",
    "trades.parquet",
    "daily_equity.parquet",
    "execution_quality.parquet",
    # Realism remediation 2 Phase 4: per-event dispatch log. Records every
    # SCAN / PROTECTION_CHECK / CHILD_FILL / EOD_MARK etc. with the portfolio
    # state at the end of the event. Sessions over the cap (default 50k rows)
    # are rotated to ``events/by_session/<date>.parquet`` so any single file is
    # bounded; the canonical roll-up always stays at the path below.
    "events/events.parquet",
    "summary.json",
    "report.md",
    "report.json",
    "config_diff_vs_actual_bowaka_v2.yaml",
)


#: Realism remediation 2 Phase 4: row cap for the canonical event log roll-up.
#: A run that exceeds the cap still emits the canonical ``events/events.parquet``
#: (truncated) and writes the full per-session detail to
#: ``events/by_session/<session>.parquet``.
_EVENTS_PER_SESSION_CAP = 50_000


def _git_head() -> str:
    """Short-lived ``git rev-parse HEAD`` for run lineage; ``"unknown"`` on failure."""
    try:
        import subprocess

        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path(__file__).resolve().parent),
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:  # noqa: BLE001 — lineage is best-effort, never fatal
        pass
    return "unknown"


def _is_synthetic_universe_snapshot(snapshot: Any) -> bool:
    """True when ``snapshot`` is the deterministic synthetic-fixture universe.

    The synthetic fixture (``sim.replay_fixtures.synthetic_universe``) marks
    itself with ``universe_hash == "sha256:synthetic"``; the PIT builder's
    snapshot carries ``synthetic: False``. Either signal is conclusive.
    """
    if not isinstance(snapshot, Mapping):
        return False
    if snapshot.get("synthetic") is True:
        return True
    if snapshot.get("synthetic") is False:
        return False
    return str(snapshot.get("universe_hash", "")) == "sha256:synthetic"


def _normalise_universe_by_session(
    universe_snapshot_by_session: Mapping[_dt.date, Any],
    *,
    sim_mode: str,
) -> tuple[dict[_dt.date, dict], dict[_dt.date, dict[str, UniverseRecord]]]:
    """Normalise per-session universes to scanner-snapshot dicts.

    Accepts either the legacy snapshot dict (``{"universe_hash", "symbols"}``)
    or the Phase-3 PIT ``{symbol: UniverseRecord}`` map, per session. Returns
    ``(snapshot_by_session, pit_records_by_session)`` — the latter is non-empty
    only for sessions supplied as PIT records (so universe artifacts are written
    only for real PIT universes).

    A **synthetic** universe in a non-smoke (``current_code_parity`` /
    ``intended_realism``) run is refused: a real run must consume the
    point-in-time universe, not the deterministic fixture.
    """
    snapshots: dict[_dt.date, dict] = {}
    pit_records: dict[_dt.date, dict[str, UniverseRecord]] = {}
    non_smoke = sim_mode in ("current_code_parity", "intended_realism", "fast_realism")
    for session_date, value in universe_snapshot_by_session.items():
        is_snapshot_dict = isinstance(value, Mapping) and (
            "symbols" in value or "universe_hash" in value
        )
        is_pit_records = isinstance(value, Mapping) and not is_snapshot_dict and (
            not value or all(isinstance(v, UniverseRecord) for v in value.values())
        )
        if is_pit_records:
            # Phase-3 PIT record map for this session (possibly empty).
            pit_records[session_date] = dict(value)
            snapshots[session_date] = to_scanner_snapshot(value)
            continue
        # Legacy snapshot dict.
        if non_smoke and _is_synthetic_universe_snapshot(value):
            raise RuntimeError(
                f"run_backtest refused: simulation.mode={sim_mode!r} consumed a "
                f"synthetic universe for session {session_date}. A non-smoke run must "
                f"use the point-in-time universe (universe.build_pit_universe_for_"
                f"sessions). Synthetic universes are permitted only in smoke_fixture mode."
            )
        snapshots[session_date] = dict(value) if isinstance(value, Mapping) else value
    return snapshots, pit_records


#: Row count past which the gate dump is *also* written partitioned per session
#: date (under ``scanner/gate_dump_by_session/``) so no single parquet is huge.
#: Full intraday replay produces ~scans x universe rows; a multi-month run can
#: reach millions of rows.
_GATE_DUMP_PARTITION_THRESHOLD = 250_000


def _write_gate_dump(run_dir: Path, all_gate_dump: list[dict]) -> None:
    """Write the per-(scan_ts, symbol) gate dump (realism Phase 4).

    Always writes the canonical ``gate_dump.parquet`` at the run-dir root (the
    path the artifact contract + promotion checklist enforce). When the dump
    exceeds :data:`_GATE_DUMP_PARTITION_THRESHOLD` rows it is additionally
    written partitioned per session date under
    ``scanner/gate_dump_by_session/<session>.parquet`` so each file is bounded.
    """
    if not all_gate_dump:
        # Keep the contract path present even when no scan ran.
        write_parquet(run_dir / "gate_dump.parquet", pd.DataFrame({"symbol": []}))
        return
    df = pd.json_normalize(all_gate_dump, sep=".")
    write_parquet(run_dir / "gate_dump.parquet", df)
    if len(df) <= _GATE_DUMP_PARTITION_THRESHOLD:
        return
    # Large dump — also partition per session date for bounded files.
    part_dir = run_dir / "scanner" / "gate_dump_by_session"
    part_dir.mkdir(parents=True, exist_ok=True)
    if "scan_ts" in df.columns:
        session_dates = (
            pd.to_datetime(df["scan_ts"], utc=True, errors="coerce")
            .dt.tz_convert("America/New_York")
            .dt.date
        )
        for session_date, part in df.groupby(session_dates):
            if pd.isna(session_date):
                continue
            write_parquet(part_dir / f"{session_date.isoformat()}.parquet", part)


def _build_fade_score_fn(
    *,
    cfg: Mapping[str, Any],
    daily_cache: Optional[pd.DataFrame],
    volume_curve: Optional[pd.DataFrame],
    minute_bars_supplier: Optional[Callable[[str, Any], pd.DataFrame | None]],
    session_minute_supplier: Optional[Callable[[str, _dt.date], pd.DataFrame | None]],
) -> Callable[[Any, pd.Timestamp], Optional[float]]:
    """Build the signal-fade re-scoring closure (Realism Phase 7, Task 5).

    Returns ``fn(pos, eval_ts) -> Optional[float]`` — at the signal-fade
    ``eval_time`` it recomputes the signal score on the *forming bar* (minute
    bars up to ``eval_ts``) against the lot's prior daily baselines, exactly as
    the live scanner scores a candidate. Returns ``None`` when the inputs to a
    score are missing (no minute bars / no prior baseline row).
    """
    from ..features.forming_bar import (
        aggregate_forming_session_bar,
        compute_forming_session_features,
        compute_signal_strength,
        compute_volume_curve_fraction,
    )

    score_cfg = dict((cfg.get("scoring") or cfg.get("score") or {}))
    # Per-symbol prior baselines from the session daily cache.
    cache_by_symbol: dict[str, dict] = {}
    if daily_cache is not None and len(daily_cache) > 0:
        for _, r in daily_cache.iterrows():
            cache_by_symbol[str(r.get("symbol"))] = r.to_dict()

    def fade_score_fn(pos: Any, eval_ts: pd.Timestamp) -> Optional[float]:
        baseline = cache_by_symbol.get(pos.symbol)
        if baseline is None:
            return None
        # Minute bars forming up to the eval timestamp.
        bars: Optional[pd.DataFrame] = None
        eval_date = pd.Timestamp(eval_ts).tz_convert("America/New_York").date()
        if session_minute_supplier is not None:
            try:
                full = session_minute_supplier(pos.symbol, eval_date)
            except Exception:  # noqa: BLE001
                full = None
            if full is not None and len(full) > 0:
                tcol = next((c for c in ("timestamp", "ts") if c in full.columns), None)
                if tcol is not None:
                    tsv = pd.to_datetime(full[tcol], utc=True)
                    bars = full[tsv <= pd.Timestamp(eval_ts)]
        if (bars is None or len(bars) == 0) and minute_bars_supplier is not None:
            try:
                bars = minute_bars_supplier(pos.symbol, eval_ts)
            except Exception:  # noqa: BLE001
                bars = None
        if bars is None or len(bars) == 0:
            return None
        try:
            sess = aggregate_forming_session_bar(bars)
        except Exception:  # noqa: BLE001 - naive ts etc.; treat as un-scorable
            return None
        adv_bucket = str(baseline.get("adv_bucket", "mid"))
        vcf = compute_volume_curve_fraction(volume_curve, eval_ts, adv_bucket)
        prior = {
            "prior_close": baseline.get("prior_close"),
            "prior_atr_14d": baseline.get("prior_atr_14d"),
            "avg_volume_20d": baseline.get("avg_volume_20d"),
            "avg_dollar_volume_20d": baseline.get("avg_dollar_volume_20d"),
            "ema_10_prior": baseline.get("ema_10_prior"),
        }
        feats = compute_forming_session_features(sess, prior, vcf)
        return compute_signal_strength(
            feats, score_cfg, ema_slope_prior=baseline.get("ema_slope_prior"),
        )

    return fade_score_fn


@dataclass
class _SessionAccumulators:
    """Per-session collectors driven by the event dispatcher.

    Holding them in a dataclass lets the dispatch handlers append without a
    long keyword-argument list. Each list is later concatenated onto the run's
    cross-session collectors so the artifact contract is unchanged.
    """

    candidate_events: list[dict] = field(default_factory=list)
    gate_dump: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    fills: list[dict] = field(default_factory=list)
    fill_records: list[dict] = field(default_factory=list)
    quote_coverage: list[dict] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)
    fade_telemetry: list[FadeTelemetry] = field(default_factory=list)
    missing_quote_count: int = 0
    ambiguous_count: int = 0
    event_log: list[dict] = field(default_factory=list)


def _portfolio_snapshot(portfolio: Portfolio) -> dict[str, Any]:
    """Snapshot the fields Phase 4 audits in :class:`PortfolioState`.

    The event log captures this dict at the END of every event so a later test
    can prove a state field updated *between* events. Returned keys match the
    documented per-event mutations (audit §9.2).
    """
    s = portfolio.state
    if s is None:
        return {
            "bankroll": float(portfolio.initial_bankroll),
            "open_positions": len(portfolio.open_positions),
            "entries_today": 0,
            "stopouts_today": 0,
            "consecutive_stopouts": 0,
            "daily_realized_pnl": 0.0,
            "daily_unrealized_pnl": 0.0,
            "gross_exposure_dollars": 0.0,
            "gross_exposure_pct": 0.0,
            "kill_switch_state": None,
            "entered_symbols_today_count": 0,
        }
    return {
        "bankroll": float(s.bankroll),
        "open_positions": len(portfolio.open_positions),
        "entries_today": int(s.entries_today),
        "stopouts_today": int(s.stopouts_today),
        "consecutive_stopouts": int(s.consecutive_stopouts),
        "daily_realized_pnl": float(s.daily_realized_pnl),
        "daily_unrealized_pnl": float(s.daily_unrealized_pnl),
        "gross_exposure_dollars": float(s.gross_exposure_dollars),
        "gross_exposure_pct": float(s.gross_exposure_pct),
        "kill_switch_state": s.kill_switch_state,
        "entered_symbols_today_count": len(s.entered_symbols_today),
    }


def _log_event(
    acc: _SessionAccumulators,
    *,
    event: Event,
    portfolio: Portfolio,
    extras: Optional[Mapping[str, Any]] = None,
) -> None:
    """Append one row to the per-session event log.

    Captures ``(timestamp, event_type, position_id or parent_order_id,
    portfolio state)`` per the Phase 4 contract. The per-session row count is
    capped by ``_EVENTS_PER_SESSION_CAP`` to keep any single canonical parquet
    bounded; sessions over the cap rotate the FULL log to a per-session
    partition (handled at write time).
    """
    # Realism remediation 2 Phase 6 — event timestamps are floored to the
    # second when written to the event log so consumers (and the Phase-4
    # ``test_event_log_chronological_and_complete`` test) can parse them with
    # a single :func:`pd.to_datetime` call. The state machine occasionally
    # produces sub-second offsets (``oco_attach_latency_seconds=0.5``); the
    # in-memory queue keeps the full precision so dispatch ordering remains
    # exact, but the persisted log uses second resolution.
    ts_floored = pd.Timestamp(event.timestamp).floor("s")
    row: dict[str, Any] = {
        "timestamp": ts_floored.isoformat(),
        "event_type": event.type.name,
        "session_date": (
            event.payload.get("session_date").isoformat()
            if isinstance(event.payload.get("session_date"), _dt.date)
            else str(event.payload.get("session_date", ""))
        ),
        "position_id": event.payload.get("position_id"),
        "parent_order_id": event.payload.get("parent_order_id"),
        "symbol": event.payload.get("symbol"),
    }
    row.update(_portfolio_snapshot(portfolio))
    if extras:
        for k, v in extras.items():
            # Don't clobber the snapshot keys.
            if k not in row:
                row[k] = v
    acc.event_log.append(row)


def _check_lot_exits_until(
    portfolio: Portfolio,
    *,
    until_ts: pd.Timestamp,
    session_date: _dt.date,
    cfg: Mapping[str, Any],
    bars_by_lot: dict[str, Optional[pd.DataFrame]],
    quote_supplier: Optional[Callable[..., Optional[dict]]],
    signal_score_fn: Optional[Callable[[Any, pd.Timestamp], Optional[float]]],
    same_minute_resolution: str,
    cost_stress: str,
    seed: int,
    fade_telemetry_out: list,
) -> list[tuple[Any, dict]]:
    """Walk every open lot's minute path up to ``until_ts``; close on bracket hits.

    Returns ``[(exit_event, trade_dict), ...]`` for every lot closed within the
    window so the caller can record per-event log rows.

    The lots are snapshotted before iteration because :meth:`Portfolio.close_
    position_by_id` mutates ``open_positions``. ``bars_by_lot`` is keyed by
    ``position_id`` so a lot that re-enters in a later session can hold its own
    minute fixture distinct from an earlier lot of the same symbol.
    """
    exits_cfg = cfg.get("exits") or {}
    closes: list[tuple[Any, dict]] = []
    for pos in list(portfolio.open_positions.values()):
        entry_session = pos.entry_session or pos.entry_date
        if session_date < entry_session:
            continue
        bars = bars_by_lot.get(pos.position_id)
        if bars is None or len(bars) == 0:
            continue
        ev = walk_lot_exit(
            pos, bars,
            exit_cfg=exits_cfg,
            same_minute_resolution=str(same_minute_resolution),
            cost_stress=cost_stress,
            quote_supplier=quote_supplier,
            signal_score_fn=signal_score_fn,
            seed=seed,
            fade_telemetry_out=fade_telemetry_out,
            until_ts=until_ts,
        )
        if ev is None:
            continue
        trade = portfolio.close_position_by_id(
            ev.position_id or pos.position_id,
            exit_price=ev.exit_price,
            exit_reason=ev.exit_reason,
            exit_date=ev.exit_date,
            exit_event=ev,
        )
        closes.append((ev, trade))
    return closes


def _build_dq_report_with_optional_cache(
    *,
    cached_invariant_report: Optional[Mapping[str, Any]],
    cfg: Mapping[str, Any],
    dataset_lineage: Mapping[str, Any],
    requested_symbols: list[str],
    sessions: list[_dt.date],
    daily_bars_supplier,
    minute_bars_supplier,
    scan_times_per_session,
    daily_cache_by_session,
    session_minute_supplier,
    cache_key_symbols: Optional[list[str]] = None,
    reuse_cached_invariant_only: bool = False,
) -> dict[str, Any]:
    """Build the DQ report — using the cached invariant half when available.

    Speedup report v2 §4 P4 / §5.6 / Phase 3 task 3/4. When
    ``cached_invariant_report`` is non-None and its ``_cache_key`` matches the
    live values, only the trial-dependent half is recomputed and the two
    halves are merged via :func:`merge_dq_reports`. On any mismatch the cache
    is silently bypassed (legacy full rebuild, with a logged warning) — the
    safer fallback. The result is bit-equivalent to the un-cached path for
    runs against the same lake / config family.
    """
    # Use module-level ``build_data_quality_report`` so ``patch.object(
    # backtester, "build_data_quality_report", ...)`` in tests reaches both
    # the full-rebuild and the trial-dependent paths.
    import hashlib as _hashlib
    import logging as _logging
    import sys as _sys

    from ..utils.profile_counters import counters_enabled, current_profile_counters

    _log = _logging.getLogger("bowaka_v2_lab.sim.backtester")

    def _build_dq(*, classify_filter: Optional[str] = None) -> dict[str, Any]:
        """Module-level dispatch — picks up ``patch.object`` rebinds on this module."""
        mod = _sys.modules[__name__]
        return mod.build_data_quality_report(
            cfg=cfg, lineage=dataset_lineage,
            requested_symbols=requested_symbols, sessions=sessions,
            daily_bars_supplier=daily_bars_supplier,
            minute_bars_supplier=minute_bars_supplier,
            scan_times_per_session=scan_times_per_session,
            daily_cache_by_session=daily_cache_by_session,
            session_minute_supplier=session_minute_supplier,
            classify_filter=classify_filter,
        )

    def _bump(field: str) -> None:
        if counters_enabled():
            try:
                current_profile_counters().inc(**{field: 1})
            except LookupError:
                pass

    def _full_rebuild() -> dict[str, Any]:
        _bump("startup_dq_builds")
        return _build_dq()

    if cached_invariant_report is None:
        return _full_rebuild()

    cache_key = cached_invariant_report.get("_cache_key") or {}
    md = cfg.get("market_data") or {}
    sim = cfg.get("simulation") or {}
    # The stamp side (fold_context) keys the cache on the per-fold ELIGIBLE
    # symbol union. ``requested_symbols`` here is derived from
    # ``universe_snapshot_by_session`` via ``u.get("symbols")``, which is EMPTY
    # for the raw ``{symbol: record}`` PIT shape — so keying on it never matched
    # the stamp and the invariant DQ report was rebuilt every fold. Prefer the
    # caller-supplied ``cache_key_symbols`` (the eligible union, computed
    # shape-robustly via ``dq_cache_symbol_set``); fall back to the legacy
    # ``requested_symbols`` only when it is not provided.
    _key_symbols = cache_key_symbols if cache_key_symbols is not None else requested_symbols
    symbols_hash = _hashlib.sha256(
        ",".join(sorted(_key_symbols)).encode("utf-8")
    ).hexdigest()[:16]
    # Lake-root hotfix 2026-05-29 — route through the helper so the
    # dataset_lineage fallback honoured for replay paths is coerced;
    # a buggy value (None or Path('None')) raises here instead of silently
    # producing empty suppliers downstream. Avoids touching
    # cfg['market_data'].get('shared_root') in this module so the AST
    # regression test in tests/unit/optuna/ keeps catching new bypasses.
    from ..data.lineage import resolve_lake_root_with_dataset_lineage_fallback

    lake_root_str = str(
        resolve_lake_root_with_dataset_lineage_fallback(cfg, dataset_lineage)
    )
    expected_key = {
        "lake_root": lake_root_str,
        "feed": str(md.get("feed", "iex")),
        "symbols_hash": symbols_hash,
        "sessions": [s.isoformat() for s in sessions],
        "simulation_mode": (sim.get("mode") if isinstance(sim, dict) else None),
        "market_data_keys": {
            "require_adjusted_daily_bars": md.get("require_adjusted_daily_bars"),
            "require_split_adjustment": md.get("require_split_adjustment"),
            "max_bar_age_seconds": md.get("max_bar_age_seconds"),
            "max_quote_age_seconds": md.get("max_quote_age_seconds"),
        },
        "dq_check_invariance_version": DQ_CHECK_INVARIANCE_VERSION,
    }
    for k, expected in expected_key.items():
        if cache_key.get(k) != expected:
            _log.warning(
                "startup_dq_cache miss on field %r (expected %r, got %r); "
                "rebuilding the full DQ report",
                k, expected, cache_key.get(k),
            )
            return _full_rebuild()

    # Cache key matches.
    _bump("startup_dq_cached_hits")
    invariant_half = dict(cached_invariant_report)
    invariant_half.pop("_cache_key", None)  # drop the bookkeeping field
    if reuse_cached_invariant_only:
        # Per-trial speedup: the expensive part of the DQ build is RE-READING
        # the per-fold daily bars (~36k parquet reads), and the trial-dependent
        # checks re-read them too — so caching only the invariant *checks* saves
        # nothing. In a mode where the trial-dependent checks neither gate the
        # run (current_code_parity / smoke_fixture gate ONLY on the invariant
        # adjustment checks — see ``evaluate_startup_dq``) nor get persisted
        # (objective_minimal), the whole trial-dependent rebuild is skipped and
        # the cached invariant report is reused as-is. The objective is
        # DQ-independent in these modes (A/B parity:
        # scripts/_ab_dq_cache.py + tests), so this is observationally inert
        # for the per-trial result while removing the ~81%-of-wall-clock reads.
        return invariant_half
    # Otherwise recompute only the trial-dependent half and merge.
    trial_half = _build_dq(classify_filter="trial_dependent")
    return merge_dq_reports(invariant_half, trial_half)


def run_backtest(
    *,
    cfg: Mapping[str, Any],
    sessions: list[_dt.date],
    scan_times_per_session: Callable[[_dt.date], list[Any]],
    universe_snapshot_by_session: Mapping[_dt.date, Any],
    daily_cache_by_session: Mapping[_dt.date, pd.DataFrame],
    minute_bars_supplier: Callable[[str, Any], pd.DataFrame | None],
    daily_bars_supplier: Callable[[str, _dt.date], pd.DataFrame | None],
    quote_supplier: Optional[Callable[..., Optional[dict]]] = None,
    forward_minute_supplier: Optional[Callable[[str, Any], pd.DataFrame | None]] = None,
    # Realism Phase 7: returns the FULL regular-session minute bars for a
    # ``(symbol, session_date)`` — the path the per-lot minute exit walk
    # consumes. When omitted the minute exit driver falls back to the ordinary
    # ``minute_bars_supplier`` queried at the 16:00 ET close.
    session_minute_supplier: Optional[Callable[[str, _dt.date], pd.DataFrame | None]] = None,
    # Realism remediation 2 Phase 5 (audit P0-009): venue-status supplier for
    # the halt gate. ``status_supplier(symbol, ts) -> dict|None``; ``None``
    # means no status data (current_code_parity warns + fails-open;
    # intended_realism rejects with ``halt_data_unavailable``).
    status_supplier: Optional[Callable[..., Optional[dict]]] = None,
    volume_curve: Optional[pd.DataFrame] = None,
    initial_bankroll: float = 100_000.0,
    paths: Optional[BowakaV2Paths] = None,
    run_dir: Optional[Path] = None,
    code_paths_for_manifest: Optional[list[Path]] = None,
    # Speedup report §5.1 / §11.2 Phase 1 — ``"objective_minimal"`` runs the
    # full simulation/event/portfolio/fill/exit/daily-equity logic but skips
    # every disk artifact write (parquet, jsonl, json, markdown, the
    # promotion checklist, the suitability decision, the report renderer)
    # — only the in-memory :class:`BacktestResult` is returned. Default
    # ``"full"`` preserves every existing call site verbatim.
    artifact_mode: Literal["full", "objective_minimal"] = "full",
    # Speedup report v2 §4 P4 / §5.6 / Phase 3 task 3 — when supplied, the
    # invariant half of the DQ report is reused (its ``_cache_key`` is
    # verified against this run's lake/feed/symbols/sessions/sim_mode/
    # market_data flags + DQ_CHECK_INVARIANCE_VERSION). Only the
    # trial-dependent half is recomputed for this trial; mismatch falls back
    # to the legacy full rebuild with a logged warning. Default ``None``
    # preserves the legacy path verbatim.
    startup_dq_report: Optional[Mapping[str, Any]] = None,
    # Speedup report v2 §6.1 / Phase 3 — when supplied AND the resolved
    # runtime_mode is "compatibility", the SCAN handler reads per-symbol
    # features from this read-only scan-matrix store (per session partition)
    # instead of re-fetching/aggregating bars, then runs the EXISTING gate /
    # score / event-builder path so candidate events are bit-identical to the
    # legacy scanner. Default ``None`` preserves the legacy path verbatim.
    scan_matrix_store: Optional[Any] = None,
) -> BacktestResult:
    """Run a complete v2 backtest.

    ``artifact_mode="full"`` (default) writes the 16-file artifact contract
    and runs the promotion checklist + suitability decision.
    ``artifact_mode="objective_minimal"`` runs the same simulation but
    suppresses every disk write — used by the Optuna walk-forward objective
    where artifacts are not consumed. Both modes populate the in-memory
    :class:`BacktestResult` with everything the objective needs."""
    if paths is None:
        repo_root = Path(__file__).resolve().parents[5]
        paths = BowakaV2Paths.default(repo_root)
    paths.assert_strategy_isolation()

    cfg_dict = dict(cfg)
    # Resolve the simulation-mode contract (parity / realism / smoke). The
    # post-validator fills the four mode-coupled policy fields, so every field
    # is concrete for the manifest and report header.
    sim_cfg = SimulationConfig.model_validate(cfg_dict.get("simulation") or {})
    # Realism Phase 3: normalise the per-session universe. Accepts either the
    # legacy snapshot dict or the PIT {symbol: UniverseRecord} map; refuses a
    # synthetic universe in a non-smoke run. ``pit_records_by_session`` is the
    # subset supplied as real PIT records — universe artifacts are written for
    # exactly those sessions.
    universe_snapshot_by_session, pit_records_by_session = _normalise_universe_by_session(
        universe_snapshot_by_session, sim_mode=sim_cfg.mode
    )
    strategy_hash = canonical_strategy_hash(cfg_dict)
    run_hash = canonical_run_hash(cfg_dict)

    # Realism Phase 2: content-derived dataset hash + lineage. The hash is a
    # deterministic function of the actual market data the run consumes (lake
    # partition sizes, lake manifest hash, symbol universe, date range), so two
    # runs over the same lake + config hash identically and a mutated parquet
    # changes the hash. Synthetic / smoke runs get a stable logical hash.
    requested_symbols = sorted(
        {s["symbol"] for u in universe_snapshot_by_session.values() for s in u.get("symbols", [])}
    )
    # Per-trial speedup: the startup_dq_cache key is the per-fold ELIGIBLE symbol
    # union, computed shape-robustly so it matches the stamp side (fold_context)
    # regardless of whether the universe arrives as the raw {symbol: record} PIT
    # form or the scanner-snapshot {"symbols": [...]} form. ``requested_symbols``
    # above is EMPTY for the raw form (``.get("symbols")`` is absent there), so it
    # cannot be used to key the cache. ``requested_symbols`` is still used for the
    # dataset lineage below (unchanged — this only fixes the cache key).
    from ..universe.builder import dq_cache_symbol_set

    cache_key_symbols = dq_cache_symbol_set(universe_snapshot_by_session)
    date_start = sessions[0] if sessions else None
    date_end = sessions[-1] if sessions else None
    dataset_lineage = build_dataset_lineage(
        cfg=cfg_dict,
        symbols=requested_symbols,
        start=date_start,
        end=date_end,
        lab_config_hash=strategy_hash,
    )
    dataset_hash = dataset_lineage["dataset_hash"]
    dataset_provider = dataset_lineage["provider"]
    # generate_run_id needs a short plain-hex token (no "sha256:" prefix — colons
    # are invalid in Windows paths). The full content hash goes in the manifest.
    run_id = generate_run_id(
        kind="backtest", cfg_hash=strategy_hash, dataset_hash=dataset_hash
    )

    if run_dir is None:
        run_dir = paths.artifact_root / "runs" / run_id
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Realism Phase 2: substantive data-quality report. Lake-backed runs get
    # audit-derived + coverage + adjustment + quote checks; synthetic runs get a
    # labelled non-fatal check set. Data quality is a *precondition* for a
    # meaningful run, so it is gated before the config-parity diff: in
    # intended_realism mode a failed *required* check (coverage, adjustment
    # mismatch, missing quotes) fails the run closed before the parity diff and
    # the heavy run loop. The precise reason is recorded in the run manifest and
    # the CLI exits non-zero. smoke_fixture / current_code_parity runs are never
    # failed by DQ — the report is still written for them.
    data_quality_report = _build_dq_report_with_optional_cache(
        cached_invariant_report=startup_dq_report,
        cfg=cfg_dict,
        dataset_lineage=dataset_lineage,
        requested_symbols=requested_symbols,
        sessions=sessions,
        daily_bars_supplier=daily_bars_supplier,
        minute_bars_supplier=minute_bars_supplier,
        scan_times_per_session=scan_times_per_session,
        daily_cache_by_session=daily_cache_by_session,
        session_minute_supplier=session_minute_supplier,
        cache_key_symbols=cache_key_symbols,
        # Per-trial speedup: in the per-trial objective path (objective_minimal)
        # under a mode that gates only on the invariant adjustment checks
        # (current_code_parity / fast_realism / smoke_fixture), reuse the cached
        # invariant DQ report and skip the trial-dependent rebuild's redundant
        # daily-bar reads. Full-artifact runs and intended_realism keep the
        # complete report (the latter gates on trial-dependent checks too).
        # §10i Path 4 — fast_realism gates ONLY on adjustment (invariant), so it
        # reuses the cached invariant report; this keeps the SEARCH stage fast.
        reuse_cached_invariant_only=(
            artifact_mode == "objective_minimal"
            and sim_cfg.mode in ("current_code_parity", "fast_realism", "smoke_fixture")
        ),
    )
    if artifact_mode == "full":
        atomic_write_json(run_dir / "data_quality_report.json", data_quality_report)
    startup_dq_failure = evaluate_startup_dq(
        data_quality_report, simulation_mode=sim_cfg.mode
    )
    if startup_dq_failure is not None:
        # Record the precise rejection reason in the run manifest, then abort.
        feed = (cfg_dict.get("market_data") or {}).get("feed", "iex")
        if artifact_mode == "full":
            failure_manifest = build_run_manifest(
                strategy_id="bowaka_v2",
                strategy_version=str(cfg_dict.get("strategy_version", "0.1.0")),
                run_id=run_id, config_hash=strategy_hash, dataset_hash=dataset_hash,
                code_manifest_hash="(aborted before code manifest)",
                run_kind="backtest", feed=feed,
                extras={
                    "run_hash": run_hash,
                    "simulation": sim_cfg.model_dump(),
                    "startup_dq_failure": startup_dq_failure,
                    "dataset_lineage": {
                        k: v for k, v in dataset_lineage.items() if k != "lake_manifest"
                    },
                },
            )
            atomic_write_json(run_dir / "run_manifest.json", failure_manifest)
        # Speedup report §4 P0-A / §5.1: a generic RuntimeError was swallowed by
        # the Optuna runner's broad ``except Exception`` block in
        # ``_run_validation_folds`` and degraded the fold to a sentinel score.
        # ``StartupDataQualityError`` is a ``DataQualityError`` subclass — it is
        # structural; the runner re-raises it to abort the study cleanly.
        raise StartupDataQualityError(startup_dq_failure)

    # Config-parity diff vs the frozen live contract (realism Phase 1). Written
    # on every run; in intended_realism mode an unannotated `mismatch` aborts
    # the run at startup, before the run loop produces any further artifacts.
    # In objective_minimal mode the diff is computed only when the realism
    # gate is active (so unannotated mismatches still abort) — the file write
    # itself is suppressed.
    if contract_available():
        if artifact_mode == "full":
            _diff_path, _diff_rows = write_config_diff(
                run_dir, cfg_dict, load_actual_contract(),
                config_path=cfg_dict.get("_source_path"),
            )
        else:
            # objective_minimal — compute the diff in-memory only (no file
            # write) so the realism unannotated-mismatch gate still fires.
            from ..config.config_diff import build_config_diff, load_parity_overrides

            _overrides = load_parity_overrides(cfg_dict.get("_source_path"))
            _diff_rows = build_config_diff(
                cfg_dict, load_actual_contract(),
                intentional_overrides=_overrides,
            )
        if sim_cfg.mode == "intended_realism":
            _unannotated = unannotated_mismatches(_diff_rows)
            if _unannotated:
                raise RuntimeError(
                    f"intended_realism run aborted: config_diff_vs_actual_bowaka_v2.yaml "
                    f"has {len(_unannotated)} unannotated mismatch(es) vs the live contract: "
                    f"{sorted(_unannotated)}. Reconcile the config, or declare each as an "
                    f"intentional override in the parity sidecar (<config>.parity.yml)."
                )
    elif artifact_mode == "full":
        # No frozen contract on this host — emit a placeholder so the artifact
        # contract still holds. Realism mode cannot be parity-gated; that is
        # surfaced rather than silently skipped.
        write_empty_config_diff(
            run_dir, note="frozen contract unavailable; parity diff not computed"
        )

    portfolio = Portfolio(initial_bankroll=initial_bankroll)
    broker = SimulatedBroker()
    from .strategy_consumer import StrategyConsumer
    consumer = StrategyConsumer(portfolio=portfolio, broker=broker, cfg=cfg_dict)

    all_candidate_events: list[dict] = []
    all_gate_dump: list[dict] = []
    all_decisions: list[dict] = []
    all_orders: list[dict] = []
    all_fills: list[dict] = []
    all_positions: list[dict] = []
    all_trades: list[dict] = []
    daily_equity: list[dict] = []
    ambiguous_bar_count = 0
    # Realism Phase 7: signal-fade telemetry — would-have-exited events recorded
    # under telemetry_only mode (the lot is NOT closed). Surfaced in the report.
    all_fade_telemetry: list[Any] = []
    # Realism Phase 6: per-candidate execution-quality fill records, the
    # missing-quote reject count and per-(symbol, scan_ts) quote-coverage rows.
    all_fill_records: list[dict] = []
    missing_quote_count = 0
    quote_coverage_rows: list[dict] = []
    # Realism Phase 4: per-session scan-count + funnel summary for the run
    # manifest. Records the cadence the calendar-aware scheduler produced and
    # the accept / reject breakdown for each session.
    scan_counts: dict[str, dict[str, Any]] = {}
    # Realism remediation 2 Phase 4: per-event log rows + per-session-cap
    # rollover info. ``all_event_log_rows`` carries the cross-session log (one
    # row per dispatched event with the portfolio snapshot at the end of the
    # event). Sessions whose row count exceeds ``_EVENTS_PER_SESSION_CAP`` are
    # written FULL to ``events/by_session/<session>.parquet``; the canonical
    # ``events/events.parquet`` carries the per-session-capped rollup.
    all_event_log_rows: list[dict] = []
    event_log_by_session: dict[str, list[dict]] = {}
    # Realism remediation 2 Phase 4: the four poll cadences are decoupled and
    # resolved once per run (audit P1-009). All four default to the live
    # contract: scan=60s, fill=5s, protection=5s, time_stop=60s.
    cadence = CadenceConfig.from_cfg(cfg_dict)
    # Speedup report §6.3 / §11.2 Phase 6 — lazy event scheduling is
    # default-off scaffolding; the on-demand handler hooks that schedule
    # PROTECTION_CHECK / QUOTE / TIME_STOP_CHECK events are not yet wired
    # into the dispatch loop. Refuse the opt-in until the parity matrix
    # at tests/parity/test_lazy_event_scheduling_parity.py proves
    # identical FoldResults to the preload variant.
    if cadence.cadence_strategy == "lazy":
        raise RuntimeError(
            "cadence_strategy='lazy' is reserved for the Phase 6 lazy "
            "scheduler; the on-demand handler hooks are not yet wired in "
            "this build. Default 'preload' must be used until the Phase 6 "
            "parity matrix proves identical FoldResults (speedup report §6.3)."
        )
    # Speedup report §6.4 / matrix doc §17.2 Phase 9 — scan-matrix runtime
    # opt-in is default-off scaffolding (Phase 8 ships the builder; Phase 9
    # wires the runtime evaluator). The runtime guard refuses the opt-in
    # until the matrix-vs-legacy parity matrix proves bit-identical
    # FoldResults; the legacy scanner path is the only path in this build.
    _matrix_enabled_flag = bool(
        ((cfg_dict.get("optuna") or {}).get("acceleration") or {})
        .get("scan_matrix", {}).get("enabled", False)
    )
    _runtime_mode = "disabled"
    if _matrix_enabled_flag:
        from ..scanner.scan_matrix_runtime import (
            assert_backtester_matrix_opt_in_is_supported,
            resolve_runtime_mode,
        )

        # Speedup report v2 §4 P6 / §6.1 / Phase 3-4 — three-mode resolution.
        # ``runtime_mode='disabled'`` (the default) lets the matrix be built
        # for inspection without firing the runtime path. ``compatibility``
        # is accepted in Phase 3; ``vectorized`` is accepted in Phase 4 when
        # the parity proof records verifier_version >= 2.
        _runtime_mode = resolve_runtime_mode(cfg_dict)
        _parity_present = bool(
            ((cfg_dict.get("optuna") or {}).get("acceleration") or {})
            .get("scan_matrix", {}).get("require_parity_manifest", True)
        )
        _parity_proof_version: Optional[int] = None
        if scan_matrix_store is not None:
            try:
                _proof_path = Path(scan_matrix_store.root) / "parity_proof.json"
                if _proof_path.is_file():
                    _proof = json.loads(_proof_path.read_text(encoding="utf-8"))
                    _parity_proof_version = int(_proof.get("verifier_version", 0))
            except Exception:  # noqa: BLE001 — missing/corrupt proof -> None
                _parity_proof_version = None
        assert_backtester_matrix_opt_in_is_supported(
            enabled=True,
            runtime_mode=_runtime_mode,
            parity_manifest_present=_parity_present,
            parity_proof_version=_parity_proof_version,
        )
    # Speedup report v2 §6.1 / Phase 3-4 — the matrix runtime is active only
    # when a matrix store was supplied AND runtime_mode is compatibility or
    # vectorized.
    _matrix_compat_active = (
        scan_matrix_store is not None
        and _runtime_mode in ("compatibility", "vectorized")
    )

    # Realism remediation 2 Phase 6 (audit P0-007) — protected-position
    # lifecycle. The state machine wires PARENT_FILL → OCO_ATTACH_ATTEMPT →
    # PROTECTED (or → UNPROTECTED_VIOLATION → fallback/flatten/entries_blocked
    # under stress). Disabled for ``smoke_fixture`` runs (they go through the
    # daily-bar exit driver, no event loop).
    protection_cfg_obj = ProtectionConfig.from_cfg(cfg_dict)
    protection_sm = ProtectionStateMachine(
        cfg=protection_cfg_obj,
        run_seed=int((cfg_dict.get("run") or {}).get("seed", 0)),
    )

    for session_date in sessions:
        portfolio.begin_session(session_date)
        # Per [Report §9.6]: open positions block re-entry by the same symbol.
        # The scanner's ``entered_symbols_today`` set acts as that block.
        # Realism Phase 4: the scanner dedup memory (cooldown, per-day entry
        # count, in-play pool) is *per session* — a fresh state dict each
        # session so a symbol's cooldown / day-cap never leaks across days.
        # Realism Phase 5: open_positions is keyed by position_id, so the
        # scanner's per-session entered-symbols memory is the SET OF SYMBOLS
        # across all open lots — fresh each session (begin_session already
        # recomputed portfolio.state.entered_symbols_today from this session's
        # lots; the scanner memory starts empty so prior-day lots never block
        # a new-session re-entry through the scanner dedup path).
        state: dict[str, Any] = {
            "entered_symbols_today": [],
            "in_play_pool": {},
            "symbol_last_emit_ts": {},
            # Realism remediation 2 Phase 7 (audit P1-003): the scanner-dedup
            # emit counter is ``signal_emits_per_symbol_today``; portfolio
            # PARENT_FILL counts live on Portfolio.state (entries_per_symbol_today
            # is rolled into the report from there, NOT from scanner state).
            "signal_emits_per_symbol_today": {},
        }
        universe = universe_snapshot_by_session.get(session_date)
        daily_cache = daily_cache_by_session.get(session_date)
        session_key = (
            session_date.isoformat()
            if isinstance(session_date, _dt.date)
            else str(session_date)
        )
        # Realism Phase 4: every session records its scan cadence, even one
        # skipped for a missing universe / daily cache (actual=0).
        session_scan_times = list(scan_times_per_session(session_date))
        sess_count: dict[str, Any] = {
            "expected_scans": len(session_scan_times),
            "actual_scans": 0,
            "candidate_count": 0,
            "accepted_count": 0,
            "gate_rejection_breakdown": {},
        }
        scan_counts[session_key] = sess_count
        if universe is None or daily_cache is None:
            continue

        # Speedup report §5.4 / §11.2 Phase 4 — precompute the per-session
        # scan context (universe_meta_by_sym, cache_by_sym, config_hash_v,
        # volume_curve_fraction_by_scan_bucket) ONCE per session. The legacy
        # per-scan rebuilds are replaced by a context lookup inside
        # ``evaluate_one_scan``. In ``objective_minimal`` mode the per-symbol
        # gate-dump rows are replaced with bounded rejection counters
        # (collect_gate_dump=False); full mode keeps the dump for forensics.
        collect_gate_dump = (artifact_mode == "full")
        # §10h opt #1 — the per-event event-log rows (built by ``_log_event``
        # below, ~185k rows/fold) are consumed ONLY by the events.parquet writes,
        # which are gated to ``artifact_mode == "full"``. In ``objective_minimal``
        # (the per-trial path) the whole log is built then discarded — profiled at
        # ~6% of the fold (cumtime). Skip the construction in minimal mode; full
        # mode is byte-for-byte unchanged. ``event_log`` feeds no
        # signal/objective/summary/BacktestResult path (verified).
        collect_event_log = (artifact_mode == "full")
        scan_session_ctx = build_scan_session_context(
            cfg_dict, daily_cache, universe, session_scan_times,
            volume_curve=volume_curve, collect_gate_dump=collect_gate_dump,
        )
        # Speedup report v2 §6.1 / Phase 3 — open this session's matrix
        # partition when the compatibility runtime is active. A holdout
        # session opened under purpose="objective" raises
        # HoldoutMatrixReadError (propagated — never caught). A missing
        # partition falls back to the legacy scanner for that session.
        matrix_session_partition = None
        if _matrix_compat_active:
            try:
                matrix_session_partition = scan_matrix_store.open_session(
                    session_date, purpose="objective",
                )
            except FileNotFoundError:
                matrix_session_partition = None
                # §10g per-scan-speed audit: a missing matrix partition under an
                # active matrix runtime silently degrades to the (far slower)
                # per-scan recompute path. Surface it LOUDLY (once) + count every
                # miss so an operator running on a window the matrix doesn't
                # cover sees the perf cliff instead of an unexplained slowdown.
                global _MATRIX_MISS_WARNED
                if not _MATRIX_MISS_WARNED:
                    _log.warning(
                        "scan_matrix runtime active but NO matrix partition for "
                        "session %s — falling back to per-scan recompute (SLOW). "
                        "Build the matrix for this study window "
                        "(rebuild_scan_matrices) or expect a much slower run. "
                        "This warning fires once; the matrix_session_miss counter "
                        "tallies every miss.",
                        session_date,
                    )
                    _MATRIX_MISS_WARNED = True
                if _profile_counters_enabled():
                    try:
                        _profile_counters_current().inc(matrix_session_miss=1)
                    except LookupError:
                        pass

        # Realism remediation 2 Phase 4: ROUTING by simulation mode.
        # ``smoke_fixture`` retains the pre-Phase-4 batch-scan-then-exits flow
        # so the smoke suite stays fast and deterministic. The realism
        # contracts (``current_code_parity`` / ``intended_realism``) drive an
        # event-driven dispatch loop where every event mutates ``Portfolio.state``
        # before the next event sees it (audit P0-002).
        closes_today: dict[str, float] = {}
        if sim_cfg.mode == "smoke_fixture":
            # ---- Smoke path (unchanged) -----------------------------------
            # Phase 4 leaves this path on the daily-bar exit driver so the
            # broad smoke / unit suites do not pay the per-minute walk. The
            # ``drive_session_exits_daily`` helper is locked to smoke mode in
            # the audit-acceptance test ``test_event_driven_*``.
            for scan_ts in session_scan_times:
                scan_result, consumer_results = run_one_scan(
                    cfg=cfg_dict, universe_snapshot=universe, daily_cache=daily_cache,
                    volume_curve=volume_curve, state=state, scan_ts=scan_ts,
                    bars_supplier=minute_bars_supplier, consumer=consumer,
                    quote_supplier=quote_supplier,
                    forward_minute_supplier=forward_minute_supplier,
                    status_supplier=status_supplier,
                    scan_context=scan_session_ctx,
                    collect_gate_dump=collect_gate_dump,
                )
                all_candidate_events.extend(scan_result.emitted)
                all_gate_dump.extend(scan_result.gate_dump)
                quote_coverage_rows.extend(scan_result.quote_coverage)
                sess_count["actual_scans"] += 1
                sess_count["candidate_count"] += len(scan_result.emitted)
                breakdown = sess_count["gate_rejection_breakdown"]
                for row in scan_result.gate_dump:
                    reason = row.get("rejection_reason")
                    if reason:
                        breakdown[reason] = breakdown.get(reason, 0) + 1
                # Speedup §5.4 — when collect_gate_dump=False the per-symbol
                # rows are replaced with bounded counters; merge them so the
                # session funnel still totals correctly.
                for reason, n in scan_result.rejection_counts.items():
                    breakdown[reason] = breakdown.get(reason, 0) + int(n)
                for cr in consumer_results:
                    all_decisions.extend(cr.decisions)
                    sess_count["accepted_count"] += sum(
                        1 for d in cr.decisions if d.get("decision") == "accepted"
                    )
                    all_fill_records.extend(cr.fills)
                    missing_quote_count += cr.missing_quote_count
                    for po in cr.parent_orders:
                        all_orders.append({
                            "parent_order_id": po.parent_order_id,
                            "symbol": po.symbol,
                            "side": po.plan.side.value,
                            "order_style": po.plan.order_style,
                            "qty": po.plan.qty,
                            "status": po.status.value,
                            "filled_qty": po.filled_qty,
                            "avg_fill_price": po.avg_fill_price,
                            "created_at": po.created_at,
                            "candidate_event_id": po.candidate_event_id,
                        })
                    for fr in cr.fills:
                        all_fills.append({
                            "parent_order_id": fr["parent_order_id"],
                            "symbol": fr["symbol"],
                            "order_style": fr["order_style"],
                            "filled": fr["filled"],
                            "filled_qty": fr["filled_qty"],
                            "requested_qty": fr["requested_qty"],
                            "avg_fill_price": fr["avg_fill_price"] if fr["filled"] else None,
                            "notional": fr["notional"] if fr["filled"] else None,
                            "slippage_bps": fr["slippage_bps"],
                            "is_partial": fr["is_partial"],
                            "reason": fr["reason"],
                            "commission": fr["commission"],
                            "regulatory_fees": fr["regulatory_fees"],
                            "quote_source": fr["quote_source"],
                        })
            exit_out = drive_session_exits_daily(
                portfolio, session_date, cfg=cfg_dict,
                daily_bars_supplier=daily_bars_supplier,
            )
            closes_today = exit_out.get("closes", {})
            ambiguous_bar_count += int(exit_out.get("ambiguous", 0))
            all_trades.extend(exit_out.get("trades", []))
            portfolio.update_mtm(closes_today)
            # Realism remediation 2 Phase 7 (audit P1-003) — record BOTH
            # counters per session (scanner emits + portfolio entries) so the
            # run report can surface them side-by-side. Smoke path mirrors the
            # event-driven path.
            sess_count["signal_emits_per_symbol_today"] = dict(
                state.get("signal_emits_per_symbol_today") or {}
            )
            sess_count["entries_per_symbol_today"] = dict(
                (portfolio.state.entries_per_symbol_today or {})
                if portfolio.state is not None
                else {}
            )
        else:
            # ---- Event-driven path (Phase 4) ------------------------------
            # Replaces the pre-Phase-4 "for scan_ts in session_scan_times:
            # ... then exits after the loop" with a min-heap dispatch loop
            # that interleaves SCAN, MINUTE_BAR (exit-walk), PROTECTION_CHECK,
            # TIME_STOP_CHECK and EOD_MARK in chronological order. A SCAN at
            # 10:05 sees the realized PnL from a 09:55 stopout, so the kill
            # switch / consecutive-stopout / gross-exposure gates evaluate on
            # the same state the live strategy would have observed.
            sess_acc = _SessionAccumulators()
            sess_fade_score_fn = _build_fade_score_fn(
                cfg=cfg_dict, daily_cache=daily_cache, volume_curve=volume_curve,
                minute_bars_supplier=minute_bars_supplier,
                session_minute_supplier=session_minute_supplier,
            )
            same_minute = (
                ((cfg_dict.get("simulation") or {}).get("same_minute_resolution"))
                or "conservative"
            )
            cost_stress = (cfg_dict.get("backtest") or {}).get("cost_stress", "base")
            run_seed = int((cfg_dict.get("run") or {}).get("seed", 0))

            # Preload SCAN / PROTECTION_CHECK / FILL_POLL / TIME_STOP_CHECK /
            # EOD_MARK events into a fresh queue.
            queue = EventQueue()
            queue.push_many(preload_session_events(
                session_date=session_date,
                scan_times=session_scan_times,
                cadence=cadence,
            ))

            # Cache the per-lot minute path; built lazily by position_id so a
            # second lot of the same symbol can hold its own fixture. The
            # accompanying ``next_idx_by_lot`` tracks how many bars of the lot's
            # path have already been walked, so each event walks ONLY the new
            # bars in ``(last_event_ts, event_ts]``. Without this the dispatch
            # loop would re-scan every bar of every lot on every event tick.
            bars_by_lot: dict[str, Optional[pd.DataFrame]] = {}
            next_idx_by_lot: dict[str, int] = {}
            # Per-trial speedup: cache each lot's sorted minute-bar timestamps as
            # an int64 ns-since-epoch (UTC) array ONCE, so the per-event window
            # boundary is a single np.searchsorted instead of re-parsing the
            # entire remaining bar tail (pd.to_datetime + mask.sum) on every one
            # of the ~10k poll-cadence events per session. Byte-identical
            # new-bar count (the bars are pre-sorted by _bars_for_lot).
            ts_ns_by_lot: dict[str, Optional[np.ndarray]] = {}

            def _bars_for_lot(pos: Position) -> Optional[pd.DataFrame]:
                """Resolve the regular-session minute bars for ``pos``.

                Honours :func:`drive_session_exits_minute`'s policy: prefer the
                full-session supplier, fall back to the forming-session
                supplier queried at the 16:00 close. Bars are pre-sorted by
                timestamp so the running cursor walks the path monotonically.
                """
                if pos.position_id in bars_by_lot:
                    return bars_by_lot[pos.position_id]
                bars: Optional[pd.DataFrame] = None
                if session_minute_supplier is not None:
                    try:
                        bars = session_minute_supplier(pos.symbol, session_date)
                    except Exception:  # noqa: BLE001
                        bars = None
                if (bars is None or len(bars) == 0) and minute_bars_supplier is not None:
                    close_ts = pd.Timestamp(
                        _dt.datetime.combine(session_date, _dt.time(16, 0)),
                        tz="America/New_York",
                    ).tz_convert("UTC")
                    try:
                        bars = minute_bars_supplier(pos.symbol, close_ts)
                    except Exception:  # noqa: BLE001
                        bars = None
                if bars is not None and len(bars) > 0:
                    ts_col = next(
                        (c for c in ("timestamp", "ts") if c in bars.columns), None
                    )
                    if ts_col is not None:
                        bars = bars.sort_values(ts_col).reset_index(drop=True)
                bars_by_lot[pos.position_id] = bars
                return bars

            def _close_lots_until(walk_until: pd.Timestamp, *, log_event: Optional[Event] = None) -> None:
                """Walk every open lot's NEW minute bars up to ``walk_until``.

                Each close mutates ``Portfolio.state`` immediately (per audit
                §9.2), so a later event in the same session sees the updated
                ``daily_realized_pnl`` / ``stopouts_today`` / etc. The cursor
                in :data:`next_idx_by_lot` makes the per-event walk linear in
                the new-bar count (not the whole session's bar count) so the
                event loop stays performant even at a 5-second poll cadence.
                When the caller passes ``log_event`` the resulting CHILD_FILL
                rows are tagged with that source event's timestamp + type.
                """
                # Snapshot lots ONCE so close-mutations don't break iteration.
                exits_cfg = cfg_dict.get("exits") or {}
                for pos in list(portfolio.open_positions.values()):
                    bars = _bars_for_lot(pos)
                    if bars is None or len(bars) == 0:
                        continue
                    entry_session = pos.entry_session or pos.entry_date
                    if session_date < entry_session:
                        continue
                    # Window the bars to ``(cursor, walk_until]``. The cursor
                    # advances after this event so each bar is examined once.
                    cursor = next_idx_by_lot.get(pos.position_id, 0)
                    if cursor >= len(bars):
                        continue
                    ts_col = next(
                        (c for c in ("timestamp", "ts") if c in bars.columns), None
                    )
                    if ts_col is None:
                        # No timestamp column — legacy fallback walks the whole
                        # remaining tail (matches the pre-speedup behaviour).
                        sub = bars.iloc[cursor:]
                        new_idx = cursor + len(sub)
                    else:
                        # Boundary via searchsorted on the cached ns array. The
                        # ``right`` side includes a bar whose ts == walk_until,
                        # exactly as the legacy ``sub_ts <= walk_until`` mask did.
                        ts_ns = ts_ns_by_lot.get(pos.position_id)
                        if ts_ns is None:
                            _idx = pd.DatetimeIndex(bars[ts_col])
                            _idx = (_idx.tz_localize("UTC") if _idx.tz is None
                                    else _idx.tz_convert("UTC"))
                            ts_ns = (_idx.tz_localize(None)
                                     .to_numpy(dtype="datetime64[ns]").view("int64"))
                            ts_ns_by_lot[pos.position_id] = ts_ns
                        _wu = pd.Timestamp(walk_until)
                        _wu = (_wu.tz_localize("UTC") if _wu.tzinfo is None
                               else _wu.tz_convert("UTC"))
                        new_idx = int(np.searchsorted(ts_ns, _wu.value, side="right"))
                        if new_idx <= cursor:
                            continue  # no new bars in (cursor, walk_until]
                        sub = bars.iloc[cursor:new_idx]
                    if len(sub) == 0:
                        continue
                    ev = walk_lot_exit(
                        pos, sub,
                        exit_cfg=exits_cfg,
                        same_minute_resolution=str(same_minute),
                        cost_stress=cost_stress,
                        quote_supplier=quote_supplier,
                        signal_score_fn=sess_fade_score_fn,
                        seed=run_seed,
                        fade_telemetry_out=sess_acc.fade_telemetry,
                        until_ts=walk_until,
                    )
                    if ev is None:
                        # No exit in this window — advance the cursor so the
                        # next event picks up where we left off.
                        next_idx_by_lot[pos.position_id] = new_idx
                        continue
                    # Exit fired — remove the cursor (lot is closed).
                    next_idx_by_lot.pop(pos.position_id, None)
                    if ev.ambiguous_bar_resolved:
                        sess_acc.ambiguous_count += 1
                    trade = portfolio.close_position_by_id(
                        ev.position_id or pos.position_id,
                        exit_price=ev.exit_price,
                        exit_reason=ev.exit_reason,
                        exit_date=ev.exit_date,
                        exit_event=ev,
                    )
                    sess_acc.trades.append(trade)
                    # Emit a CHILD_FILL log row at the actual exit minute.
                    exit_ts_utc = pd.Timestamp(ev.exit_timestamp) if ev.exit_timestamp else walk_until
                    if exit_ts_utc.tzinfo is None:
                        exit_ts_utc = exit_ts_utc.tz_localize("UTC")
                    child_fill = Event(
                        timestamp=exit_ts_utc,
                        type=EventType.CHILD_FILL,
                        payload={
                            "session_date": session_date,
                            "position_id": ev.position_id or pos.position_id,
                            "symbol": pos.symbol,
                            "exit_reason": ev.exit_reason,
                        },
                    )
                    _log_event(
                        sess_acc, event=child_fill, portfolio=portfolio,
                        extras={
                            "exit_price": float(ev.exit_price),
                            "trade_pnl": float(trade.get("pnl", 0.0)),
                        },
                    )

            def _handle_scan(event: Event) -> None:
                """Run one SCAN tick — gated by the live risk state.

                The pre-Phase-4 backtester called ``run_one_scan`` blindly on
                every scan ts. The realism path keeps that wiring (the scanner
                + StrategyConsumer collectively implement the entry gates) so
                signal emission stays bit-identical. Phase 4's contribution is
                that ``portfolio.state`` is now up-to-date BEFORE this call —
                a same-day stopout earlier in the loop has already updated
                ``daily_realized_pnl`` / ``stopouts_today``, so the
                ``daily_loss_pct`` / ``max_stopouts_per_day`` / consecutive-
                stopout kill switches gate this scan correctly.
                """
                scan_ts = event.timestamp
                # Speedup report v2 §6.1 / Phase 3 — dispatch the SCAN to the
                # matrix compatibility evaluator when active for this session.
                # The result is a ScanResult bit-identical to the legacy path;
                # the consumer loop is shared via run_one_scan's override.
                _matrix_scan_result = None
                if matrix_session_partition is not None:
                    if _runtime_mode == "vectorized":
                        from ..scanner.scan_matrix_vectorized import (
                            evaluate_one_scan_vectorized,
                        )
                        _matrix_scan_result = evaluate_one_scan_vectorized(
                            cfg=cfg_dict, matrix_session=matrix_session_partition,
                            scan_ts=scan_ts, state=state,
                            scan_context=scan_session_ctx,
                            universe_snapshot=universe, volume_curve=volume_curve,
                            collect_gate_dump=collect_gate_dump,
                        )
                    else:
                        from ..scanner.scan_matrix_runtime import (
                            evaluate_one_scan_compat,
                        )
                        _matrix_scan_result = evaluate_one_scan_compat(
                            cfg=cfg_dict, matrix_session=matrix_session_partition,
                            scan_ts=scan_ts, state=state,
                            scan_context=scan_session_ctx,
                            universe_snapshot=universe, volume_curve=volume_curve,
                            collect_gate_dump=collect_gate_dump,
                        )
                # Walk-forward scan-matrix speedup Phase 2 — explicit "matrix
                # fired" signal: bump once per scan the matrix actually served
                # (override produced) so a silent legacy fallthrough is
                # observable (counter stays 0).
                if _matrix_scan_result is not None and _profile_counters_enabled():
                    try:
                        _profile_counters_current().inc(matrix_scans_evaluated=1)
                    except LookupError:
                        pass
                scan_result, consumer_results = run_one_scan(
                    cfg=cfg_dict, universe_snapshot=universe, daily_cache=daily_cache,
                    volume_curve=volume_curve, state=state, scan_ts=scan_ts,
                    bars_supplier=minute_bars_supplier, consumer=consumer,
                    quote_supplier=quote_supplier,
                    forward_minute_supplier=forward_minute_supplier,
                    status_supplier=status_supplier,
                    scan_context=scan_session_ctx,
                    collect_gate_dump=collect_gate_dump,
                    scan_result_override=_matrix_scan_result,
                )
                sess_acc.candidate_events.extend(scan_result.emitted)
                sess_acc.gate_dump.extend(scan_result.gate_dump)
                sess_acc.quote_coverage.extend(scan_result.quote_coverage)
                sess_count["actual_scans"] += 1
                sess_count["candidate_count"] += len(scan_result.emitted)
                breakdown = sess_count["gate_rejection_breakdown"]
                for row in scan_result.gate_dump:
                    reason = row.get("rejection_reason")
                    if reason:
                        breakdown[reason] = breakdown.get(reason, 0) + 1
                # Speedup §5.4 — merge bounded counters when full per-symbol
                # dump rows were suppressed.
                for reason, n in scan_result.rejection_counts.items():
                    breakdown[reason] = breakdown.get(reason, 0) + int(n)
                for cr in consumer_results:
                    sess_acc.decisions.extend(cr.decisions)
                    sess_count["accepted_count"] += sum(
                        1 for d in cr.decisions if d.get("decision") == "accepted"
                    )
                    sess_acc.fill_records.extend(cr.fills)
                    sess_acc.missing_quote_count += cr.missing_quote_count
                    # Realism remediation 2 Phase 6 — drive the protection
                    # state machine for every newly-created lot. The consumer
                    # left each lot in PARENT_FILLED (realism / parity) or
                    # PROTECTED (smoke); for realism / parity we push a
                    # PARENT_FILL event into the queue so the dispatch loop
                    # honors the chronological ordering of the attach attempt
                    # vs subsequent SCAN / PROTECTION_CHECK events.
                    for pos in cr.new_positions:
                        if pos.protection_state == ProtectionState.PARENT_FILLED:
                            fill_ts = pd.Timestamp(
                                pos.parent_fill_ts or pos.entry_timestamp
                                or scan_ts
                            )
                            if fill_ts.tzinfo is None:
                                fill_ts = fill_ts.tz_localize("UTC")
                            queue.push(Event(
                                timestamp=fill_ts,
                                type=EventType.PARENT_FILL,
                                payload={
                                    "session_date": session_date,
                                    "position_id": pos.position_id,
                                    "symbol": pos.symbol,
                                    "parent_order_id": pos.parent_order_id,
                                },
                            ))
                    for po in cr.parent_orders:
                        sess_acc.orders.append({
                            "parent_order_id": po.parent_order_id,
                            "symbol": po.symbol,
                            "side": po.plan.side.value,
                            "order_style": po.plan.order_style,
                            "qty": po.plan.qty,
                            "status": po.status.value,
                            "filled_qty": po.filled_qty,
                            "avg_fill_price": po.avg_fill_price,
                            "created_at": po.created_at,
                            "candidate_event_id": po.candidate_event_id,
                        })
                    for fr in cr.fills:
                        sess_acc.fills.append({
                            "parent_order_id": fr["parent_order_id"],
                            "symbol": fr["symbol"],
                            "order_style": fr["order_style"],
                            "filled": fr["filled"],
                            "filled_qty": fr["filled_qty"],
                            "requested_qty": fr["requested_qty"],
                            "avg_fill_price": fr["avg_fill_price"] if fr["filled"] else None,
                            "notional": fr["notional"] if fr["filled"] else None,
                            "slippage_bps": fr["slippage_bps"],
                            "is_partial": fr["is_partial"],
                            "reason": fr["reason"],
                            "commission": fr["commission"],
                            "regulatory_fees": fr["regulatory_fees"],
                            "quote_source": fr["quote_source"],
                        })
                        # Realism remediation 2 Phase 5 (audit P0-006): schedule
                        # a PARENT_FILL_TIMEOUT event at ``submit_ts +
                        # timeout_seconds`` so the dispatch log reflects the
                        # timeout firing. The fill model already realized the
                        # no-fill synchronously; the event is purely a log row.
                        if (
                            not fr.get("filled")
                            and str(fr.get("reason") or "") == "marketable_limit_timeout"
                            and str(fr.get("order_style") or "") == "marketable_limit"
                        ):
                            timeout_secs = int(
                                (cfg_dict.get("execution") or {}).get(
                                    "marketable_limit_timeout_seconds", 30
                                )
                            )
                            queue.push(Event(
                                timestamp=scan_ts + pd.Timedelta(seconds=timeout_secs),
                                type=EventType.PARENT_FILL_TIMEOUT,
                                payload={
                                    "session_date": session_date,
                                    "parent_order_id": fr["parent_order_id"],
                                    "symbol": fr["symbol"],
                                },
                            ))

            # Dispatch. Walk lots up to each event's timestamp BEFORE handling
            # the event so an intraday stop is realized in Portfolio.state
            # before the next SCAN runs (audit P0-002 fix).
            while not queue.empty():
                event = queue.pop()
                if _profile_counters_enabled():
                    try:
                        _profile_counters_current().inc(event_count_processed=1)
                    except LookupError:
                        pass
                # Phase 6 reserved: PROTECTION_CHECK / OCO_ATTACH_ATTEMPT
                # become first-class lifecycle steps. Phase 4 treats them as
                # poll-tick markers and uses them to evaluate exits up to now.
                # Phase 7 reserved: SIGNAL_FADE_CHECK splits out of the lot
                # walk into its own event so a fade event is independently
                # logged and dispatched. Phase 4 keeps fade integrated.
                _close_lots_until(event.timestamp, log_event=event)
                # Realism remediation 2 Phase 6 — protection-state-machine
                # event handlers. Tracks per-event ``log_extras`` so the
                # event-log row can carry the success / failure markers.
                log_extras: dict[str, Any] = {}
                if event.type == EventType.SCAN:
                    _handle_scan(event)
                elif event.type == EventType.PARENT_FILL:
                    # Phase 6 task 2 — schedule the first OCO_ATTACH_ATTEMPT.
                    pid = event.payload.get("position_id")
                    pos = portfolio.open_positions.get(pid)
                    if pos is not None and pos.protection_state in (
                        ProtectionState.PARENT_FILLED,
                        ProtectionState.PARENT_ACKNOWLEDGED,
                    ):
                        step = protection_sm.on_parent_fill(
                            pos, event.timestamp,
                            portfolio=portfolio, queue=queue,
                            session_date=session_date,
                        )
                        log_extras.update(step.log_extras)
                elif event.type == EventType.OCO_ATTACH_ATTEMPT:
                    pid = event.payload.get("position_id")
                    attempt_index = int(event.payload.get("attempt_index", 0))
                    pos = portfolio.open_positions.get(pid)
                    if pos is not None:
                        step = protection_sm.on_oco_attach_attempt(
                            pos, event.timestamp,
                            portfolio=portfolio, queue=queue,
                            session_date=session_date,
                            attempt_index=attempt_index,
                        )
                        log_extras.update(step.log_extras)
                elif event.type == EventType.PROTECTION_CHECK:
                    step = protection_sm.on_protection_check(
                        event.timestamp,
                        portfolio=portfolio, queue=queue,
                        session_date=session_date,
                    )
                    log_extras.update(step.log_extras)
                    # Phase 6 task 2 — flatten violators that the state
                    # machine moved to FLATTEN_SUBMITTED. We close them at the
                    # last known mark (the lot's current_price, which is the
                    # entry price if no MTM yet) using ``manual_flatten`` as
                    # the exit reason; the trade row drops into the standard
                    # trades.parquet.
                    flatten_lots = [
                        p for p in list(portfolio.open_positions.values())
                        if p.protection_state == ProtectionState.FLATTEN_SUBMITTED
                    ]
                    for p in flatten_lots:
                        exit_price = float(p.current_price or p.entry_price)
                        trade = portfolio.close_position_by_id(
                            p.position_id,
                            exit_price=exit_price,
                            exit_reason="manual_flatten",
                            exit_date=session_date,
                        )
                        sess_acc.trades.append(trade)
                        # Emit a CHILD_FILL log row for the manual flatten so
                        # the dispatch log records the closure timestamp.
                        flatten_event = Event(
                            timestamp=event.timestamp,
                            type=EventType.CHILD_FILL,
                            payload={
                                "session_date": session_date,
                                "position_id": p.position_id,
                                "symbol": p.symbol,
                                "exit_reason": "manual_flatten",
                            },
                        )
                        _log_event(
                            sess_acc, event=flatten_event, portfolio=portfolio,
                            extras={
                                "exit_price": float(exit_price),
                                "trade_pnl": float(trade.get("pnl", 0.0)),
                                "manual_flatten": True,
                            },
                        )
                elif event.type == EventType.PARENT_FILL_TIMEOUT:
                    # Realism remediation 2 Phase 5 (audit P0-006): a no-fill
                    # marker emitted by ``simulate_marketable_limit_fill`` when
                    # the quote ran past the limit before the timeout. The
                    # synchronous fill model already realised the no-fill; the
                    # event is logged here so the dispatch log reflects the
                    # timeout firing in chronological order.
                    pass
                elif event.type == EventType.EOD_MARK:
                    # End-of-session mark-to-market for still-open lots uses
                    # the symbol's last daily-bar close.
                    for sym in sorted({p.symbol for p in portfolio.open_positions.values()}):
                        day_bars = daily_bars_supplier(sym, session_date)
                        if day_bars is None or len(day_bars) == 0:
                            continue
                        row = day_bars.iloc[-1].to_dict()
                        closes_today[sym] = float(row.get("close", row.get("Close", 0.0)) or 0.0)
                    portfolio.update_mtm(closes_today)
                # PROTECTION_CHECK / TIME_STOP_CHECK / QUOTE (fill_poll):
                # exits already evaluated above; the event itself is just a
                # log marker in Phase 4. Phase 6 / Phase 7 fill in lifecycle.
                if collect_event_log:  # §10h opt #1 — skip discarded rows in objective_minimal
                    _log_event(
                        sess_acc, event=event, portfolio=portfolio,
                        extras=log_extras or None,
                    )

            # Roll the session accumulators into the cross-session lists.
            all_candidate_events.extend(sess_acc.candidate_events)
            all_gate_dump.extend(sess_acc.gate_dump)
            all_decisions.extend(sess_acc.decisions)
            all_orders.extend(sess_acc.orders)
            all_fills.extend(sess_acc.fills)
            all_fill_records.extend(sess_acc.fill_records)
            quote_coverage_rows.extend(sess_acc.quote_coverage)
            all_trades.extend(sess_acc.trades)
            all_fade_telemetry.extend(sess_acc.fade_telemetry)
            missing_quote_count += sess_acc.missing_quote_count
            ambiguous_bar_count += sess_acc.ambiguous_count
            if collect_event_log:
                event_log_by_session[session_key] = list(sess_acc.event_log)
            # Realism remediation 2 Phase 7 (audit P1-003): record BOTH
            # counters per session — the scanner-dedup view (signal emits) and
            # the portfolio view (PARENT_FILL entries). The two are
            # intentionally distinct; the report surfaces them side-by-side.
            sess_count["signal_emits_per_symbol_today"] = dict(
                state.get("signal_emits_per_symbol_today") or {}
            )
            sess_count["entries_per_symbol_today"] = dict(
                (portfolio.state.entries_per_symbol_today or {})
                if portfolio.state is not None
                else {}
            )
            # The canonical roll-up parquet honors the per-session cap so the
            # default file is bounded; the per-session partition (written
            # below) keeps the FULL log when the session overflowed.
            if collect_event_log:
                if len(sess_acc.event_log) > _EVENTS_PER_SESSION_CAP:
                    all_event_log_rows.extend(sess_acc.event_log[:_EVENTS_PER_SESSION_CAP])
                else:
                    all_event_log_rows.extend(sess_acc.event_log)
        for pos in portfolio.open_positions.values():
            all_positions.append({
                "session_date": session_date.isoformat(),
                "symbol": pos.symbol, "qty": pos.qty,
                "position_id": pos.position_id,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price,
                "unrealized_pnl": pos.unrealized_pnl,
            })
        daily_equity.append({
            "session_date": session_date.isoformat(),
            "bankroll": portfolio.state.bankroll if portfolio.state else portfolio.initial_bankroll,
            "gross_exposure_dollars": portfolio.state.gross_exposure_dollars if portfolio.state else 0,
            "gross_exposure_pct": portfolio.state.gross_exposure_pct if portfolio.state else 0,
            "entries_today": portfolio.state.entries_today if portfolio.state else 0,
            "stopouts_today": portfolio.state.stopouts_today if portfolio.state else 0,
            "daily_realized_pnl": portfolio.state.daily_realized_pnl if portfolio.state else 0,
            "daily_unrealized_pnl": portfolio.state.daily_unrealized_pnl if portfolio.state else 0,
        })

    # Realism Phase 3: per-session universe artifacts + hashes. The funnel +
    # snapshot parquet are written for sessions supplied as real PIT records;
    # the per-session universe_hash (sorted eligible-symbol sha256) is collected
    # for *every* session for the run manifest. For PIT sessions the hash comes
    # from the funnel; for legacy snapshots it is the snapshot's own hash.
    universe_hashes_by_session: dict[str, str] = {}
    if pit_records_by_session:
        if artifact_mode == "full":
            pit_hashes = write_universe_artifacts(run_dir, pit_records_by_session)
        else:
            # objective_minimal — compute the per-session universe hashes
            # in-memory without writing the universe artifact parquet files.
            from ..universe.persist import compute_universe_hashes

            pit_hashes = compute_universe_hashes(pit_records_by_session)
        for sd, uhash in pit_hashes.items():
            key = sd.isoformat() if isinstance(sd, _dt.date) else str(sd)
            universe_hashes_by_session[key] = uhash
    for session_date, snap in universe_snapshot_by_session.items():
        key = (
            session_date.isoformat()
            if isinstance(session_date, _dt.date)
            else str(session_date)
        )
        universe_hashes_by_session.setdefault(
            key, str(snap.get("universe_hash", "sha256:unknown"))
        )

    # Build summary + write artifacts.
    accepted_count = sum(1 for d in all_decisions if d["decision"] == "accepted")
    rejected_count = sum(1 for d in all_decisions if d["decision"] == "rejected")
    broker_reject_count = sum(1 for d in all_decisions if d.get("reason") == "broker_reject")
    summary = build_summary(
        trades=all_trades,
        candidate_events_count=len(all_candidate_events),
        entry_decisions_count=len(all_decisions),
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        broker_reject_count=broker_reject_count,
        initial_bankroll=initial_bankroll,
        final_bankroll=portfolio.state.bankroll if portfolio.state else initial_bankroll,
        ambiguous_bar_count=ambiguous_bar_count,
        cost_stress=(cfg_dict.get("backtest") or {}).get("cost_stress", "conservative"),
        feed=(cfg_dict.get("market_data") or {}).get("feed", "iex"),
        run_id=run_id,
        strategy_version=str(cfg_dict.get("strategy_version", "0.1.0")),
    )
    # Realism Phase 6: surface execution-quality counters in the summary so the
    # walk-forward objective (FoldResult.missing_quote_count) and reports can
    # read them.
    from ..data.data_quality import build_quote_coverage_check, historical_quote_coverage_pct

    _filled_fills = [f for f in all_fill_records if f.get("filled")]
    _partials = [f for f in _filled_fills if f.get("is_partial")]
    quote_cov_pct = historical_quote_coverage_pct(quote_coverage_rows)
    summary["missing_quote_count"] = missing_quote_count
    summary["fills_count"] = len(_filled_fills)
    summary["partial_fill_count"] = len(_partials)
    summary["fill_rate"] = (
        len(_filled_fills) / len(all_fill_records) if all_fill_records else 0.0
    )
    summary["historical_quote_coverage_pct"] = round(quote_cov_pct, 4)
    summary["fees_paid_total"] = round(
        sum(float(f.get("commission", 0.0) or 0.0)
            + float(f.get("regulatory_fees", 0.0) or 0.0) for f in _filled_fills),
        6,
    )

    # Audit 2026-05-29 §8.5 / Phase 4b — gap-through-stop counters. A bar that
    # opens past the stop fills at the OPEN (reason "gap_stop"), taking the gap
    # loss. Surface the event count + realized loss on losing gap-throughs so the
    # objective's gap_through_stop penalty (default-off weight) can read them.
    _gap_trades = [t for t in all_trades if t.get("exit_reason") == "gap_stop"]
    summary["n_gap_through_events"] = len(_gap_trades)
    summary["gap_through_loss_dollars"] = round(
        sum(-float(t.get("pnl", 0.0) or 0.0)
            for t in _gap_trades if float(t.get("pnl", 0.0) or 0.0) < 0.0),
        6,
    )
    # Audit 2026-05-29 §9 Phase 5 — distinct entry sessions (fold-activity gate).
    summary["n_active_days"] = len(
        {t.get("entry_date") for t in all_trades if t.get("entry_date")}
    )

    # Realism remediation 2 Phase 6 (audit P0-007) — protection lifecycle
    # metrics. Surfaced under ``summary['protection']`` so the run-report and
    # the Phase-8 optuna objective penalty can read them without traversing
    # the per-event log. Always present so a clean-run zero-value row is
    # explicit in the report rather than an absent key.
    pm = portfolio.protection_metrics
    summary["protection"] = {
        "max_unprotected_seconds_observed": round(
            float(pm.max_unprotected_seconds_observed), 4
        ),
        "oco_attach_attempts_count": int(pm.oco_attach_attempts_count),
        "oco_attach_failure_count": int(pm.oco_attach_failure_count),
        "fallback_stop_count": int(pm.fallback_stop_count),
        "flatten_unprotected_count": int(pm.flatten_unprotected_count),
        "entries_blocked_by_protection_count": int(
            pm.entries_blocked_by_protection_count
        ),
        "total_unprotected_seconds_across_lots": round(
            float(pm.total_unprotected_seconds_across_lots), 4
        ),
        "unprotected_violation_count": int(pm.unprotected_violation_count),
    }

    # Code & dataset manifests.
    code_paths = code_paths_for_manifest or [paths.lab_root / "src"]
    code_man = build_code_manifest(repo_root=paths.lab_root.parent.parent, source_paths=code_paths)
    code_hash = code_manifest_hash(code_man)
    feed = (cfg_dict.get("market_data") or {}).get("feed", "iex")
    all_symbols = sorted({s["symbol"] for u in universe_snapshot_by_session.values() for s in u.get("symbols", [])})
    if not all_symbols:
        all_symbols = ["SYNTH"]
    ds_man = build_dataset_manifest(
        # Realism Phase 2: real provider — lake runs report the lake provider
        # ("alpaca"); synthetic runs legitimately report "fixture".
        provider=dataset_provider, feed=feed, symbols=all_symbols,
        start_date=sessions[0].isoformat() if sessions else "1970-01-01",
        end_date=sessions[-1].isoformat() if sessions else "1970-01-01",
        dataset_hash=dataset_hash,
        bar_count=sum(len(daily_cache_by_session.get(s, pd.DataFrame())) for s in sessions),
        adjustments=str(dataset_lineage.get("adjustment", "")) or None,
        extras={"strategy_id": "bowaka_v2", "dataset_regime": dataset_lineage["regime"]},
    )
    # Run lineage: the simulation-mode contract + the four lineage hashes plus
    # the Phase-2 content-derived dataset lineage (component hashes for forensics).
    git_head = _git_head()
    strategy_config_hash_actual = actual_contract_hash()  # "" if contract not generated
    lineage = {
        "simulation_mode": sim_cfg.mode,
        "feed": feed,
        "strategy_config_hash_actual": strategy_config_hash_actual,
        "lab_config_hash": strategy_hash,
        "dataset_hash": dataset_hash,
        "code_hash": git_head,
        "code_manifest_hash": code_hash,
        "dataset_regime": dataset_lineage["regime"],
        "dataset_provider": dataset_provider,
        "dataset_adjustment": dataset_lineage.get("adjustment"),
        "dataset_hash_components": dataset_lineage["components"],
    }
    run_man = build_run_manifest(
        strategy_id="bowaka_v2",
        strategy_version=str(cfg_dict.get("strategy_version", "0.1.0")),
        run_id=run_id, config_hash=strategy_hash, dataset_hash=dataset_hash,
        code_manifest_hash=code_hash, run_kind="backtest", feed=feed,
        extras={
            "run_hash": run_hash,
            "ambiguous_bar_count": ambiguous_bar_count,
            "simulation": sim_cfg.model_dump(),
            # Realism remediation 2 Phase 0: the simulation contract (== the
            # simulation mode) is surfaced as a top-level manifest field so every
            # run artifact declares which strategy it reproduced. suitability_tier
            # is added below, after the mechanical decision runs.
            "simulation_contract": sim_cfg.mode,
            "lineage": lineage,
            # Realism Phase 3: per-session point-in-time universe hashes.
            "universe_hashes_by_session": universe_hashes_by_session,
            # Realism Phase 4: per-session intraday scan cadence + funnel —
            # expected vs actual scan count, candidate / accepted counts and
            # the gate-rejection breakdown.
            "scan_counts": scan_counts,
            "data_quality": {
                "regime": data_quality_report["regime"],
                "passed": data_quality_report["passed"],
                "failed": data_quality_report["failed"],
                "warned": data_quality_report["warned"],
                "required_failures": data_quality_report["required_failures"],
            },
            "startup_dq_failure": None,
        },
    )

    # Build the in-memory execution-quality rows + exit analysis — these are
    # needed by the BacktestResult fields the Optuna objective consumes, and
    # also for the finalize quote-coverage gate below. They are the SAME
    # objects subsequently written to disk in full mode.
    from ..reports.execution_quality import build_execution_quality_rows
    from ..reports.exit_analysis import build_exit_analysis

    eq_rows = build_execution_quality_rows(
        all_fill_records, missing_quote_count=missing_quote_count,
        decisions=all_decisions, quote_coverage_rows=quote_coverage_rows,
    )
    eq_rows.append({
        "metric": "broker_reject_rate",
        "value": broker_reject_count / max(1, len(all_decisions)),
    })
    eq_rows.append({"metric": "ambiguous_bar_count", "value": float(ambiguous_bar_count)})
    eq_rows.append({
        "metric": "historical_quote_coverage_pct", "value": round(quote_cov_pct, 4),
    })

    exit_analysis = build_exit_analysis(all_trades)
    exit_analysis["signal_fade_telemetry_count"] = len(all_fade_telemetry)
    exit_analysis["signal_fade_telemetry"] = [
        {
            "symbol": t.symbol, "position_id": t.position_id,
            "eval_date": t.eval_date.isoformat(),
            "eval_timestamp": t.eval_timestamp, "score": t.score,
            "threshold_name": t.threshold_name,
            "threshold_value": t.threshold_value,
            "would_exit_reason": t.would_exit_reason,
        }
        for t in all_fade_telemetry
    ]
    # Surface the exit-analysis summary fields BEFORE the finalize gate so the
    # summary is identical regardless of artifact_mode.
    summary["exit_reason_distribution"] = exit_analysis["exit_reason_distribution"]["counts"]
    summary["ambiguous_stop_wins"] = (
        exit_analysis["exit_reason_distribution"]["ambiguous_stop_wins"]
    )
    summary["exit_slippage_bps"] = exit_analysis["exit_slippage_bps"]
    summary["signal_fade_telemetry_count"] = len(all_fade_telemetry)

    # ---- Realism Phase 6: finalize-step quote-coverage gate (always runs) ----
    # In intended_realism mode the run FAILS at finalize when the fraction of
    # (symbol, scan_ts) pairs backed by a historical quote is below
    # simulation.min_quote_coverage_pct. The check is appended to the (in-memory
    # OR on-disk) data-quality report; the run manifest's startup_dq_failure
    # stays None (this is a finalize failure, distinct from the startup gate).
    quote_cov_check = build_quote_coverage_check(
        quote_coverage_rows=quote_coverage_rows,
        min_quote_coverage_pct=sim_cfg.min_quote_coverage_pct,
        simulation_mode=sim_cfg.mode,
    )
    if artifact_mode == "full":
        try:
            _dq_doc = json.loads((run_dir / "data_quality_report.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — defensive; the report was written earlier
            _dq_doc = {"checks": []}
    else:
        # objective_minimal — the pre-loop DQ json was not written; clone the
        # in-memory report so we can append the finalize check identically.
        _dq_doc = dict(data_quality_report)
        _dq_doc["checks"] = list(_dq_doc.get("checks") or [])
    _dq_doc.setdefault("checks", []).append(quote_cov_check)
    if quote_cov_check["status"] == "fail":
        _dq_doc["failed"] = int(_dq_doc.get("failed", 0)) + 1
        _req = list(_dq_doc.get("required_failures") or [])
        if "quote_coverage" not in _req:
            _req.append("quote_coverage")
        _dq_doc["required_failures"] = sorted(set(_req))
    elif quote_cov_check["status"] == "warn":
        _dq_doc["warned"] = int(_dq_doc.get("warned", 0)) + 1
    else:
        _dq_doc["passed"] = int(_dq_doc.get("passed", 0)) + 1
    if sim_cfg.mode == "intended_realism" and quote_cov_check["status"] == "fail":
        raise RuntimeError(
            "intended_realism run aborted at finalize: "
            + str(quote_cov_check["evidence"].get("detail", "quote_coverage failed"))
        )

    # The remaining work — artifact writes, report renderer, promotion
    # checklist, suitability decision — runs only in full mode. The in-memory
    # state collected above is returned in :class:`BacktestResult` and the
    # Optuna objective scores from it directly (speedup §5.1 / §11.2 Phase 1).
    if artifact_mode == "full":
        # Write all artifacts (atomic). data_quality_report.json was written
        # earlier (before the run loop) so the realism DQ gate could fail
        # closed; here it is rewritten with the finalize quote-coverage row.
        atomic_write_json(run_dir / "run_manifest.json", run_man)
        atomic_write_json(run_dir / "config_snapshot.json", cfg_dict)
        atomic_write_json(run_dir / "dataset_manifest.json", ds_man)
        atomic_write_json(run_dir / "code_manifest.json", code_man)
        if all_candidate_events:
            append_jsonl(run_dir / "candidate_events.jsonl", all_candidate_events)
            write_parquet(run_dir / "candidate_events.parquet", pd.json_normalize(all_candidate_events, sep="."))
        else:
            (run_dir / "candidate_events.jsonl").write_text("", encoding="utf-8")
            write_parquet(run_dir / "candidate_events.parquet", pd.DataFrame({"symbol": []}))
        # Realism Phase 4: per-(scan_ts, symbol) gate dump. With full intraday
        # replay this is ~scans x universe rows; when it grows past the
        # partition threshold the rows are also written partitioned per session
        # date under scanner/gate_dump_by_session/ to keep any single file
        # bounded.
        _write_gate_dump(run_dir, all_gate_dump)
        write_parquet(run_dir / "entry_decisions.parquet",
                      pd.json_normalize(all_decisions, sep=".") if all_decisions else pd.DataFrame({"symbol": []}))
        write_parquet(run_dir / "orders.parquet",
                      pd.DataFrame(all_orders) if all_orders else pd.DataFrame({"parent_order_id": []}))
        write_parquet(run_dir / "fills.parquet",
                      pd.DataFrame(all_fills) if all_fills else pd.DataFrame({"parent_order_id": []}))
        write_parquet(run_dir / "positions.parquet",
                      pd.DataFrame(all_positions) if all_positions else pd.DataFrame({"symbol": []}))
        write_parquet(run_dir / "trades.parquet",
                      pd.DataFrame(all_trades) if all_trades else pd.DataFrame({"symbol": []}))
        write_parquet(run_dir / "daily_equity.parquet",
                      pd.DataFrame(daily_equity) if daily_equity else pd.DataFrame({"session_date": []}))
        write_parquet(run_dir / "execution_quality.parquet", pd.DataFrame(eq_rows))

        events_dir = run_dir / "events"
        events_dir.mkdir(parents=True, exist_ok=True)
        if all_event_log_rows:
            write_parquet(events_dir / "events.parquet", pd.DataFrame(all_event_log_rows))
        else:
            write_parquet(events_dir / "events.parquet", pd.DataFrame({
                "timestamp": [], "event_type": [], "session_date": [],
                "position_id": [], "parent_order_id": [], "symbol": [],
            }))
        for sk, rows in event_log_by_session.items():
            if len(rows) > _EVENTS_PER_SESSION_CAP:
                partition_dir = events_dir / "by_session"
                partition_dir.mkdir(parents=True, exist_ok=True)
                write_parquet(partition_dir / f"{sk}.parquet", pd.DataFrame(rows))

        atomic_write_json(run_dir / "exit_analysis.json", exit_analysis)
        atomic_write_json(run_dir / "summary.json", summary)
        atomic_write_json(run_dir / "data_quality_report.json", _dq_doc)

        # ---- Realism Phase 8: substantive report renderer ---------------------
        # report.md + report.json are assembled from the artifacts written above
        # — nothing is recomputed.
        from ..reports.render_run_report import write_run_report
        from ..promotion.checklist import run_all_checklists
        from ..promotion.suitability import decide_suitability

        _checklist_results = run_all_checklists(run_dir)
        _tier = decide_suitability(run_dir, _checklist_results)
        run_man["suitability_tier"] = _tier
        atomic_write_json(run_dir / "run_manifest.json", run_man)
        write_run_report(
            run_dir,
            suitability=_tier,
            checklist_results=_checklist_results,
        )

    # Capture the active ProfileCounters snapshot (if any) into the result —
    # exposed on BacktestResult for the benchmark script. Safe under no-context.
    from ..utils.profile_counters import counters_enabled as _ce
    from ..utils.profile_counters import current_profile_counters as _cc

    profile_snapshot: Optional[dict] = None
    if _ce():
        try:
            profile_snapshot = _cc().snapshot()
        except LookupError:
            profile_snapshot = None

    return BacktestResult(
        run_id=run_id, run_dir=run_dir, summary=summary,
        trades=all_trades, decisions=all_decisions,
        candidate_events=all_candidate_events, portfolio=portfolio,
        daily_equity=list(daily_equity),
        execution_quality_rows=list(eq_rows),
        quote_coverage_rows=list(quote_coverage_rows),
        orders=list(all_orders),
        fills=list(all_fills),
        positions=list(all_positions),
        exit_analysis=dict(exit_analysis),
        profile_counters=profile_snapshot,
        artifact_mode=artifact_mode,
    )
