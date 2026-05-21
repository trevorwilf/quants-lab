#!/usr/bin/env python
"""Sequentially execute the bowaka_v2_lab notebooks via papermill.

Runs every notebook in this directory **except 02** (universe snapshot), in
order, and prints a pass/fail summary. Executed copies (with outputs) are
written to the output directory.

    python notebooks/run_all_notebooks.py                          # smoke / synthetic, fast
    python notebooks/run_all_notebooks.py --config <research.yml>   # run against the lake
    python notebooks/run_all_notebooks.py --optuna-trials 50        # deeper notebook-10 tune
    python notebooks/run_all_notebooks.py --skip 09                 # also skip notebook 09
    python notebooks/run_all_notebooks.py --list                    # list selection, run nothing

Run inside the ql-jupyter container (needs the quants-lab env + a python3 kernel).
Note: notebook 10 is a real walk-forward Optuna run — the slow one; --optuna-trials
controls how long it takes.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # research_notebooks/bowaka_v2_lab/notebooks
_LAB_ROOT = _HERE.parent

# 02 is excluded by request — run it on its own when you need a universe snapshot.
_ALWAYS_SKIP = ("02_universe_backfill_and_snapshot.ipynb",)


def _selected(extra_skip: list[str]) -> list[Path]:
    skips = list(_ALWAYS_SKIP) + list(extra_skip)
    selected = []
    for path in sorted(_HERE.glob("*.ipynb")):
        if any(path.name == s or path.name.startswith(s) for s in skips):
            continue
        selected.append(path)
    return selected


def _parameters(nb_name: str, *, config: str | None, optuna_trials: int) -> dict:
    """Per-notebook papermill parameters."""
    if nb_name.startswith("10_"):
        # Notebook 10 keeps its own walk-forward config; only bound the trial count.
        return {"N_TRIALS": optuna_trials}
    return {"CONFIG_PATH": config} if config else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run all v2 notebooks except 02, in order.")
    ap.add_argument("--config", default=None,
                    help="CONFIG_PATH for the backtest notebooks (default: each notebook's own)")
    ap.add_argument("--optuna-trials", type=int, default=5,
                    help="N_TRIALS for notebook 10 (default 5; raise for a real tune)")
    ap.add_argument("--skip", nargs="*", default=[], metavar="NAME",
                    help="extra notebooks to skip (name or numeric prefix, e.g. 09)")
    ap.add_argument("--out-dir", default=str(_LAB_ROOT / "artifacts" / "executed_notebooks"),
                    help="directory for the executed notebooks")
    ap.add_argument("--stop-on-error", action="store_true",
                    help="stop at the first failure (default: run all, then report)")
    ap.add_argument("--list", action="store_true", dest="list_only",
                    help="list the notebooks that would run, then exit")
    args = ap.parse_args(argv)

    notebooks = _selected(args.skip)
    if args.list_only:
        for nb in notebooks:
            print(nb.name)
        print(f"({len(notebooks)} notebook(s) selected; 02 excluded)")
        return 0
    if not notebooks:
        print("no notebooks selected")
        return 0

    try:
        import papermill as pm
    except ImportError:
        print("papermill is required (run inside the ql-jupyter container)", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"running {len(notebooks)} notebook(s); 02 excluded; output -> {out_dir}\n", flush=True)

    results: list[tuple[str, str, float, str]] = []
    for nb in notebooks:
        params = _parameters(nb.name, config=args.config, optuna_trials=args.optuna_trials)
        print(f">> {nb.name}   {params or '(defaults)'}", flush=True)
        started = time.time()
        try:
            pm.execute_notebook(
                str(nb),
                str(out_dir / nb.name),
                parameters=params,
                cwd=str(_LAB_ROOT),
                kernel_name="python3",
                progress_bar=False,
            )
            elapsed = time.time() - started
            results.append((nb.name, "OK", elapsed, ""))
            print(f"   OK   ({elapsed:.1f}s)\n", flush=True)
        except Exception as exc:  # noqa: BLE001 — one bad notebook must not abort the batch
            elapsed = time.time() - started
            tail = str(exc).strip().splitlines()
            msg = tail[-1][:200] if tail else type(exc).__name__
            results.append((nb.name, "FAIL", elapsed, msg))
            print(f"   FAIL ({elapsed:.1f}s): {msg}\n", flush=True)
            if args.stop_on_error:
                break

    n_ok = sum(1 for _, status, _, _ in results if status == "OK")
    print("=" * 64)
    for name, status, elapsed, err in results:
        print(f"  {status:4s}  {name}  ({elapsed:.1f}s)")
        if err:
            print(f"        {err}")
    print("=" * 64)
    print(f"{n_ok}/{len(results)} notebook(s) passed")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
