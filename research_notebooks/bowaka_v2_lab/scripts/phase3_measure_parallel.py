"""Phase 3 — measure serial vs parallel parity wall-clock on the golden window.

Must be run as a real script (not ``python -`` / a notebook): the parallel path
uses ``multiprocessing`` spawn, which re-imports the main module — hence the
``if __name__ == "__main__"`` guard. Usage::

    PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \\
      C:/Python312/python.exe research_notebooks/bowaka_v2_lab/scripts/phase3_measure_parallel.py 1 4
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from bowaka_common.marketdata.store import resolve_market_data_root
from bowaka_v2_lab.parity import run_parity
from bowaka_v2_lab.parity.golden_sample import (
    GOLDEN_COST_STRESS,
    GOLDEN_END,
    GOLDEN_START,
    GOLDEN_SYMBOLS,
)

_LAB = Path(__file__).resolve().parents[1]


def main() -> int:
    common = dict(
        start_date=GOLDEN_START, end_date=GOLDEN_END, symbols=list(GOLDEN_SYMBOLS),
        prod_config_path=_LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml",
        lab_config_path=_LAB / "configs" / "bowaka_v2_actual_iex_current_code.yml",
        lake_root=resolve_market_data_root(None, create=False),
        cost_stress=GOLDEN_COST_STRESS, python_exe=sys.executable,
        chunk_per_session=True, print_progress=False,
    )
    out = _LAB / "artifacts" / "parity" / "phase3_measure"
    workers = [int(x) for x in sys.argv[1:]] or [1, 4]
    for nw in workers:
        t0 = time.monotonic()
        rep = run_parity(**common, run_root=out / f"w{nw}", parallel_workers=nw)
        print(f"workers={nw}: {time.monotonic() - t0:5.1f}s  "
              f"prod={rep.prod_n_trades} lab={rep.lab_n_trades} "
              f"sessions={rep.n_sessions}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
