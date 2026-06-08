"""Measure the REAL (cached) minute supplier the study uses vs the raw fallback,
to settle per-scan-compute vs one-time-preload. The study wires
make_session_minute_window_supplier when session_minute_window_cache.enabled +
cached_suppliers (both true in ir2m.yml).
"""
import sys
import time

import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_common.marketdata import MarketDataStore  # noqa: E402
from bowaka_v2_lab.optuna.walkforward_runner import load_config  # noqa: E402
from bowaka_v2_lab.data.suppliers import make_lake_suppliers, resolve_intraday_window_policy  # noqa: E402
from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config  # noqa: E402
from bowaka_v2_lab.sim.schedule import scan_times_for_session  # noqa: E402
from bowaka_v2_lab.scanner.session_minute_window_supplier import make_session_minute_window_supplier  # noqa: E402

LAKE = "/opt/market_data_cache"
cfg = load_config("/tmp/ir2m_smoke.yml")
SESSION = pd.Timestamp("2025-11-03").date()
policy = resolve_intraday_window_policy(cfg)
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
SYMS = sorted({str(s) for s in cdf[cdf.daily_eligible == 1].symbol.dropna().unique()})[:8]
scans = list(scan_times_for_session(SESSION, cfg))

raw_sup, _ = make_lake_suppliers(LAKE, feed="sip", intraday_window_policy=policy,
                                 daily_adjustment=daily_adjustment_for_config(cfg))
for sym in SYMS:  # warm parquet cache for the raw path comparison
    raw_sup(sym, scans[-1])

# RAW path: per-scan call
t0 = time.perf_counter()
for sym in SYMS:
    for t in scans:
        raw_sup(sym, t)
raw_t = time.perf_counter() - t0

# CACHED path: build (preload) once, then per-scan calls
store = MarketDataStore(LAKE)
t0 = time.perf_counter()
cached_sup = make_session_minute_window_supplier(
    store, [SESSION], {SESSION: SYMS}, feed="sip",
    intraday_policy=policy, max_bar_age_seconds=None,
)
preload_t = time.perf_counter() - t0
t0 = time.perf_counter()
for sym in SYMS:
    for t in scans:
        cached_sup(sym, t)
cached_t = time.perf_counter() - t0

n = len(SYMS) * len(scans)
print(f"symbols={len(SYMS)}  scans={len(scans)}  total calls={n}\n")
print(f"RAW supplier (re-read per scan) : {raw_t:.2f}s  ({raw_t/n*1e6:.0f} us/scan)")
print(f"CACHED preload (one-time/fold)  : {preload_t:.3f}s  ({preload_t/len(SYMS)*1000:.0f} ms/symbol)")
print(f"CACHED per-scan (read-once+ss)  : {cached_t:.3f}s  ({cached_t/n*1e6:.0f} us/scan)")
print(f"\nper-scan SPEEDUP cached vs raw  : {raw_t/max(cached_t,1e-9):.0f}x")
print(f"break-even: preload pays off after {preload_t/max((raw_t-cached_t)/n,1e-12):.0f} scan-calls "
      f"(<< {len(scans)} scans/symbol * trials)")
