"""Phase 2.5 — worker-count benchmark matrix.

Speedup report v2 §7.3 / §1.3 item 2. Sweeps a fixed grid of Optuna worker
counts against a real walk-forward config + PostgreSQL backend, captures
wall-clock + throughput + per-worker RSS + profile counters + PG saturation
proxies, and snapshots a fixed-parameter replay so a follow-up parity check
can confirm worker-count has no effect on per-fold output.

Output: ``artifacts/benchmarks/worker_count_matrix_<UTC timestamp>.json``
plus per-worker-count side files for forensic detail.

Operator-driven. The benchmark needs:
    - PostgreSQL container up (``docker compose ... up optuna-postgres``).
    - Enough RAM for the largest configured worker count to keep the
      memory-available headroom above the configured reserve.

The benchmark itself is NOT part of ``make test-all`` — its companion
analysis scripts (``check_worker_count_parity.py`` and
``select_worker_count_winner.py``) ARE tested in
``tests/unit/scripts/test_worker_count_*.py``.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


_DEFAULT_WORKER_COUNTS: tuple[int, ...] = (1, 4, 8, 10, 12)


def _peak_rss_gib() -> float:
    """Best-effort RSS measurement (cross-platform)."""
    try:
        import psutil  # type: ignore

        return float(psutil.Process(os.getpid()).memory_info().rss) / (2 ** 30)
    except Exception:  # noqa: BLE001
        return 0.0


def _system_memory_snapshot() -> dict[str, float]:
    """``{total_gib, available_gib, used_gib}`` snapshot of the host."""
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        return {
            "total_gib": vm.total / (2 ** 30),
            "available_gib": vm.available / (2 ** 30),
            "used_gib": (vm.total - vm.available) / (2 ** 30),
        }
    except Exception:  # noqa: BLE001
        return {"total_gib": 0.0, "available_gib": 0.0, "used_gib": 0.0}


def _replay_fixed_params_snapshot(cfg_path: Path) -> dict[str, Any]:
    """Run the INCUMBENT (actual-contract) params over one representative
    validation session and snapshot trades / daily equity / realized PnL.

    Used by the companion parity check to confirm worker-count is a side
    channel: the fixed-parameter output is deterministic, so it must be
    byte-equal across worker counts. ``run_backtest`` is keyword-only and
    needs the full supplier + universe + session set, so this builds them
    (one session = bounded cost) exactly like the lab's fold path does.
    """
    try:
        import pandas as pd

        from bowaka_common.marketdata import MarketDataStore
        from bowaka_v2_lab.config import load_config
        from bowaka_v2_lab.config.paths import BowakaV2Paths
        from bowaka_v2_lab.data.lineage import resolve_lake_root
        from bowaka_v2_lab.data.suppliers import (
            build_daily_cache_from_lake, make_forward_minute_supplier,
            make_lake_suppliers, make_quote_supplier,
            resolve_intraday_window_policy,
        )
        from bowaka_v2_lab.optuna.calendar_sessions import calendar_sessions_half_open
        from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
        from bowaka_v2_lab.optuna.walkforward_runner import (
            _incumbent_baseline_params, apply_trial_params,
        )
        from bowaka_v2_lab.sim.backtester import run_backtest
        from bowaka_v2_lab.sim.schedule import scan_times_for_session
        from bowaka_v2_lab.universe.builder import (
            build_pit_universe_for_sessions, eligible_symbols,
        )

        cfg = load_config(cfg_path)
        lake_root = resolve_lake_root(cfg)
        feed = str((cfg.get("market_data") or {}).get("feed", "iex"))
        bt = cfg.get("backtest") or {}
        wf = (cfg.get("optuna") or {}).get("walkforward") or {}
        plan = build_walkforward_splits(
            full_start=pd.Timestamp(bt["start_date"]).date(),
            full_end=pd.Timestamp(bt["end_date"]).date(),
            train_months=int(wf.get("train_months", 6)),
            val_months=int(wf.get("val_months", 1)),
            final_holdout_months=int(wf.get("final_holdout_months", 1)),
        )
        split = plan.splits[0]
        session = calendar_sessions_half_open(split.val_start, split.val_end)[0]

        cfg = dict(cfg)
        cfg["optuna"] = dict(cfg.get("optuna") or {})
        cfg["optuna"]["acceleration"] = {"scan_matrix": {"enabled": False}}

        store = MarketDataStore(lake_root)
        pit = build_pit_universe_for_sessions([session], dict(cfg), store)
        syms = sorted(eligible_symbols(pit.get(session, {})) or [])
        policy = resolve_intraday_window_policy(cfg)
        minute_sup, daily_sup = make_lake_suppliers(
            lake_root, feed=feed, intraday_window_policy=policy,
        )
        quote_sup = make_quote_supplier(lake_root, feed=feed, default_max_age_seconds=60.0)
        fwd_sup = make_forward_minute_supplier(lake_root, feed=feed)
        daily_cache = build_daily_cache_from_lake(lake_root, syms, session, feed=feed)
        universe = {session: {
            "universe_hash": "sha256:parity",
            "symbols": [
                {"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                 "instrument_class": "operating_equity",
                 "eligible_for_bowaka_equity_bucket": True}
                for s in syms
            ],
        }}
        cfg_inc = apply_trial_params(cfg, _incumbent_baseline_params())
        repo_root = Path(__file__).resolve().parents[5]
        paths = BowakaV2Paths.from_config(cfg_inc, repo_root=repo_root)
        result = run_backtest(
            cfg=cfg_inc, sessions=[session],
            scan_times_per_session=lambda d: list(scan_times_for_session(d, dict(cfg_inc))),
            universe_snapshot_by_session=universe,
            daily_cache_by_session={session: daily_cache},
            minute_bars_supplier=minute_sup, daily_bars_supplier=daily_sup,
            quote_supplier=quote_sup, forward_minute_supplier=fwd_sup,
            initial_bankroll=100_000.0, paths=paths,
            artifact_mode="objective_minimal",
        )
        eq = result.daily_equity or []
        trade_pnls = [round(float(t.get("pnl", 0.0)), 9) for t in result.trades]
        return {
            "session": session.isoformat(),
            "trades_count": len(result.trades),
            "trade_pnls": trade_pnls,
            "candidate_events": len(result.candidate_events),
            "daily_equity_first_last": [
                round(float(eq[0]["bankroll"]), 9) if eq else None,
                round(float(eq[-1]["bankroll"]), 9) if eq else None,
            ],
            "final_pnl": round(sum(trade_pnls), 9),
        }
    except Exception as exc:  # noqa: BLE001 — record but never abort the sweep
        return {"replay_error": str(exc)[:500]}


def _build_ceiling_config(
    src_config: Path, ceiling: int, storage_uri: str, out_dir: Path,
) -> Path:
    """Write a temp config = ``src_config`` with parallel.max_workers raised to
    ``ceiling`` and storage hardcoded, so the worker-count sweep is not clamped
    by the source ceiling. Everything else (cache flags, reserve, strict) kept.
    """
    import yaml

    cfg = yaml.safe_load(src_config.read_text(encoding="utf-8"))
    opt = cfg.setdefault("optuna", {})
    parallel = opt.setdefault("parallel", {})
    parallel["max_workers"] = int(ceiling)
    # Hardcode storage so the host-run benchmark hits the host-mapped PG port
    # (the config's ${OPTUNA_STORAGE:-...optuna-postgres:5432...} default only
    # resolves inside the docker network).
    opt["storage"] = storage_uri
    dest = out_dir / f"_benchmark_config_max{int(ceiling)}w.yml"
    dest.write_text(yaml.safe_dump(cfg, sort_keys=True), encoding="utf-8")
    return dest


def _get_study_names(storage_uri: str) -> set[str]:
    """All Optuna study names currently in the storage (empty set on error)."""
    try:
        import optuna

        return set(optuna.study.get_all_study_names(storage=storage_uri))
    except Exception:  # noqa: BLE001
        return set()


def _delete_study(study_name: str, storage_uri: str) -> bool:
    """Delete one Optuna study; True on success, False if absent / error."""
    try:
        import optuna

        optuna.delete_study(study_name=study_name, storage=storage_uri)
        return True
    except Exception:  # noqa: BLE001
        return False


def _run_one_worker_count(
    *,
    cfg_path: Path,
    n_trials: int,
    n_workers: int,
    capture_fixed_replay: bool,
    storage_uri: str,
    preexisting_studies: set[str],
) -> dict[str, Any]:
    """One pass through the sweep at a single worker count.

    Each worker count runs a FRESH study: the config's study name is keyed on
    feed/cost_stress/dataset_hash/date (not the worker count), so every
    iteration would otherwise resume one shared study. We isolate each run by
    deleting the iteration's own study afterwards (and refusing to count a run
    that resumed a pre-existing study). The ``current_code_parity`` opt-in
    flags are required or ``run_walkforward_study`` hard-refuses this config.
    """
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study
    from bowaka_v2_lab.utils.profile_counters import (
        ProfileCounters, profile_counters_context, set_counters_enabled,
    )

    set_counters_enabled(True)
    counters = ProfileCounters()
    mem_start = _system_memory_snapshot()
    wall_start = time.perf_counter()
    status = "ok"
    error: str | None = None
    result: dict[str, Any] | None = None
    completed_trials = 0
    best_value: float | None = None
    study_name: str | None = None
    with profile_counters_context(counters, enable=True):
        try:
            result = run_walkforward_study(
                cfg_path, n_trials=n_trials, n_jobs=n_workers,
                # The workstation config is current_code_parity; the study
                # runner refuses it without this explicit research-only opt-in.
                allow_current_code_parity_study=True,
                tier="research_only",
            )
            status = result.get("status", "ok")
            best_value = result.get("best_value")
            # The result key is ``n_trials_completed`` (not completed_trials).
            completed_trials = int(
                result.get("n_trials_completed", result.get("completed_trials", n_trials))
            )
            study_name = result.get("study_name")
        except Exception as exc:  # noqa: BLE001
            status = "error"
            error = str(exc)[:500]
    wall_end = time.perf_counter()
    mem_end = _system_memory_snapshot()

    # Isolate this iteration: a fresh study per worker count. If the study we
    # ran already existed before the sweep, this run RESUMED stale trials — its
    # timing is not a clean per-worker-count measurement; mark it.
    resumed_stale = bool(study_name and study_name in preexisting_studies)
    if study_name and not resumed_stale:
        _delete_study(study_name, storage_uri)
    if resumed_stale and status == "ok":
        status = "contaminated_preexisting_study"

    wall = wall_end - wall_start
    per_trial = wall / max(1, completed_trials) if completed_trials else None

    out: dict[str, Any] = {
        "n_workers": int(n_workers),
        "status": status,
        "best_value": best_value,
        "study_name": study_name,
        "wall_seconds": float(wall),
        "completed_trials": int(completed_trials),
        "trials_per_hour": float(completed_trials * 3600.0 / wall) if wall > 0 else 0.0,
        "p50_trial_seconds": per_trial,
        "peak_rss_gib": _peak_rss_gib(),
        "memory_at_start": mem_start,
        "memory_at_end": mem_end,
        "min_memory_available_gib": min(
            mem_start.get("available_gib", 0.0),
            mem_end.get("available_gib", 0.0),
        ),
        "counters": counters.snapshot(),
        "captured_at_utc": _dt.datetime.utcnow().isoformat() + "Z",
    }
    if error is not None:
        out["error"] = error
    if capture_fixed_replay:
        out["fixed_replay_snapshot"] = _replay_fixed_params_snapshot(cfg_path)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config", required=True, type=Path,
        help="Path to the walk-forward config (typically the workstation overlay).",
    )
    p.add_argument(
        "--n-trials", type=int, default=24,
        help="Per-worker-count trial budget. Default 24 keeps each worker at >=2 trials.",
    )
    p.add_argument(
        "--workers", default=",".join(str(c) for c in _DEFAULT_WORKER_COUNTS),
        help="Comma-separated worker counts to sweep (e.g. 1,4,8,10,12).",
    )
    p.add_argument(
        "--output", default=None, type=Path,
        help="Output directory. Defaults to ``artifacts/benchmarks/``.",
    )
    p.add_argument(
        "--no-replay", action="store_true",
        help="Skip the fixed-parameter replay snapshot (faster, no parity data).",
    )
    p.add_argument(
        "--storage", default=None,
        help="Optuna storage URL. Default: $OPTUNA_STORAGE or "
             "postgresql+psycopg2://optuna:optuna@localhost:5433/optuna "
             "(the host-mapped port of the optuna-postgres container).",
    )
    args = p.parse_args(argv)

    out_dir = args.output or (
        Path(args.config).resolve().parent.parent / "artifacts" / "benchmarks"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = [int(c.strip()) for c in str(args.workers).split(",") if c.strip()]

    # Resolve the storage URL (host-run benchmark -> host-mapped PG port).
    storage_uri = (
        args.storage
        or os.environ.get("OPTUNA_STORAGE")
        or "postgresql+psycopg2://optuna:optuna@localhost:5433/optuna"
    )

    # Build a temp config that raises the parallel.max_workers CEILING to the
    # largest swept worker count + hardcodes the resolved storage, so the
    # ``effective_n_jobs = min(n_jobs, max_workers)`` clamp does not cap the
    # high worker counts back to the config's default ceiling. Everything else
    # (cache flags, memory_reserve_gib, strict_parallel) is preserved.
    bench_cfg_path = _build_ceiling_config(
        Path(args.config), max(counts), storage_uri, out_dir,
    )
    print(f"[worker_count_matrix] benchmark config -> {bench_cfg_path}")
    print(f"[worker_count_matrix] storage -> {storage_uri}")

    # Studies that already exist must NOT be deleted (they may be the
    # operator's). A run that resumes one of these is flagged, not counted.
    preexisting_studies = _get_study_names(storage_uri)

    started_at = _dt.datetime.utcnow()
    matrix: list[dict[str, Any]] = []
    for n_workers in counts:
        print(f"[worker_count_matrix] n_workers={n_workers} starting ...")
        rec = _run_one_worker_count(
            cfg_path=bench_cfg_path,
            n_trials=int(args.n_trials),
            n_workers=n_workers,
            capture_fixed_replay=not args.no_replay,
            storage_uri=storage_uri,
            preexisting_studies=preexisting_studies,
        )
        matrix.append(rec)
        side = out_dir / f"worker_count_matrix__n{n_workers:02d}.json"
        side.write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
        print(
            f"[worker_count_matrix] n_workers={n_workers} status={rec['status']} "
            f"wall={rec['wall_seconds']:.1f}s trials_per_hour="
            f"{rec['trials_per_hour']:.2f}"
        )

    timestamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    out = out_dir / f"worker_count_matrix_{timestamp}.json"
    out.write_text(
        json.dumps(
            {
                "started_at_utc": started_at.isoformat() + "Z",
                "config": str(args.config),
                "benchmark_config": str(bench_cfg_path),
                "storage": storage_uri,
                "worker_counts": counts,
                "n_trials_per_worker_count": int(args.n_trials),
                "results": matrix,
            },
            indent=2, default=str,
        ),
        encoding="utf-8",
    )
    print(f"[worker_count_matrix] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
