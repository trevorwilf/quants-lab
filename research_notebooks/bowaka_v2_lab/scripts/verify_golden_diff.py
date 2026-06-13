"""Verify the current code reproduces the Phase 0 golden parity baseline.

Re-runs production-vs-lab parity on the golden sample/window in BOTH chunk modes
with the CURRENT code, then diffs each result bundle against the committed golden
(``parity.golden.diff_parity_bundles``; price 1e-12 / pnl 1e-9). Exit 0 iff every
mode matches — the per-phase fidelity gate.

    PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \\
      C:/Python312/python.exe research_notebooks/bowaka_v2_lab/scripts/verify_golden_diff.py phase1
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from bowaka_common.marketdata.store import resolve_market_data_root
from bowaka_v2_lab.parity import run_parity
from bowaka_v2_lab.parity.golden import diff_parity_bundles
from bowaka_v2_lab.parity.golden_sample import (
    GOLDEN_COST_STRESS,
    GOLDEN_END,
    GOLDEN_START,
    GOLDEN_SYMBOLS,
)

_LAB = Path(__file__).resolve().parents[1]
LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_sip_current_code.yml"
PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"
GOLDEN_ROOT = _LAB / "artifacts" / "parity" / "golden"
VERIFY_ROOT = _LAB / "artifacts" / "parity" / "golden_verify"


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "current"
    lake_root = resolve_market_data_root(None, create=False)
    ok = True
    results: dict[str, dict] = {}
    for mode, chunk in (("chunked", True), ("nonchunked", False)):
        run_root = VERIFY_ROOT / label / mode / "run"
        bundle_out = VERIFY_ROOT / label / mode / "bundle"
        golden_bundle = GOLDEN_ROOT / mode / "bundle"
        if not (golden_bundle / "report.json").is_file():
            print(f"[{mode}] NO GOLDEN at {golden_bundle} — run phase0_capture_golden.py first",
                  flush=True)
            return 2
        print(f"\n=== verify [{label}/{mode}] re-running parity (current code) ===", flush=True)
        run_parity(
            start_date=GOLDEN_START, end_date=GOLDEN_END, symbols=list(GOLDEN_SYMBOLS),
            prod_config_path=PROD_CONFIG, lab_config_path=LAB_CONFIG,
            lake_root=lake_root, cost_stress=GOLDEN_COST_STRESS,
            run_root=run_root, python_exe=sys.executable, python_extra=(),
            timeout_sec=3600, chunk_per_session=chunk,
            bundle_out=bundle_out, print_progress=True,
        )
        d = diff_parity_bundles(golden_bundle, bundle_out)
        results[mode] = {
            "match": d["match"],
            "report_diffs": len(d["report_diffs"]),
            "trade_diffs": len(d["trade_diffs"]),
            "candidate_diffs": len(d["candidate_diffs"]),
        }
        print(f"[{mode}] {'MATCH' if d['match'] else 'DIFF'}: {results[mode]}", flush=True)
        if not d["match"]:
            ok = False
            print(json.dumps(d, indent=2, default=str)[:6000], flush=True)
    print("\nGOLDEN DIFF: " + ("ALL MATCH — gate PASS" if ok else "DIFFS FOUND — gate FAIL"),
          flush=True)
    print(json.dumps(results, indent=2), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
