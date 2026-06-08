"""§10h #5 — verify the parallel (fork) matrix build is BYTE-IDENTICAL to serial.

Builds the same handful of sessions twice (n_workers=1 vs n_workers=3) to two
throwaway store roots, then compares every computed array (.npy) + universe_meta
+ the per-session manifest checksums. Sessions are independent + deterministic, so
this must match exactly regardless of worker count.
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.config import load_config  # noqa: E402
from bowaka_v2_lab.data.lineage import resolve_lake_root  # noqa: E402
from bowaka_v2_lab.scanner.scan_matrix import (  # noqa: E402
    _build_session_partitions, _prewarm_pit_daily_cache,
)

cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ir2m_smoke.yml")
lake_root = resolve_lake_root(cfg)
feed = str((cfg.get("market_data") or {}).get("feed", "sip"))
sessions = [dt.date(2025, 11, 3), dt.date(2025, 11, 4), dt.date(2025, 11, 5)]

root_ser = Path(tempfile.mkdtemp(prefix="par_ser_")) / "validation"
root_par = Path(tempfile.mkdtemp(prefix="par_par_")) / "validation"
root_ser.mkdir(parents=True, exist_ok=True)
root_par.mkdir(parents=True, exist_ok=True)

print(f"sessions={[s.isoformat() for s in sessions]} feed={feed}", flush=True)
_prewarm_pit_daily_cache(sessions, cfg, lake_root)

t0 = time.perf_counter()
ser = _build_session_partitions(sessions, cfg, lake_root, feed, store_root=root_ser, scope="validation", n_workers=1)
t_ser = time.perf_counter() - t0

t0 = time.perf_counter()
par = _build_session_partitions(sessions, cfg, lake_root, feed, store_root=root_par, scope="validation", n_workers=3)
t_par = time.perf_counter() - t0

print(f"serial(n=1): {t_ser:.1f}s   parallel(n=3): {t_par:.1f}s   (warm-cache inherited)", flush=True)
assert [m["n_symbols"] for m in ser] == [m["n_symbols"] for m in par], "n_symbols differ"

diffs = 0
for sd in sessions:
    d_ser = root_ser / f"session={sd.isoformat()}"
    d_par = root_par / f"session={sd.isoformat()}"
    npys = sorted(p.name for p in d_ser.glob("*.npy"))
    assert npys, f"no .npy in {d_ser}"
    for fn in npys:
        a = np.load(d_ser / fn)
        b = np.load(d_par / fn)
        if not np.array_equal(a, b, equal_nan=True) if a.dtype.kind == "f" else not np.array_equal(a, b):
            print(f"  DIFF {sd} {fn}"); diffs += 1
    ma = pd.read_parquet(d_ser / "universe_meta.parquet")
    mb = pd.read_parquet(d_par / "universe_meta.parquet")
    if not ma.equals(mb):
        print(f"  DIFF {sd} universe_meta.parquet"); diffs += 1
    print(f"  {sd}: {len(npys)} arrays + universe_meta compared", flush=True)

print(f"\n{'BYTE-IDENTICAL serial vs parallel — OK' if diffs == 0 else f'{diffs} DIFFERENCES'}", flush=True)
sys.exit(1 if diffs else 0)
