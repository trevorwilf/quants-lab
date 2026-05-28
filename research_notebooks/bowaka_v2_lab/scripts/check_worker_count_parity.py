"""Phase 2.5 §2 — verify the fixed-parameter replay snapshot is byte-equal
across worker counts.

A worker count N is "parity-clean" iff:
    - ``fixed_replay_snapshot`` is present and not an error;
    - its ``trades_count`` matches the reference (the n_workers=1 run);
    - its ``daily_equity_first_last`` matches the reference within
      1e-9 (objective tolerance) / 1e-12 (price tolerance);
    - ``final_pnl`` matches within 1e-9.

The script reads a matrix JSON, scores parity per worker count, and emits
``parity_clean: bool`` per row + an overall ``status`` field. Exit 0
when all surviving (status=ok) worker counts are parity-clean; non-zero
otherwise.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path
from typing import Any


_PRICE_TOLERANCE = 1e-12
_OBJECTIVE_TOLERANCE = 1e-9


def _close(a: float | None, b: float | None, *, tol: float) -> bool:
    if a is None or b is None:
        return a == b
    if math.isnan(a) and math.isnan(b):
        return True
    return abs(float(a) - float(b)) <= tol


def _replay_matches(
    reference: dict[str, Any] | None, candidate: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    """Compare a candidate replay snapshot to the reference."""
    if not isinstance(candidate, dict):
        return False, "candidate replay snapshot missing"
    if "replay_error" in candidate:
        return False, candidate["replay_error"]
    if not isinstance(reference, dict):
        return False, "reference replay snapshot missing"
    if "replay_error" in reference:
        return False, f"reference replay errored: {reference['replay_error']}"
    if candidate.get("trades_count") != reference.get("trades_count"):
        return False, (
            f"trades_count={candidate.get('trades_count')!r} "
            f"vs reference {reference.get('trades_count')!r}"
        )
    cand_eq = candidate.get("daily_equity_first_last") or []
    ref_eq = reference.get("daily_equity_first_last") or []
    if len(cand_eq) != len(ref_eq):
        return False, "daily_equity_first_last shape differs"
    for c, r in zip(cand_eq, ref_eq):
        if not _close(c, r, tol=_PRICE_TOLERANCE):
            return False, f"daily_equity {c} vs {r}"
    if not _close(
        candidate.get("final_pnl"), reference.get("final_pnl"),
        tol=_OBJECTIVE_TOLERANCE,
    ):
        return False, (
            f"final_pnl={candidate.get('final_pnl')!r} "
            f"vs reference {reference.get('final_pnl')!r}"
        )
    return True, None


def check_parity(matrix: dict[str, Any]) -> dict[str, Any]:
    """Score parity per worker count. Returns the augmented matrix dict."""
    results = list(matrix.get("results") or [])
    if not results:
        return {"status": "no_results", "results": []}
    # Reference: pick the lowest worker count with status == "ok" + replay
    # snapshot present.
    reference: dict[str, Any] | None = None
    for row in sorted(results, key=lambda r: int(r.get("n_workers") or 0)):
        if (
            row.get("status") == "ok"
            and isinstance(row.get("fixed_replay_snapshot"), dict)
            and "replay_error" not in row["fixed_replay_snapshot"]
        ):
            reference = row["fixed_replay_snapshot"]
            ref_n = int(row.get("n_workers") or 0)
            break
    if reference is None:
        for row in results:
            row["parity_clean"] = False
            row["parity_reason"] = "no clean replay snapshot to use as reference"
        return {
            "status": "no_reference",
            "results": results,
        }
    out_rows: list[dict[str, Any]] = []
    overall_ok = True
    for row in results:
        if row.get("status") != "ok":
            row["parity_clean"] = False
            row["parity_reason"] = f"worker-count run failed: status={row.get('status')!r}"
            overall_ok = False
            out_rows.append(row)
            continue
        clean, why = _replay_matches(reference, row.get("fixed_replay_snapshot"))
        row["parity_clean"] = bool(clean)
        row["parity_reason"] = None if clean else why
        if not clean:
            overall_ok = False
        out_rows.append(row)
    return {
        "status": "ok" if overall_ok else "fail",
        "reference_n_workers": ref_n,
        "results": out_rows,
    }


def _load_matrix_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input", required=True,
        help="Path or glob to ``worker_count_matrix_*.json``",
    )
    p.add_argument("--output", default=None, type=Path)
    args = p.parse_args(argv)

    candidates = sorted(glob.glob(str(args.input)))
    if not candidates:
        # Maybe a literal path.
        if Path(str(args.input)).is_file():
            candidates = [str(args.input)]
    if not candidates:
        print(f"no matrix JSON found for {args.input!r}", file=sys.stderr)
        return 2
    target = candidates[-1]  # newest
    matrix = _load_matrix_json(Path(target))
    report = check_parity(matrix)

    if args.output is not None:
        args.output.write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
