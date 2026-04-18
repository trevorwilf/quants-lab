"""Generate cell 10 source for direction-custom sweep notebooks.

Adds the compact sorted results table per prompt Section 6A while
preserving the status-counts + per-pair outcome log.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent


CELL10_SRC = r'''# Results summary — status counts, per-pair outcomes, and compact sorted table.
import os
from pathlib import Path

def _status_counts(rows):
    counts = {}
    for r in rows:
        counts[r.get("status", "?")] = counts.get(r.get("status", "?"), 0) + 1
    return counts

print("=" * 60)
print("SWEEP RESULTS SUMMARY")
print("=" * 60)
print("Status counts:", _status_counts(sweep_results))

print("\nPer-pair outcomes:")
for r in sweep_results:
    status = r.get("validation_status", r.get("status", "?"))
    conn = r.get("connector", "?")
    pair = r.get("pair", r.get("trading_pair", "?"))
    extras = ""
    if status in ("validated_pass", "complete"):
        extras = f" score={r.get('robust_score', r.get('best_score', 0)):.3f}  yaml={r.get('yaml_path')}"
    elif status == "validated_fail":
        failed = r.get("mandatory_gates_failed", [])
        extras = f" failed_gates={failed}  yaml={r.get('yaml_path')}"
    elif "reason" in r:
        extras = f" reason={r['reason']}"
    elif "error" in r:
        extras = f" error={str(r['error'])[:80]}"
    print(f"  [{status:20s}] {conn:8s} {pair:15s}{extras}")


# ── Compact sorted results table (ML-DIR-001, ML-DIR-003) ──
# Primary: validation_status == validated_pass (or legacy "complete").
# Secondary: validation_status == validated_fail (rejected candidates).
_primary = [
    r for r in sweep_results
    if r.get("validation_status", r.get("status")) in ("validated_pass", "complete")
]
_rejected = [
    r for r in sweep_results
    if r.get("validation_status", r.get("status")) == "validated_fail"
]
_primary_sorted = sorted(
    _primary,
    key=lambda r: r.get("robust_score", float("-inf")) if r.get("robust_score") is not None else float("-inf"),
    reverse=True,
)
# Keep legacy name for back-compat with test fixtures that reference it
_completed_sorted = _primary_sorted

print("\n" + "=" * 100)
print("COMPACT RESULTS TABLE (sorted by robust_score descending)")
print("=" * 100)

_header = f"{'Rank':>4}  {'Connector':<10}  {'Pair':<18}  {'Robust':>8}  {'Holdout':>8}  {'Recent28d':>10}  {'Gates':>7}  {'DataDays':>8}  {'YAML'}"
print(_header)
print("-" * 100)

for _rank, _r in enumerate(_completed_sorted, start=1):
    _conn = _r.get("connector", "?")
    _pair = _r.get("pair", _r.get("trading_pair", "?"))
    _robust = _r.get("robust_score")
    _robust_s = f"{_robust:>8.4f}" if isinstance(_robust, (int, float)) else f"{'N/A':>8}"
    _hr = _r.get("holdout_report")
    if _hr is not None:
        _hs = getattr(_hr, "exported_holdout_score", None)
        _holdout_s = f"{_hs:>8.4f}" if isinstance(_hs, (int, float)) else f"{'N/A':>8}"
    else:
        _holdout_s = f"{'N/A':>8}"
    _rw = _r.get("recent_window_result")
    if _rw is not None and getattr(_rw, "objective", None) is not None:
        _rs = getattr(_rw.objective, "raw_score", None)
        _recent_s = f"{_rs:>10.4f}" if isinstance(_rs, (int, float)) else f"{'N/A':>10}"
    else:
        _recent_s = f"{'N/A':>10}"
    _checks = _r.get("checks") or {}
    _gp = sum(1 for v in _checks.values() if v)
    _gt = len(_checks) if _checks else 0
    _gates_s = f"{_gp}/{_gt}" if _gt else "N/A"
    _dd = _r.get("dataset_days")
    _datadays_s = f"{_dd:>6.0f}d" if isinstance(_dd, (int, float)) else f"{'N/A':>8}"
    _yaml = _r.get("yaml_path") or "-"
    _yaml_s = os.path.basename(_yaml) if _yaml != "-" else "-"
    print(f"{_rank:>4}  {_conn:<10}  {_pair:<18}  {_robust_s}  {_holdout_s}  {_recent_s}  {_gates_s:>7}  {_datadays_s:>8}  {_yaml_s}")

if not _completed_sorted:
    print("  (no validated pairs)")
print("=" * 100)

# Secondary: rejected candidates (validated_fail) with their failed gates.
if _rejected:
    print("\n" + "=" * 100)
    print(f"REJECTED CANDIDATES ({len(_rejected)}) — YAML under rejected/ subdir")
    print("=" * 100)
    for _r in _rejected:
        _conn = _r.get("connector", "?")
        _pair = _r.get("pair", _r.get("trading_pair", "?"))
        _failed = _r.get("mandatory_gates_failed", [])
        _yaml = _r.get("yaml_path") or "-"
        _yaml_s = os.path.basename(_yaml) if _yaml != "-" else "-"
        print(f"  {_conn:<10}  {_pair:<18}  failed_gates={_failed}  yaml={_yaml_s}")
    print("=" * 100)
'''


def write_cell10(nb_path: Path, new_source: str) -> int:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    nb["cells"][10]["source"] = new_source
    nb["cells"][10]["outputs"] = []
    nb["cells"][10]["execution_count"] = None
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    return len(new_source.splitlines())


def main():
    results = []
    for name in [
        "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "mean_reversion_bb_rsi_retest_sweep.ipynb",
        "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "ema_regime_hold_retest_sweep.ipynb",
    ]:
        path = NB_DIR / name
        lines = write_cell10(path, CELL10_SRC)
        results.append((name, lines))

    for name, lines in results:
        print(f"{name}: cell 10 = {lines} lines")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
