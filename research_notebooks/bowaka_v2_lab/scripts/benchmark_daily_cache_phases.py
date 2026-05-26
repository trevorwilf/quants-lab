"""Daily-cache phase benchmark (speedup report v2 §5.3 / Phase 1 task 6).

Runs ``build_fold_contexts`` for the requested mode (``legacy`` per-session
loop vs ``batch`` one-shot) and writes a JSON snapshot with wall-clock seconds,
peak RSS, profile counters, and the per-mode parquet-read totals.

Not asserted by any unit test — operator-driven sweep. Output lands at
``artifacts/benchmarks/phase_1_daily_cache_<mode>.json`` (gitignored).
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
    p.add_argument("--mode", required=True, choices=("legacy", "batch"))
    p.add_argument("--folds", type=int, default=1)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args(argv)

    # Lazy imports so a quick --help does not pay the cost.
    from bowaka_v2_lab.config.loader import load_config
    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.config.simulation import SimulationConfig
    from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
    from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
    from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
    from bowaka_v2_lab.optuna.walkforward_runner import _resolve_symbols, _to_date
    from bowaka_v2_lab.utils.profile_counters import (
        ProfileCounters, profile_counters_context, set_counters_enabled,
    )

    cfg = load_config(args.config)
    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
    optuna_cfg = cfg.get("optuna") or {}
    wf = optuna_cfg.get("walkforward") or {}
    bt = cfg.get("backtest") or {}
    md = cfg.get("market_data") or {}

    plan = build_walkforward_splits(
        full_start=_to_date(bt["start_date"]),
        full_end=_to_date(bt["end_date"]),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    feed = str(md.get("feed", "iex"))
    lake_root = md.get("shared_root")
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    paths = BowakaV2Paths.from_config(
        cfg, repo_root=Path(__file__).resolve().parents[3],
    )
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    # Flip the config flag based on --mode.
    cfg.setdefault("optuna", {}).setdefault("acceleration", {})[
        "batch_daily_cache"
    ] = {"enabled": args.mode == "batch"}

    # Limit to the first ``--folds`` splits for the benchmark.
    if args.folds > 0:
        plan.splits = plan.splits[: args.folds]

    set_counters_enabled(True)
    counters = ProfileCounters()
    wall_start = time.perf_counter()
    with profile_counters_context(counters, enable=True):
        contexts = build_fold_contexts(
            cfg, plan, lake_root=lake_root, feed=feed, symbols=symbols,
            paths=paths, holdout_guard=holdout_guard,
        )
    wall_end = time.perf_counter()

    out: dict[str, Any] = {
        "mode": args.mode,
        "config": str(args.config),
        "folds": len([c for c in contexts if c is not None]),
        "wall_seconds": wall_end - wall_start,
        "peak_rss_gib": _peak_rss_gib(),
        "counters": counters.snapshot(),
        "captured_at": _dt.datetime.utcnow().isoformat() + "Z",
    }

    output = args.output or (
        paths.artifact_root / "benchmarks" / f"phase_1_daily_cache_{args.mode}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
