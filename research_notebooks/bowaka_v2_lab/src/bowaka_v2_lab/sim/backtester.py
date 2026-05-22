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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

import pandas as pd

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
from ..data.data_quality import build_data_quality_report, evaluate_startup_dq
from ..data.lineage import build_dataset_lineage
from ..reference import actual_contract_hash, contract_available, load_actual_contract
from ..universe.builder import UniverseRecord, to_scanner_snapshot
from ..universe.persist import write_universe_artifacts
from ..utils.atomic_io import append_jsonl, atomic_write_json, write_parquet
from ..utils.ids import generate_run_id
from ..utils.time import require_aware_timestamp
from .broker import SimulatedBroker
from .event_loop import run_one_scan
from .exit_driver import drive_session_exits_daily, drive_session_exits_minute
from .metrics import build_summary
from .portfolio import Portfolio, Position
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
    "summary.json",
    "report.md",
    "report.json",
    "config_diff_vs_actual_bowaka_v2.yaml",
)


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
    non_smoke = sim_mode in ("current_code_parity", "intended_realism")
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
    volume_curve: Optional[pd.DataFrame] = None,
    initial_bankroll: float = 100_000.0,
    paths: Optional[BowakaV2Paths] = None,
    run_dir: Optional[Path] = None,
    code_paths_for_manifest: Optional[list[Path]] = None,
) -> BacktestResult:
    """Run a complete v2 backtest and write the 16-file artifact contract."""
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
    data_quality_report = build_data_quality_report(
        cfg=cfg_dict,
        lineage=dataset_lineage,
        requested_symbols=requested_symbols,
        sessions=sessions,
        daily_bars_supplier=daily_bars_supplier,
        minute_bars_supplier=minute_bars_supplier,
        scan_times_per_session=scan_times_per_session,
        # Realism remediation 2 Phase 3 — the daily-feature cache feeds the
        # feature-leakage check; the full-session minute supplier feeds the
        # session-level minute-count / gap / stale checks.
        daily_cache_by_session=daily_cache_by_session,
        session_minute_supplier=session_minute_supplier,
    )
    atomic_write_json(run_dir / "data_quality_report.json", data_quality_report)
    startup_dq_failure = evaluate_startup_dq(
        data_quality_report, simulation_mode=sim_cfg.mode
    )
    if startup_dq_failure is not None:
        # Record the precise rejection reason in the run manifest, then abort.
        feed = (cfg_dict.get("market_data") or {}).get("feed", "iex")
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
        raise RuntimeError(startup_dq_failure)

    # Config-parity diff vs the frozen live contract (realism Phase 1). Written
    # on every run; in intended_realism mode an unannotated `mismatch` aborts
    # the run at startup, before the run loop produces any further artifacts.
    if contract_available():
        _diff_path, _diff_rows = write_config_diff(
            run_dir, cfg_dict, load_actual_contract(),
            config_path=cfg_dict.get("_source_path"),
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
    else:
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
            "entries_per_symbol_today": {},
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

        for scan_ts in session_scan_times:
            scan_result, consumer_results = run_one_scan(
                cfg=cfg_dict, universe_snapshot=universe, daily_cache=daily_cache,
                volume_curve=volume_curve, state=state, scan_ts=scan_ts,
                bars_supplier=minute_bars_supplier, consumer=consumer,
                quote_supplier=quote_supplier,
                forward_minute_supplier=forward_minute_supplier,
            )
            all_candidate_events.extend(scan_result.emitted)
            all_gate_dump.extend(scan_result.gate_dump)
            # Realism Phase 6: per-(symbol, scan_ts) quote-coverage rows built by
            # run_one_scan — drives historical_quote_coverage_pct.
            quote_coverage_rows.extend(scan_result.quote_coverage)
            # Realism Phase 4: roll the per-session scan-count summary.
            sess_count["actual_scans"] += 1
            sess_count["candidate_count"] += len(scan_result.emitted)
            for row in scan_result.gate_dump:
                reason = row.get("rejection_reason")
                if reason:
                    breakdown = sess_count["gate_rejection_breakdown"]
                    breakdown[reason] = breakdown.get(reason, 0) + 1
            for cr in consumer_results:
                all_decisions.extend(cr.decisions)
                sess_count["accepted_count"] += sum(
                    1 for d in cr.decisions if d.get("decision") == "accepted"
                )
                # Realism Phase 6: collect the consumer's per-candidate fill
                # records + missing-quote rejects for the execution-quality
                # report.
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
                # Realism Phase 6: fills.parquet rows come from the *actual*
                # fill records — one per candidate that reached the fill stage,
                # whether the fill landed or failed (timeout / partial-below-min).
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

        # Exit evaluation. Realism Phase 7: exits are driven PER LOT (not per
        # symbol), closing by position_id. The minute path
        # (drive_session_exits_minute) is used for current_code_parity /
        # intended_realism; the daily-bar path (drive_session_exits_daily) is
        # used ONLY for smoke_fixture so the smoke suite stays fast.
        closes_today: dict[str, float] = {}
        if sim_cfg.mode == "smoke_fixture":
            exit_out = drive_session_exits_daily(
                portfolio, session_date, cfg=cfg_dict,
                daily_bars_supplier=daily_bars_supplier,
            )
            closes_today = exit_out.get("closes", {})
        else:
            session_fade_score_fn = _build_fade_score_fn(
                cfg=cfg_dict, daily_cache=daily_cache, volume_curve=volume_curve,
                minute_bars_supplier=minute_bars_supplier,
                session_minute_supplier=session_minute_supplier,
            )
            exit_out = drive_session_exits_minute(
                portfolio, session_date, cfg=cfg_dict,
                session_minute_supplier=session_minute_supplier,
                minute_bars_supplier=minute_bars_supplier,
                quote_supplier=quote_supplier,
                signal_score_fn=session_fade_score_fn,
                cost_stress=(cfg_dict.get("backtest") or {}).get("cost_stress", "base"),
                seed=int((cfg_dict.get("run") or {}).get("seed", 0)),
            )
            all_fade_telemetry.extend(exit_out.get("fade_telemetry", []))
            # End-of-session mark-to-market for the still-open lots uses the
            # symbol's last daily-bar close.
            for sym in sorted({p.symbol for p in portfolio.open_positions.values()}):
                day_bars = daily_bars_supplier(sym, session_date)
                if day_bars is None or len(day_bars) == 0:
                    continue
                row = day_bars.iloc[-1].to_dict()
                closes_today[sym] = float(row.get("close", row.get("Close", 0.0)) or 0.0)
        ambiguous_bar_count += int(exit_out.get("ambiguous", 0))
        all_trades.extend(exit_out.get("trades", []))
        portfolio.update_mtm(closes_today)
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
        pit_hashes = write_universe_artifacts(run_dir, pit_records_by_session)
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

    # Write all 16 artifacts (atomic). data_quality_report.json is written
    # earlier (before the run loop) so the realism DQ gate can fail closed; it
    # is not re-written here.
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
    # replay this is ~scans x universe rows; when it grows past the partition
    # threshold the rows are also written partitioned per session date under
    # scanner/gate_dump_by_session/ to keep any single file bounded.
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
    # Realism Phase 6: execution_quality.parquet — spread / quote-age / slippage
    # distributions, fill + partial-fill rates, missing-quote count, liquidity
    # participation, fees paid and the quote source mix. Built from the
    # per-candidate fill records; the legacy broker-reject / ambiguous-bar
    # counters are appended so existing readers still find them.
    from ..reports.execution_quality import build_execution_quality_rows

    eq_rows = build_execution_quality_rows(
        all_fill_records, missing_quote_count=missing_quote_count
    )
    eq_rows.append({
        "metric": "broker_reject_rate",
        "value": broker_reject_count / max(1, len(all_decisions)),
    })
    eq_rows.append({"metric": "ambiguous_bar_count", "value": float(ambiguous_bar_count)})
    eq_rows.append({
        "metric": "historical_quote_coverage_pct", "value": round(quote_cov_pct, 4),
    })
    write_parquet(run_dir / "execution_quality.parquet", pd.DataFrame(eq_rows))

    # Realism Phase 7: exit-lifecycle analysis artifact — exit-reason
    # distribution, exit-slippage distribution and per-trade MFE/MAE. Written as
    # exit_analysis.json (machine-readable) and surfaced in summary.json so the
    # report renderer + downstream readers can find the distribution.
    from ..reports.exit_analysis import build_exit_analysis

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
    atomic_write_json(run_dir / "exit_analysis.json", exit_analysis)
    summary["exit_reason_distribution"] = exit_analysis["exit_reason_distribution"]["counts"]
    summary["ambiguous_stop_wins"] = (
        exit_analysis["exit_reason_distribution"]["ambiguous_stop_wins"]
    )
    summary["exit_slippage_bps"] = exit_analysis["exit_slippage_bps"]
    summary["signal_fade_telemetry_count"] = len(all_fade_telemetry)
    atomic_write_json(run_dir / "summary.json", summary)

    # ---- Realism Phase 6: finalize-step quote-coverage gate ----------------
    # In intended_realism mode the run FAILS at finalize when the fraction of
    # (symbol, scan_ts) pairs backed by a historical quote is below
    # simulation.min_quote_coverage_pct. The coverage check is appended to the
    # already-written data_quality_report.json so the failure is recorded; the
    # run manifest's startup_dq_failure stays None (this is a finalize failure,
    # distinct from the startup gate). This runs BEFORE the report is rendered
    # so the report reflects the complete, finalized data-quality report.
    quote_cov_check = build_quote_coverage_check(
        quote_coverage_rows=quote_coverage_rows,
        min_quote_coverage_pct=sim_cfg.min_quote_coverage_pct,
        simulation_mode=sim_cfg.mode,
    )
    try:
        _dq_doc = json.loads((run_dir / "data_quality_report.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — defensive; the report was written earlier
        _dq_doc = {"checks": []}
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
    atomic_write_json(run_dir / "data_quality_report.json", _dq_doc)
    if sim_cfg.mode == "intended_realism" and quote_cov_check["status"] == "fail":
        raise RuntimeError(
            "intended_realism run aborted at finalize: "
            + str(quote_cov_check["evidence"].get("detail", "quote_coverage failed"))
        )

    # ---- Realism Phase 8: substantive report renderer ---------------------
    # report.md (human) + report.json (machine-readable) are assembled entirely
    # from the artifacts written above — nothing is recomputed. The renderer
    # carries the full Phase 0-7 section set; the Phase-4 stub language is gone.
    from ..reports.render_run_report import write_run_report
    from ..promotion.checklist import run_all_checklists
    from ..promotion.suitability import decide_suitability

    _checklist_results = run_all_checklists(run_dir)
    _tier = decide_suitability(run_dir, _checklist_results)
    # Realism remediation 2 Phase 0: stamp the mechanical suitability_tier onto
    # the run manifest (simulation_contract was stamped above). The report
    # renderer already surfaces both top-level fields in report.json.
    run_man["suitability_tier"] = _tier
    atomic_write_json(run_dir / "run_manifest.json", run_man)
    write_run_report(
        run_dir,
        suitability=_tier,
        checklist_results=_checklist_results,
    )

    return BacktestResult(
        run_id=run_id, run_dir=run_dir, summary=summary,
        trades=all_trades, decisions=all_decisions,
        candidate_events=all_candidate_events, portfolio=portfolio,
    )
