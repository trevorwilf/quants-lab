"""Phase 2.5 §3 — pick the parity-clean worker count with the best throughput.

Selection rules (in order):
    1. Filter out worker counts with ``status != "ok"`` OR worker failures
       (an ``error`` field) OR ``parity_clean == False``.
    2. If no survivors remain, fall back to ``n_workers=8`` and flag the
       decision as "fallback".
    3. Among survivors, pick the one with the highest ``trials_per_hour``.
    4. Tiebreaker: lower ``p50_trial_seconds``.
    5. Tiebreaker 2: lower ``peak_rss_gib``.

The decision is emitted as a single-line ``worker_count_winner.txt`` and
returned as a structured dict on stdout.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import sys
from pathlib import Path
from typing import Any


_FALLBACK_N_WORKERS = 8


def _is_survivor(row: dict[str, Any]) -> bool:
    if row.get("status") != "ok":
        return False
    if row.get("error"):
        return False
    if row.get("parity_clean") is False:
        return False
    return True


def select_winner(parity_report: dict[str, Any]) -> dict[str, Any]:
    """Pick the winner from a parity-augmented matrix report."""
    rows = list(parity_report.get("results") or [])
    survivors = [r for r in rows if _is_survivor(r)]
    if not survivors:
        return {
            "winner_n_workers": _FALLBACK_N_WORKERS,
            "reason": "no parity-clean worker count survived; fallback to 8",
            "fallback": True,
        }

    def _score(row: dict[str, Any]) -> tuple[float, float, float]:
        # Negate trials_per_hour so higher is better in the sort.
        trials_per_hour = float(row.get("trials_per_hour") or 0.0)
        p50 = float(row.get("p50_trial_seconds") or 1e9)
        rss = float(row.get("peak_rss_gib") or 1e9)
        return (-trials_per_hour, p50, rss)

    survivors.sort(key=_score)
    best = survivors[0]
    return {
        "winner_n_workers": int(best.get("n_workers")),
        "reason": (
            f"highest parity-clean trials_per_hour="
            f"{best.get('trials_per_hour'):.2f} "
            f"(p50_trial_seconds={best.get('p50_trial_seconds')!r}, "
            f"peak_rss_gib={best.get('peak_rss_gib'):.2f})"
        ),
        "fallback": False,
        "survivor_count": len(survivors),
        "all_n_workers_considered": [int(r.get("n_workers")) for r in rows],
    }


def _load_input(path_str: str) -> dict[str, Any]:
    candidates = sorted(glob.glob(path_str))
    if not candidates and Path(path_str).is_file():
        candidates = [path_str]
    if not candidates:
        raise FileNotFoundError(path_str)
    return json.loads(Path(candidates[-1]).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input", required=True,
        help="Path or glob to a parity-augmented matrix JSON.",
    )
    p.add_argument("--output", default=None, type=Path)
    args = p.parse_args(argv)

    matrix = _load_input(str(args.input))
    decision = select_winner(matrix)
    decision["captured_at_utc"] = _dt.datetime.utcnow().isoformat() + "Z"
    if args.output is not None:
        args.output.write_text(
            f"{decision['winner_n_workers']}\n"
            f"# Reason: {decision['reason']}\n"
            f"# Fallback: {decision['fallback']}\n"
            f"# Captured at: {decision['captured_at_utc']}\n",
            encoding="utf-8",
        )
    print(json.dumps(decision, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
