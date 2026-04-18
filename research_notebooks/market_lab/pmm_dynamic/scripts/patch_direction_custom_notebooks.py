"""Patch cells 12 (all 4) and 14 (retest only) in the direction-custom notebooks.

Replaces stale bracket-access patterns (r["trading_pair"], r["best_score"],
binding_frac) with validation-status-aware, .get()-fallback versions. Adds
stable cell IDs via nbformat.validator.normalize. Commit the resulting diffs.

Run once after any generator update:
    python scripts/patch_direction_custom_notebooks.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent.parent / "notebooks" / "direction-custom"

ALL_NBS = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]
RETEST_NBS = [nb for nb in ALL_NBS if "retest" in nb]


def _is_mr(nb_name: str) -> bool:
    return "mean_reversion_bb_rsi" in nb_name


CELL12_MR = """# Profitable candidates — only those that passed validation gates (ML-DIR-001)
profitable = [
    r for r in sweep_results
    if r.get("validation_status", r.get("status")) in ("validated_pass", "complete")
    and r.get("robust_score", 0.0) is not None
    and r.get("robust_score", 0.0) > 0
]
print(f"\\n{'='*60}")
print(f"Profitable & validated pairs: {len(profitable)}")
print(f"{'='*60}")

# Informational release gates. None are blocking (already enforced in the pipeline).
print("\\nRelease Gates (Informational Only):")
for r in profitable:
    pair = r.get("pair", r.get("trading_pair", "?"))
    print(f"\\n  {r['connector']} / {pair}:")
    rs = r.get("robust_score", 0.0)
    brf = r.get("total_reject_fraction")
    gates = [
        ("robust_score > 0", rs, 0.0, rs is not None and rs > 0),
    ]
    if brf is not None:
        gates.append(
            ("order_reject_fraction < 0.30", brf, 0.30, brf < 0.30),
        )
    for name, actual, threshold, passed in gates:
        mark = "PASS" if passed else "FAIL"
        print(f"    [{mark}] {name}: actual={actual}")
"""

CELL12_EMA = """# Profitable candidates — only those that passed validation gates (ML-DIR-001)
profitable = [
    r for r in sweep_results
    if r.get("validation_status", r.get("status")) in ("validated_pass", "complete")
    and r.get("robust_score", 0.0) is not None
    and r.get("robust_score", 0.0) > 0
]
print(f"\\n{'='*60}")
print(f"Profitable & validated pairs: {len(profitable)}")
print(f"{'='*60}")

print("\\nRelease Gates (Informational Only):")
for r in profitable:
    pair = r.get("pair", r.get("trading_pair", "?"))
    print(f"\\n  {r['connector']} / {pair}:")
    rs = r.get("robust_score", 0.0)
    gates = [
        ("robust_score > 0", rs, 0.0, rs is not None and rs > 0),
    ]
    for name, actual, threshold, passed in gates:
        mark = "PASS" if passed else "FAIL"
        print(f"    [{mark}] {name}: actual={actual}")
"""

CELL14 = """# ── CROSS-PAIR RANKING (ML-DIR-001, ML-DIR-003) ──
validated = [
    r for r in sweep_results
    if r.get("validation_status", r.get("status")) in ("validated_pass", "complete")
]
rejected = [
    r for r in sweep_results
    if r.get("validation_status", r.get("status")) == "validated_fail"
]

def _rs(r):
    v = r.get("robust_score")
    return v if isinstance(v, (int, float)) else float("-inf")

validated.sort(key=_rs, reverse=True)

print(f"\\n{'='*60}")
print(f"Cross-pair ranking by robust_score (best first)")
print(f"{'='*60}")
for rank, r in enumerate(validated, 1):
    pair = r.get("pair", r.get("trading_pair", "?"))
    rs = r.get("robust_score", 0.0)
    rs_s = f"{rs:>8.3f}" if isinstance(rs, (int, float)) else f"{'N/A':>8}"
    print(f"  #{rank:>2} {r['connector']:8s} {pair:15s} "
          f"robust_score={rs_s}  "
          f"yaml={r.get('yaml_path')}")

if rejected:
    print(f"\\n{'='*60}")
    print(f"Rejected candidates ({len(rejected)}) — YAML in rejected/ subdir")
    print(f"{'='*60}")
    for r in rejected:
        pair = r.get("pair", r.get("trading_pair", "?"))
        failed = r.get("mandatory_gates_failed", [])
        print(f"  {r['connector']:8s} {pair:15s} failed_gates={failed}")
"""


def _set_cell_source(cell: dict, new_src: str) -> None:
    """Write the cell's source as a list of lines (nbformat convention)."""
    # Normalize: split into lines, preserve final newline behavior
    lines = new_src.splitlines(keepends=True)
    cell["source"] = lines
    cell["outputs"] = []
    cell["execution_count"] = None


def _ensure_cell_ids(nb: dict) -> None:
    """Add missing cell IDs so nbformat validates cleanly.

    Uses nbformat.validator.normalize if available; else assigns deterministic
    ids based on index.
    """
    try:
        import nbformat
        nbformat.validator.normalize(nb)
    except Exception:
        # Fallback: assign deterministic ids
        for i, cell in enumerate(nb["cells"]):
            if "id" not in cell:
                cell["id"] = f"cell-{i:03d}"


def patch_notebook(path: Path) -> None:
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    is_mr = _is_mr(path.name)
    cell12_src = CELL12_MR if is_mr else CELL12_EMA

    if len(nb["cells"]) > 12:
        _set_cell_source(nb["cells"][12], cell12_src)

    if "retest" in path.name and len(nb["cells"]) > 14:
        _set_cell_source(nb["cells"][14], CELL14)

    _ensure_cell_ids(nb)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"patched {path.name} (cells 12{' + 14' if 'retest' in path.name else ''})")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for name in ALL_NBS:
        patch_notebook(NB_DIR / name)


if __name__ == "__main__":
    main()
