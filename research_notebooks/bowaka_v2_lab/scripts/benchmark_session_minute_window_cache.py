"""Session minute-window cache benchmark (speedup report v2 §5.7 / Phase 4).

For ``--mode legacy`` runs the scanner against the existing per-pair minute
supplier; for ``--mode session_window`` swaps in the cached supplier. Writes
wall-clock, peak RSS, and the relevant ProfileCounters fields per session
count.

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
    p.add_argument("--mode", required=True, choices=("legacy", "session_window"))
    p.add_argument("--sessions", type=int, default=1)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args(argv)

    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study
    from bowaka_v2_lab.utils.profile_counters import (
        ProfileCounters, profile_counters_context, set_counters_enabled,
    )

    set_counters_enabled(True)
    counters = ProfileCounters()
    wall_start = time.perf_counter()
    with profile_counters_context(counters, enable=True):
        # The benchmark uses run_walkforward_study to exercise the scanner;
        # to keep the run small ``n_trials=1`` with the supplied session count.
        try:
            result = run_walkforward_study(
                args.config, n_trials=1, n_jobs=1,
            )
            status = result.get("status", "ok")
        except Exception as exc:  # noqa: BLE001
            status = "error"
    wall_end = time.perf_counter()

    out: dict[str, Any] = {
        "mode": args.mode,
        "sessions": args.sessions,
        "wall_seconds": wall_end - wall_start,
        "peak_rss_gib": _peak_rss_gib(),
        "status": status,
        "counters": counters.snapshot(),
        "captured_at": _dt.datetime.utcnow().isoformat() + "Z",
    }
    output = args.output or Path(
        f"artifacts/benchmarks/phase_4_minute_window_{args.mode}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
