"""Phase 0 — capture the golden parity baseline on a strategy-relevant sample.

Runs production-vs-lab parity on a fixed 40-symbol sample (chosen because the
strategy actually screens them in over the window, so the golden has real
signals + trades) across the golden window in BOTH chunk modes, and persists a
diffable golden bundle per mode under
``artifacts/parity/golden/{chunked,nonchunked}/bundle``.

Every later speedup phase re-runs parity with ``bundle_out=`` and asserts
``parity.golden.diff_parity_bundles(GOLDEN, run)["match"]`` — identical per-trade
rows, candidate stream, and report fields (price 1e-12, pnl 1e-9).

Run from anywhere; paths are resolved relative to this file. Invoke with the
deps-bearing interpreter so the prod subprocess inherits it, e.g.::

    PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \\
      C:/Python312/python.exe research_notebooks/bowaka_v2_lab/scripts/phase0_capture_golden.py
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

from bowaka_common.marketdata.store import resolve_market_data_root
from bowaka_v2_lab.parity import run_parity
from bowaka_v2_lab.parity.golden_sample import (
    GOLDEN_COST_STRESS as COST_STRESS,
    GOLDEN_END as END,
    GOLDEN_START as START,
    GOLDEN_SYMBOLS as SYMBOLS,
)

_LAB = Path(__file__).resolve().parents[1]
LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_sip_current_code.yml"
PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"
GOLDEN_ROOT = _LAB / "artifacts" / "parity" / "golden"


def main() -> int:
    lake_root = resolve_market_data_root(None, create=False)
    print(f"[golden] lake={lake_root}", flush=True)
    print(f"[golden] window={START}..{END}  symbols={len(SYMBOLS)}  cost_stress={COST_STRESS}",
          flush=True)
    summary: dict[str, dict] = {}
    for mode, chunk in (("chunked", True), ("nonchunked", False)):
        run_root = GOLDEN_ROOT / mode / "run"
        bundle_out = GOLDEN_ROOT / mode / "bundle"
        t0 = _dt.datetime.now()
        print(f"\n=== [{mode}] capturing golden (chunk_per_session={chunk}) at "
              f"{t0:%H:%M:%S} ===", flush=True)
        report = run_parity(
            start_date=START, end_date=END, symbols=SYMBOLS,
            prod_config_path=PROD_CONFIG, lab_config_path=LAB_CONFIG,
            lake_root=lake_root, cost_stress=COST_STRESS,
            run_root=run_root, python_exe=sys.executable, python_extra=(),
            timeout_sec=3600, chunk_per_session=chunk,
            bundle_out=bundle_out, print_progress=True,
        )
        secs = (_dt.datetime.now() - t0).total_seconds()
        summary[mode] = {
            "bundle": str(bundle_out),
            "elapsed_seconds": round(secs, 1),
            "prod_n_trades": report.prod_n_trades,
            "lab_n_trades": report.lab_n_trades,
            "n_sessions": report.n_sessions,
            "n_trade_sessions": report.n_trade_sessions,
            "trade_intersection_rate": report.trade_intersection_rate,
            "fill_price_mae_bps": report.fill_price_mae_bps,
            "passes_audit_thresholds": report.passes_audit_thresholds,
        }
        print(f"=== [{mode}] done in {secs/60:.1f} min: prod_trades={report.prod_n_trades} "
              f"lab_trades={report.lab_n_trades} "
              f"intersection={report.trade_intersection_rate:.4f} ===", flush=True)
    (GOLDEN_ROOT / "golden_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nGOLDEN CAPTURE COMPLETE -> {GOLDEN_ROOT}", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
