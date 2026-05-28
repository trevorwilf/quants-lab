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
    """Run the actual contract params through one fold and snapshot equity / trades.

    Used by the companion parity check to assert worker-count is a side-
    channel: the fixed-parameter fold output should be byte-equal across
    worker counts.
    """
    try:
        from bowaka_v2_lab.config import load_config
        from bowaka_v2_lab.sim.backtester import run_backtest

        cfg = load_config(cfg_path)
        result = run_backtest(cfg)
        return {
            "trades_count": int(len(result.trades)) if hasattr(result, "trades") else 0,
            "daily_equity_first_last": [
                float(result.daily_equity.iloc[0]) if hasattr(result, "daily_equity") and len(result.daily_equity) > 0 else None,
                float(result.daily_equity.iloc[-1]) if hasattr(result, "daily_equity") and len(result.daily_equity) > 0 else None,
            ],
            "final_pnl": float(getattr(result, "final_pnl", 0.0)) if hasattr(result, "final_pnl") else None,
        }
    except Exception as exc:  # noqa: BLE001 — record but never abort the sweep
        return {"replay_error": str(exc)[:500]}


def _run_one_worker_count(
    *,
    cfg_path: Path,
    n_trials: int,
    n_workers: int,
    capture_fixed_replay: bool,
) -> dict[str, Any]:
    """One pass through the sweep at a single worker count."""
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
    with profile_counters_context(counters, enable=True):
        try:
            result = run_walkforward_study(
                cfg_path, n_trials=n_trials, n_jobs=n_workers,
            )
            status = result.get("status", "ok")
            best_value = result.get("best_value")
            completed_trials = int(result.get("completed_trials", n_trials))
        except Exception as exc:  # noqa: BLE001
            status = "error"
            error = str(exc)[:500]
    wall_end = time.perf_counter()
    mem_end = _system_memory_snapshot()

    wall = wall_end - wall_start
    per_trial = wall / max(1, completed_trials) if completed_trials else None

    out: dict[str, Any] = {
        "n_workers": int(n_workers),
        "status": status,
        "best_value": best_value,
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
    args = p.parse_args(argv)

    out_dir = args.output or (
        Path(args.config).resolve().parent.parent / "artifacts" / "benchmarks"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = [int(c.strip()) for c in str(args.workers).split(",") if c.strip()]
    started_at = _dt.datetime.utcnow()
    matrix: list[dict[str, Any]] = []
    for n_workers in counts:
        print(f"[worker_count_matrix] n_workers={n_workers} starting ...")
        rec = _run_one_worker_count(
            cfg_path=args.config,
            n_trials=int(args.n_trials),
            n_workers=n_workers,
            capture_fixed_replay=not args.no_replay,
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
