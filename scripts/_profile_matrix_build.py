"""Measure #5 — where the scan-matrix BUILD time goes: minute-bar IO
(store.minute_bars / pd.read_parquet, re-reading a symbol's whole month parquet
per session) vs the numba feature kernel vs the PIT-universe resolution.

cProfile build_session_partition for N sessions (full PIT universe) to a THROWAWAY
store root (does NOT touch /opt/scan_matrix_cache). Reports cumtime shares so the
single-read-and-slice + session-parallelism build-time win can be sized.
"""
from __future__ import annotations

import cProfile
import datetime as dt
import io
import pstats
import sys
import tempfile
import time
from pathlib import Path

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.config import load_config  # noqa: E402
from bowaka_v2_lab.data.lineage import resolve_lake_root  # noqa: E402
from bowaka_v2_lab.scanner.scan_matrix import build_session_partition  # noqa: E402

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ir2m_smoke.yml"
N_SESS = int(sys.argv[2]) if len(sys.argv) > 2 else 1

cfg = load_config(CONFIG)
lake_root = resolve_lake_root(cfg)
feed = str((cfg.get("market_data") or {}).get("feed", "sip"))
nb = (((cfg.get("optuna") or {}).get("acceleration") or {}).get("numba") or {})
sessions = [dt.date(2025, 11, 3), dt.date(2025, 11, 4), dt.date(2025, 11, 5)][:N_SESS]
store_root = Path(tempfile.mkdtemp(prefix="m5_matrix_")) / "validation"

print(f"config={CONFIG}  feed={feed}  numba.enabled={nb.get('enabled')}  "
      f"sessions={[s.isoformat() for s in sessions]}  store_root={store_root}", flush=True)

pr = cProfile.Profile()
pr.enable()
t0 = time.perf_counter()
nsyms = 0
for s in sessions:
    frag = build_session_partition(s, cfg, lake_root, feed, store_root=store_root, scope="validation")
    nsyms = frag.get("n_symbols", nsyms) if isinstance(frag, dict) else nsyms
wall = time.perf_counter() - t0
pr.disable()

st = pstats.Stats(pr)
total = st.total_tt
print(f"\nbuild wall (cProfiled): {wall:.1f}s for {len(sessions)} session(s)  "
      f"(~{wall/len(sessions):.1f}s/session)  total_tt={total:.1f}s", flush=True)

BUCKETS = {
    "minute IO (store.minute_bars)": [("store.py", "minute_bars")],
    "parquet read (pyarrow/pandas)": [("parquet", "read"), ("parquet", "_read"), ("parquet", "read_table")],
    "pd.read_parquet": [("", "read_parquet")],
    "numba kernel (build_session_columns_nb)": [("_numba_scan_features", "build_session_columns_nb")],
    "aggregate_forming_session_bar": [("forming_bar", "aggregate_forming_session_bar")],
    "compute_forming_session_features": [("forming_bar", "compute_forming_session_features")],
    "compute_volume_curve_fraction": [("", "compute_volume_curve_fraction")],
    "PIT universe (build_pit_universe_for_sessions)": [("", "build_pit_universe_for_sessions")],
    "daily IO (store.daily_bars)": [("store.py", "daily_bars")],
}
agg = {k: 0.0 for k in BUCKETS}
for (fn, lineno, func), (cc, nc, tt, ct, callers) in st.stats.items():
    base = str(fn).split("/")[-1].split("\\")[-1]
    for label, pats in BUCKETS.items():
        for fpat, fnpat in pats:
            if (fpat in base or fpat == "") and func == fnpat:
                agg[label] += ct  # cumulative (includes callees) — the right measure for IO/kernel cost
                break

print("\n=== build cumtime by stage (cumulative; shares of total_tt) ===")
for k, v in sorted(agg.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k:48s}: {v:8.2f}s  ({v/max(total,1e-9)*100:5.1f}%)")

buf = io.StringIO()
st2 = pstats.Stats(pr, stream=buf)
st2.sort_stats("cumulative")
buf.write("\n===== TOP 25 by CUMULATIVE time =====\n")
st2.print_stats(25)
st2.sort_stats("tottime")
buf.write("\n===== TOP 20 by tottime =====\n")
st2.print_stats(20)
print(buf.getvalue())
print("(cProfile inflates ~2x; read RELATIVE shares.)")
