"""Run all bowaka_lab numbered notebooks (00-11) in order, unattended.

Designed for overnight runs. Each notebook is executed via
``jupyter nbconvert --to notebook --execute`` in a fresh subprocess. The
executed copy and a full per-notebook log are written to a timestamped
output directory under ``_notebook_runs/<YYYYMMDD_HHMMSS>/`` so successive
runs do not stomp on each other. A pass/fail summary is printed at the end.

Defaults are tuned for unattended use:

- Continue on failure (you want info on every notebook by morning, not just
  up to the first break). Pass ``--stop-on-error`` to abort instead.
- 30-minute timeout per notebook (override with ``--timeout``).
- Uses the ``python3`` kernel (matches the notebooks' kernelspec).

Usage examples::

    # Run every numbered notebook with defaults
    python scripts/run_all_notebooks.py

    # Skip the Alpaca-fetching backfill and the long Optuna walk-forward
    python scripts/run_all_notebooks.py --exclude 02_ 10_

    # Only run 03 + 04
    python scripts/run_all_notebooks.py --include 03_ 04_

    # Stop on the first failure
    python scripts/run_all_notebooks.py --stop-on-error

Exit code is 0 when every executed notebook succeeds, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DEFAULT_TIMEOUT_PER_NOTEBOOK = 1800  # 30 minutes


def find_notebooks(
    notebooks_dir: Path,
    include: list[str] | None,
    exclude: list[str],
) -> list[Path]:
    nbs = sorted(notebooks_dir.glob("[0-9][0-9]_*.ipynb"))
    if include:
        nbs = [n for n in nbs if any(pat in n.name for pat in include)]
    if exclude:
        nbs = [n for n in nbs if not any(pat in n.name for pat in exclude)]
    return nbs


def run_one_notebook(
    nb_path: Path,
    output_dir: Path,
    log_path: Path,
    timeout: int,
) -> tuple[bool, float, str]:
    """Execute ``nb_path`` via nbconvert. Returns (success, duration_s, summary_msg)."""
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        f"--ExecutePreprocessor.timeout={timeout}",
        "--ExecutePreprocessor.kernel_name=python3",
        f"--output-dir={output_dir}",
        f"--output={nb_path.stem}",
        str(nb_path),
    ]
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 60,  # safety margin over the in-kernel timeout
            cwd=nb_path.parent.parent,  # bowaka_lab/, so the bootstrap walk-up works
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        log_path.write_text(
            f"CMD: {' '.join(cmd)}\n\nTimed out after {elapsed:.1f}s\n",
            encoding="utf-8",
        )
        return False, elapsed, f"timed out after {elapsed:.0f}s"

    elapsed = time.time() - t0
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"CMD: {' '.join(cmd)}\n")
        f.write(f"RETURN CODE: {result.returncode}\n")
        f.write(f"ELAPSED: {elapsed:.1f}s\n\n")
        f.write("=== STDOUT ===\n")
        f.write(result.stdout or "")
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr or "")

    if result.returncode == 0:
        return True, elapsed, "ok"

    # Pull a short, useful tail from stderr (nbconvert prints the cell
    # traceback there). Fall back to stdout if stderr is empty.
    blob = (result.stderr or result.stdout or "").rstrip()
    tail_lines = blob.splitlines()[-8:]
    tail = "\n".join(tail_lines) if tail_lines else f"exit code {result.returncode}"
    return False, elapsed, tail


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run all bowaka_lab numbered notebooks in order. "
            "Writes executed notebooks + logs to a timestamped output dir."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--notebooks-dir",
        default=None,
        help="Directory of source notebooks (default: <bowaka_lab>/notebooks).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Where to write executed notebooks + logs "
            "(default: <bowaka_lab>/_notebook_runs/<timestamp>/)."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_PER_NOTEBOOK,
        help=f"Per-notebook timeout in seconds (default: {DEFAULT_TIMEOUT_PER_NOTEBOOK}).",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Abort after the first failing notebook (default: keep going).",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        metavar="PATTERN",
        help="Skip notebooks whose filename contains any of these substrings.",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        metavar="PATTERN",
        help="Only run notebooks whose filename contains any of these substrings.",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve()
    bowaka_root = here.parent.parent  # scripts/.. == bowaka_lab/

    notebooks_dir = (
        Path(args.notebooks_dir).resolve()
        if args.notebooks_dir
        else bowaka_root / "notebooks"
    )
    if not notebooks_dir.is_dir():
        print(f"ERROR: notebooks dir not found: {notebooks_dir}", file=sys.stderr)
        return 2

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = bowaka_root / "_notebook_runs" / stamp
    output_dir.mkdir(parents=True, exist_ok=True)

    notebooks = find_notebooks(notebooks_dir, args.include, args.exclude)
    if not notebooks:
        print(f"No notebooks matched in {notebooks_dir}", file=sys.stderr)
        return 1

    print("==> Bowaka notebook batch run")
    print(f"    started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    src:     {notebooks_dir}")
    print(f"    out:     {output_dir}")
    print(f"    count:   {len(notebooks)} notebook(s)")
    print(f"    timeout: {args.timeout}s per notebook")
    print(f"    on-fail: {'stop' if args.stop_on_error else 'continue'}\n")

    results: list[tuple[str, bool, float, str]] = []
    overall_t0 = time.time()
    for i, nb in enumerate(notebooks, 1):
        log = output_dir / f"{nb.stem}.log"
        prefix = f"[{i}/{len(notebooks)}] {nb.name}"
        print(f"{prefix} ... ", end="", flush=True)
        ok, dur, msg = run_one_notebook(nb, output_dir, log, args.timeout)
        status = "OK  " if ok else "FAIL"
        print(f"{status} ({dur:.1f}s)")
        if not ok:
            indented = "    " + msg.replace("\n", "\n    ")
            print(indented)
            print(f"    full log: {log}")
        results.append((nb.name, ok, dur, msg))
        if not ok and args.stop_on_error:
            print(f"\n[stop-on-error] Aborting after {nb.name}")
            break

    overall = time.time() - overall_t0

    print("\n" + "=" * 70)
    print(f"Summary  ({overall:.1f}s total, finished {datetime.now().strftime('%H:%M:%S')})")
    print("=" * 70)
    n_ok = sum(1 for _, ok, _, _ in results if ok)
    n_fail = sum(1 for _, ok, _, _ in results if not ok)
    for name, ok, dur, _msg in results:
        marker = "OK  " if ok else "FAIL"
        print(f"  [{marker}] {dur:>7.1f}s  {name}")
    print(f"\nPassed: {n_ok}    Failed: {n_fail}    Total: {len(results)}")
    print(f"Output dir: {output_dir}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
