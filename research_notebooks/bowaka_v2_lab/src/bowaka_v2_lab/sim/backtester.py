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

from ..config.hashing import canonical_run_hash, canonical_strategy_hash
from ..config.models import SimulationConfig
from ..config.paths import BowakaV2Paths
from ..reference import actual_contract_hash
from ..utils.atomic_io import append_jsonl, atomic_write_json, write_parquet
from ..utils.ids import generate_run_id
from ..utils.time import require_aware_timestamp
from .broker import SimulatedBroker
from .event_loop import run_one_scan
from .exits import evaluate_exits
from .metrics import build_summary
from .portfolio import Portfolio, Position


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


def run_backtest(
    *,
    cfg: Mapping[str, Any],
    sessions: list[_dt.date],
    scan_times_per_session: Callable[[_dt.date], list[Any]],
    universe_snapshot_by_session: Mapping[_dt.date, dict],
    daily_cache_by_session: Mapping[_dt.date, pd.DataFrame],
    minute_bars_supplier: Callable[[str, Any], pd.DataFrame | None],
    daily_bars_supplier: Callable[[str, _dt.date], pd.DataFrame | None],
    quote_supplier: Optional[Callable[[str, Any], Optional[dict]]] = None,
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
    strategy_hash = canonical_strategy_hash(cfg_dict)
    run_hash = canonical_run_hash(cfg_dict)
    # Use plain hex for generate_run_id (no "sha256:" prefix — colons are invalid on Windows paths).
    dataset_hash = run_hash[:16]  # simulator-grade placeholder
    run_id = generate_run_id(kind="backtest", cfg_hash=strategy_hash, dataset_hash=dataset_hash)

    if run_dir is None:
        run_dir = paths.artifact_root / "runs" / run_id
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

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

    state: dict[str, Any] = {"entered_symbols_today": [], "in_play_pool": {}}
    for session_date in sessions:
        portfolio.begin_session(session_date)
        # Per [Report §9.6]: open positions block re-entry by the same symbol.
        # The scanner's ``entered_symbols_today`` set acts as that block.
        state["entered_symbols_today"] = sorted(portfolio.open_positions.keys())
        universe = universe_snapshot_by_session.get(session_date)
        daily_cache = daily_cache_by_session.get(session_date)
        if universe is None or daily_cache is None:
            continue

        for scan_ts in scan_times_per_session(session_date):
            scan_result, consumer_results = run_one_scan(
                cfg=cfg_dict, universe_snapshot=universe, daily_cache=daily_cache,
                volume_curve=volume_curve, state=state, scan_ts=scan_ts,
                bars_supplier=minute_bars_supplier, consumer=consumer,
                quote_supplier=quote_supplier,
            )
            all_candidate_events.extend(scan_result.emitted)
            all_gate_dump.extend(scan_result.gate_dump)
            for cr in consumer_results:
                all_decisions.extend(cr.decisions)
                for po in cr.parent_orders:
                    all_orders.append({
                        "parent_order_id": po.parent_order_id,
                        "symbol": po.symbol,
                        "side": po.plan.side.value,
                        "order_style": po.plan.order_style,
                        "qty": po.plan.qty,
                        "status": po.status.value,
                        "created_at": po.created_at,
                        "candidate_event_id": po.candidate_event_id,
                    })
                    if po.status.value == "accepted":
                        all_fills.append({
                            "parent_order_id": po.parent_order_id,
                            "symbol": po.symbol,
                            "filled_qty": po.plan.qty,
                            "avg_fill_price": cr.new_positions[0].entry_price if cr.new_positions else None,
                            "notional": (cr.new_positions[0].entry_price * po.plan.qty) if cr.new_positions else None,
                        })

        # Daily bars + exit evaluation.
        symbols_to_check = list(portfolio.open_positions.keys())
        closes_today: dict[str, float] = {}
        for sym in symbols_to_check:
            day_bars = daily_bars_supplier(sym, session_date)
            if day_bars is None or len(day_bars) == 0:
                continue
            row = day_bars.iloc[-1].to_dict()
            closes_today[sym] = float(row.get("close", row.get("Close", 0.0)) or 0.0)
            pos = portfolio.open_positions.get(sym)
            if pos is None:
                continue
            ev = evaluate_exits(
                pos, bar=row, bar_date=session_date,
                exit_cfg=(cfg_dict.get("exits") or {}),
                same_bar_policy=(cfg_dict.get("exits") or {}).get("same_bar_policy", "stop_first"),
            )
            if ev is not None:
                if ev.ambiguous_bar_resolved:
                    ambiguous_bar_count += 1
                trade = portfolio.close_position(
                    sym, exit_price=ev.exit_price, exit_reason=ev.exit_reason,
                    exit_date=session_date,
                )
                all_trades.append(trade)
        portfolio.update_mtm(closes_today)
        for sym, pos in portfolio.open_positions.items():
            all_positions.append({
                "session_date": session_date.isoformat(),
                "symbol": sym, "qty": pos.qty,
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

    # Code & dataset manifests.
    code_paths = code_paths_for_manifest or [paths.lab_root / "src"]
    code_man = build_code_manifest(repo_root=paths.lab_root.parent.parent, source_paths=code_paths)
    code_hash = code_manifest_hash(code_man)
    feed = (cfg_dict.get("market_data") or {}).get("feed", "iex")
    all_symbols = sorted({s["symbol"] for u in universe_snapshot_by_session.values() for s in u.get("symbols", [])})
    if not all_symbols:
        all_symbols = ["SYNTH"]
    ds_man = build_dataset_manifest(
        provider="fixture", feed=feed, symbols=all_symbols,
        start_date=sessions[0].isoformat() if sessions else "1970-01-01",
        end_date=sessions[-1].isoformat() if sessions else "1970-01-01",
        dataset_hash=dataset_hash,
        bar_count=sum(len(daily_cache_by_session.get(s, pd.DataFrame())) for s in sessions),
        extras={"strategy_id": "bowaka_v2"},
    )
    # Run lineage: the simulation-mode contract + the four lineage hashes.
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
            "lineage": lineage,
        },
    )

    # Write all 16 artifacts (atomic).
    atomic_write_json(run_dir / "run_manifest.json", run_man)
    atomic_write_json(run_dir / "config_snapshot.json", cfg_dict)
    atomic_write_json(run_dir / "dataset_manifest.json", ds_man)
    atomic_write_json(run_dir / "code_manifest.json", code_man)
    atomic_write_json(run_dir / "data_quality_report.json", {
        "schema_version": 1,
        "checks": [],
        "notes": "Phase 4: minimal data-quality report; Phase 5 extends.",
    })
    if all_candidate_events:
        append_jsonl(run_dir / "candidate_events.jsonl", all_candidate_events)
        write_parquet(run_dir / "candidate_events.parquet", pd.json_normalize(all_candidate_events, sep="."))
    else:
        (run_dir / "candidate_events.jsonl").write_text("", encoding="utf-8")
        write_parquet(run_dir / "candidate_events.parquet", pd.DataFrame({"symbol": []}))
    write_parquet(run_dir / "gate_dump.parquet",
                  pd.json_normalize(all_gate_dump, sep=".") if all_gate_dump else pd.DataFrame({"symbol": []}))
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
    write_parquet(run_dir / "execution_quality.parquet", pd.DataFrame({
        "metric": ["broker_reject_rate", "ambiguous_bar_count"],
        "value": [broker_reject_count / max(1, len(all_decisions)), ambiguous_bar_count],
    }))
    atomic_write_json(run_dir / "summary.json", summary)
    report_lines = [
        "# Bowaka v2 Backtest Report (Phase 4 stub)",
        "",
        "## Run Header",
        "",
        f"- simulation.mode: `{sim_cfg.mode}`",
        f"- feed: `{feed}`",
        f"- strategy_config_hash_actual: `{strategy_config_hash_actual or '(contract not generated)'}`",
        f"- lab_config_hash: `{strategy_hash}`",
        f"- dataset_hash: `{dataset_hash}`",
        f"- code_hash (git HEAD): `{git_head}`",
        "",
        "### Simulation contract",
        "",
        f"- intraday_window_policy: `{sim_cfg.intraday_window_policy}`",
        f"- accepted_event_sequencing: `{sim_cfg.accepted_event_sequencing}`",
        f"- unknown_instrument_class_policy: `{sim_cfg.unknown_instrument_class_policy}`",
        f"- quote_fallback_policy: `{sim_cfg.quote_fallback_policy}`",
        f"- allow_research_relaxed: `{sim_cfg.allow_research_relaxed}`",
        "",
        "## Summary",
        "",
        f"- run_id: {run_id}",
        f"- trades: {len(all_trades)}",
        f"- net_return_pct: {summary['net_return_pct']:.4%}",
        "- (Phase 5 fills in the full report sections.)",
        "",
    ]
    (run_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    return BacktestResult(
        run_id=run_id, run_dir=run_dir, summary=summary,
        trades=all_trades, decisions=all_decisions,
        candidate_events=all_candidate_events, portfolio=portfolio,
    )
