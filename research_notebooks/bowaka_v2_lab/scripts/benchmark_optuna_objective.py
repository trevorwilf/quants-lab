"""Benchmark one walk-forward objective fold (speedup report §10.0, §11.1).

Phase 0 ships this as the baseline-capture tool. It runs ``run_walkforward_study``
with one trial on the tiny synthetic lake (no IEX/SIP dependencies), with
:class:`ProfileCounters` active, and prints the snapshot + wall-clock seconds +
peak RSS + the final FoldResult. The baseline output is saved to
``artifacts/benchmarks/phase_0_baseline.json`` (gitignored) for later
comparison; nothing about the baseline is asserted in tests.

Usage::

    python scripts/benchmark_optuna_objective.py --out artifacts/benchmarks/phase_0_baseline.json

Re-run after each phase to compare wall-clock and supplier-call counts. The
final phase verification (after Phase 10) compares against the baseline.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import tempfile
import time
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/benchmarks/phase_0_baseline.json"),
        help="Output JSON path (relative to the lab dir)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Compare against an existing baseline file (does not assert).",
    )
    parser.add_argument("--n-trials", type=int, default=1)
    args = parser.parse_args(argv)

    from bowaka_v2_lab.devtools.wf_lake import (
        build_tiny_lake,
        write_walkforward_test_config,
    )
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study
    from bowaka_v2_lab.utils.profile_counters import profile_counters_context

    lab_root = Path.cwd()
    quarantined = (
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml"
    )
    if not quarantined.is_file():
        print(f"ERROR: required base config missing: {quarantined}", file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="bowaka_bench_"))
    lake = tmp / "lake"
    build_tiny_lake(
        lake, ["AAA"], start=_dt.date(2024, 1, 1), end=_dt.date(2024, 5, 1),
    )
    cfg = write_walkforward_test_config(
        quarantined,
        tmp / "wf.yml", lake=lake, symbols=["AAA"],
        start=_dt.date(2024, 1, 1), end=_dt.date(2024, 5, 1),
        n_trials=int(args.n_trials),
    )

    try:
        import psutil  # noqa: F401  (peak RSS query below requires psutil)
        proc = psutil.Process(os.getpid())
        peak_rss_bytes = int(proc.memory_info().rss)
    except Exception:  # noqa: BLE001 — psutil optional
        proc = None
        peak_rss_bytes = -1

    with profile_counters_context(enable=True) as counters:
        t0 = time.monotonic()
        result = run_walkforward_study(cfg, allow_smoke=True)
        wall = time.monotonic() - t0
        snapshot = counters.snapshot()

    if proc is not None:
        peak_rss_bytes = max(peak_rss_bytes, int(proc.memory_info().rss))

    report = {
        "phase": "phase_0_baseline",
        "wall_seconds": wall,
        "peak_rss_bytes": peak_rss_bytes,
        "n_trials": int(args.n_trials),
        "counters": snapshot,
        "study_status": result.get("status"),
        "study_best_value": result.get("best_value"),
        "study_n_folds": result.get("n_folds"),
        "study_n_trials_completed": result.get("n_trials_completed"),
    }
    out = (lab_root / args.out) if not args.out.is_absolute() else args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))

    if args.baseline is not None and args.baseline.is_file():
        try:
            base = json.loads(args.baseline.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — diagnostic only
            print(f"WARNING: could not read baseline {args.baseline}: {e}",
                  file=sys.stderr)
        else:
            print("\nDelta vs baseline:")
            print(f"  wall_seconds: {base.get('wall_seconds')} -> {wall:.3f}")
            for k in sorted(snapshot.keys()):
                print(f"  {k}: {base.get('counters', {}).get(k)} -> {snapshot[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
