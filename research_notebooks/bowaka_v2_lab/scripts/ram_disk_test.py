"""4-vs-16 worker timing: host bind-mount lake vs container-native cache lake.

Run INSIDE the ql-jupyter container so /opt/market_data_cache is visible::

    docker exec ql-jupyter bash -lc "cd /quants-lab && \
      PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \
      /opt/conda/envs/quants-lab/bin/python \
      research_notebooks/bowaka_v2_lab/scripts/ram_disk_test.py"

Times run_parity only (universe build excluded) so it isolates the parallel
worker phase. Full PIT universe, ~20 XNYS sessions (enough to load 16 workers).
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import time
from pathlib import Path

from bowaka_v2_lab.parity import build_parity_universe, run_parity

_LAB = Path(__file__).resolve().parents[1]
PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"
LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_iex_current_code.yml"
START = dt.date(2026, 1, 2)
END = dt.date(2026, 1, 30)   # ~20 XNYS sessions
MAX_UNIV = int(os.environ.get("RAMTEST_MAX_UNIV", "300"))  # cap universe for fast iteration
# Optional: pass an explicit comma-separated symbol list to skip the serial
# build_parity_universe screen (a fixed pre-cost that does NOT scale with
# workers). Isolates the parallel-worker phase — the actual 4-vs-16 question.
_SYMS_ENV = os.environ.get("RAMTEST_SYMBOLS", "").strip()
EXPLICIT_SYMS = [s.strip().upper() for s in _SYMS_ENV.split(",") if s.strip()] or None

BIND = "/quants-lab/research_notebooks/market_data"
CACHE = "/opt/market_data_cache"


def _run(label: str, lake_root: str, workers: int) -> None:
    try:
        if EXPLICIT_SYMS:
            syms = EXPLICIT_SYMS
        else:
            syms = build_parity_universe(
                start_date=START, end_date=END,
                lab_config_path=LAB_CONFIG, lake_root=Path(lake_root),
                max_universe_size=MAX_UNIV,
            )
        t0 = time.monotonic()
        rep = run_parity(
            start_date=START, end_date=END, symbols=syms,
            prod_config_path=PROD_CONFIG, lab_config_path=LAB_CONFIG,
            lake_root=Path(lake_root), cost_stress="base",
            run_root=_LAB / "artifacts" / "parity" / f"ramtest_{label}",
            python_exe=sys.executable, chunk_per_session=True,
            parallel_workers=workers, print_progress=False,
        )
        secs = time.monotonic() - t0
        print(f"[{label:>10}] workers={workers:>2}  lake={'cache' if lake_root==CACHE else 'bind '}  "
              f"run_parity={secs:6.1f}s  sessions={rep.n_sessions} universe={len(syms)} "
              f"prod={rep.prod_n_trades} lab={rep.lab_n_trades}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[{label}] FAILED: {type(exc).__name__}: {exc}", flush=True)


if __name__ == "__main__":
    # combos via argv (default: cache-only, fast). Pass "bind" to include the
    # slow host-bind-mount baseline.
    want = set(sys.argv[1:]) or {"cache"}
    print(f"window {START}..{END}  full PIT universe  combos={sorted(want)}", flush=True)
    if "bind" in want:
        _run("bind_w16", BIND, 16)   # baseline: slow host bind-mount
    if "cache" in want:
        _run("cache_w16", CACHE, 16)  # fast: container-native cache
        _run("cache_w4", CACHE, 4)    # sweet-spot comparison
    print("DONE", flush=True)
