"""Worker-count sweep benchmark (speedup report v2 §5.4 / Phase 2 task 4).

For each worker count in ``--workers``, runs a walk-forward Optuna study at
``--trials`` trials over ``--folds`` validation folds and captures wall-clock,
peak RSS, profile counters, and the best objective. Writes one
``artifacts/benchmarks/phase_2_workers_<N>.json`` per run.

Operator-driven sweep — not asserted by any test.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from pathlib import Path
from typing import Any


def _peak_rss_gib() -> float:
    import os
    try:
        import resource

        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if ru > 2_000_000_000:
            return float(ru) / (2 ** 30)
        return float(ru * 1024) / (2 ** 30)
    except ImportError:
        pass
    try:
        import psutil  # type: ignore

        return float(psutil.Process(os.getpid()).memory_info().rss) / (2 ** 30)
    except Exception:  # noqa: BLE001
        return 0.0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True, type=Path)
    p.add_argument(
        "--workers", required=True,
        help="Comma-separated worker counts to sweep (e.g. 1,4,8,10,12,16)",
    )
    p.add_argument("--trials", type=int, default=8)
    p.add_argument("--folds", type=int, default=2)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    counts = [int(c.strip()) for c in args.workers.split(",") if c.strip()]
    out_dir = args.output_dir or (
        Path(args.config).resolve().parent.parent / "artifacts" / "benchmarks"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Lazy imports.
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study
    from bowaka_v2_lab.utils.profile_counters import (
        ProfileCounters, profile_counters_context, set_counters_enabled,
    )

    summary: list[dict[str, Any]] = []
    for n_workers in counts:
        set_counters_enabled(True)
        counters = ProfileCounters()
        wall_start = time.perf_counter()
        with profile_counters_context(counters, enable=True):
            try:
                result = run_walkforward_study(
                    args.config, n_trials=args.trials, n_jobs=n_workers,
                )
                status = result.get("status", "ok")
                best = result.get("best_value")
            except Exception as exc:  # noqa: BLE001 — record the error for the sweep
                status = "error"
                best = None
                result = {"error": str(exc)}
        wall_end = time.perf_counter()

        run_summary = {
            "n_workers": n_workers,
            "status": status,
            "best_value": best,
            "wall_seconds": wall_end - wall_start,
            "peak_rss_gib": _peak_rss_gib(),
            "counters": counters.snapshot(),
            "captured_at": _dt.datetime.utcnow().isoformat() + "Z",
        }
        if status == "error":
            run_summary["error"] = result.get("error")
        summary.append(run_summary)
        out = out_dir / f"phase_2_workers_{n_workers}.json"
        out.write_text(json.dumps(run_summary, indent=2, default=str), encoding="utf-8")
        print(f"[n_workers={n_workers}] wall={run_summary['wall_seconds']:.1f}s "
              f"best={best} status={status}")

    summary_path = out_dir / "phase_2_workers_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
