#!/usr/bin/env python
"""Measure real per-trial walk-forward wall-clock + the 5000-trial budget.

Walk-forward scan-matrix speedup Phase 3. Runs a SMALL study against the matrix
overlay (default ``N_TRIALS=8``), reads the phase-profile JSON the runner
writes next to the study artifact, and prints:

    * mean / median per-trial wall-clock,
    * the per-phase second breakdown (``phase_seconds``),
    * the scanner work counters — ``scanner_symbols_seen`` (legacy per-symbol
      scan work; COLLAPSES to ~0 when the matrix is active) and
      ``matrix_scans_evaluated`` (scans served by the matrix runtime),
    * peak RSS,
    * the projected 5000-trial budget at the config's ``n_jobs``,
    * a one-line verdict vs the <=3 min/trial target.

``--legacy`` re-runs the same small study with ``runtime_mode=disabled`` (no
matrix) so the operator gets an A/B speedup ratio.

PRECONDITIONS (operator step — see docs/walkforward_scan_matrix_runbook.md):
the matrix overlay requires a built + verified validation matrix at its
``store_root``; without it the fold-context builder fails loud. Run from the
lab root with the lab importable, e.g.::

    cd research_notebooks/bowaka_v2_lab
    PYTHONPATH=src:../bowaka_common/src python scripts/benchmark_walkforward_trial.py \
        --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.yml \
        --n-trials 8 --legacy
"""
from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

_LAB_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    "configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.yml"
)
TARGET_SECONDS_PER_TRIAL = 180.0  # the <=3 min/trial hard goal


def _parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Benchmark per-trial walk-forward wall-clock against the matrix "
            "overlay and project the 5000-trial budget."
        ),
    )
    p.add_argument(
        "--config", default=DEFAULT_CONFIG,
        help="config to benchmark (default: the matrix enablement overlay).",
    )
    p.add_argument(
        "--n-trials", type=int, default=8,
        help="number of trials in the small benchmark study (default 8).",
    )
    p.add_argument(
        "--legacy", action="store_true",
        help="also run the same study with runtime_mode=disabled for an A/B "
             "speedup ratio (the legacy scanner, no matrix).",
    )
    p.add_argument(
        "--allow-smoke", action="store_true",
        help="pass allow_smoke=True (only for a smoke_fixture-mode config).",
    )
    p.add_argument(
        "--target-trials", type=int, default=5000,
        help="study size to project the budget for (default 5000).",
    )
    return p.parse_args(argv)


def _write_legacy_variant(config_path: Path, tmp_dir: Path) -> Path:
    """A copy of ``config_path`` with the scan-matrix runtime disabled."""
    import yaml

    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    sm = ((raw.get("optuna") or {}).get("acceleration") or {}).get("scan_matrix")
    if isinstance(sm, dict):
        sm["enabled"] = False
        sm["runtime_mode"] = "disabled"
    out = tmp_dir / "benchmark_legacy.yml"
    out.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return out


def _newest_phase_profile(artifact_root: Path) -> Path | None:
    cands = sorted(
        (artifact_root / "optuna").glob("*__phase_profile.json"),
        key=lambda p: p.stat().st_mtime,
    )
    return cands[-1] if cands else None


def _run_and_profile(config_path: Path, *, n_trials: int, allow_smoke: bool,
                     label: str) -> dict:
    """Run a small study and return a metrics dict read from the phase profile."""
    from bowaka_v2_lab.config import load_config
    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

    cfg = load_config(config_path)
    paths = BowakaV2Paths.from_config(cfg, repo_root=_LAB_ROOT.parents[1])
    artifact_root = Path(paths.artifact_root)
    n_jobs = int((cfg.get("optuna") or {}).get("n_jobs", 1))

    print(f"[{label}] running {n_trials}-trial study against {config_path.name} ...",
          flush=True)
    t0 = time.monotonic()
    result = run_walkforward_study(
        config_path, n_trials=n_trials, allow_smoke=allow_smoke,
    )
    wall = time.monotonic() - t0
    n_done = int(result.get("n_trials_completed", n_trials) or n_trials)

    prof_path = _newest_phase_profile(artifact_root)
    profile = json.loads(prof_path.read_text(encoding="utf-8")) if prof_path else {}
    phase_seconds = profile.get("phase_seconds", {})
    counters = profile.get("counters", {})
    rss_gib = (profile.get("memory") or {}).get("rss_peak_gib")

    optimize_s = float(phase_seconds.get("optuna_optimize", wall) or wall)
    per_trial = optimize_s / max(1, n_done)
    return {
        "label": label, "config": config_path.name, "n_jobs": n_jobs,
        "n_trials_completed": n_done, "wall_seconds": wall,
        "optimize_seconds": optimize_s, "per_trial_seconds": per_trial,
        "phase_seconds": phase_seconds, "counters": counters,
        "rss_peak_gib": rss_gib,
        "scanner_symbols_seen": counters.get("scanner_symbols_seen"),
        "matrix_scans_evaluated": counters.get("matrix_scans_evaluated"),
        "status": result.get("status"),
    }


def _print_metrics(m: dict, *, target_trials: int) -> None:
    print(f"\n===== {m['label']} ({m['config']}) =====")
    print(f"  status               : {m['status']}")
    print(f"  trials completed     : {m['n_trials_completed']}")
    print(f"  wall-clock total     : {m['wall_seconds']:.1f}s")
    print(f"  per-trial (optimize) : {m['per_trial_seconds']:.1f}s "
          f"(<=3min target = {TARGET_SECONDS_PER_TRIAL:.0f}s)")
    if m.get("rss_peak_gib") is not None:
        print(f"  peak RSS             : {m['rss_peak_gib']:.2f} GiB")
    print(f"  scanner_symbols_seen : {m['scanner_symbols_seen']} "
          "(legacy per-symbol scan work; ~0 when matrix active)")
    print(f"  matrix_scans_evaluated: {m['matrix_scans_evaluated']} "
          "(scans served by the matrix; 0 == matrix did NOT fire)")
    ph = m.get("phase_seconds") or {}
    if ph:
        print("  phase_seconds:")
        for k in sorted(ph, key=lambda k: -float(ph[k] or 0.0)):
            print(f"      {k:<28} {float(ph[k] or 0.0):8.1f}s")
    n_jobs = max(1, int(m["n_jobs"]))
    proj = target_trials * m["per_trial_seconds"] / n_jobs
    print(f"  projected {target_trials} trials @ n_jobs={n_jobs}: "
          f"{proj/3600:.1f}h ({proj/60:.0f} min wall-clock)")
    verdict = "MET" if m["per_trial_seconds"] <= TARGET_SECONDS_PER_TRIAL else "NOT MET"
    print(f"  VERDICT vs <=3min/trial: {verdict}")


def main(argv=None) -> int:
    args = _parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = _LAB_ROOT / config_path
    if not config_path.is_file():
        print(f"config not found: {config_path}", file=sys.stderr)
        return 2

    matrix_m = _run_and_profile(
        config_path, n_trials=args.n_trials, allow_smoke=args.allow_smoke,
        label="matrix",
    )
    _print_metrics(matrix_m, target_trials=args.target_trials)

    if args.legacy:
        with tempfile.TemporaryDirectory() as td:
            legacy_cfg = _write_legacy_variant(config_path, Path(td))
            legacy_m = _run_and_profile(
                legacy_cfg, n_trials=args.n_trials, allow_smoke=args.allow_smoke,
                label="legacy",
            )
        _print_metrics(legacy_m, target_trials=args.target_trials)
        if matrix_m["per_trial_seconds"] > 0:
            ratio = legacy_m["per_trial_seconds"] / matrix_m["per_trial_seconds"]
            print(f"\n===== A/B =====\n  matrix speedup vs legacy: {ratio:.1f}x "
                  f"({legacy_m['per_trial_seconds']:.1f}s -> "
                  f"{matrix_m['per_trial_seconds']:.1f}s per trial)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
