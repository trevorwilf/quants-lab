"""Microbenchmark the per-scan hot ops in isolation (no fold-context build) to
confirm where the controller_compat per-scan time goes and quantify the fix.

For a few real symbols over one session, replay the scan grid the way scan_loop
does — minute_bars_supplier(sym, scan_ts) then aggregate_forming_session_bar(bars)
— timing each leg, then compare against an INCREMENTAL aggregate (read the
session once, advance only the new bars). cProfile the replay to expose the
function-level hotspots.
"""
import cProfile
import io
import pstats
import sys
import time

import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.optuna.walkforward_runner import load_config  # noqa: E402
from bowaka_v2_lab.data.suppliers import make_lake_suppliers, resolve_intraday_window_policy  # noqa: E402
from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config  # noqa: E402
from bowaka_v2_lab.sim.schedule import scan_times_for_session  # noqa: E402
from bowaka_v2_lab.features.forming_bar import aggregate_forming_session_bar  # noqa: E402

LAKE = "/opt/market_data_cache"
cfg = load_config("/tmp/ir2m_smoke.yml")
SESSION = pd.Timestamp("2025-11-03").date()
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
SYMS = sorted({str(s) for s in cdf[cdf.daily_eligible == 1].symbol.dropna().unique()})[:8]

minute_supplier, _ = make_lake_suppliers(
    LAKE, feed="sip", intraday_window_policy=resolve_intraday_window_policy(cfg),
    daily_adjustment=daily_adjustment_for_config(cfg),
)
scans = list(scan_times_for_session(SESSION, cfg))
print(f"session {SESSION}  scans/session={len(scans)}  symbols={len(SYMS)}", flush=True)

# warm the per-symbol-month parquet cache so we measure compute, not cold disk
for sym in SYMS:
    minute_supplier(sym, scans[-1])


def replay_current(times=1):
    """The scan_loop way: re-fetch [09:45, t] + re-aggregate each scan -> O(scans^2)."""
    t_sup = t_agg = 0.0
    n = 0
    for _ in range(times):
        for sym in SYMS:
            for t in scans:
                a = time.perf_counter()
                bars = minute_supplier(sym, t)
                b = time.perf_counter()
                aggregate_forming_session_bar(bars)
                c = time.perf_counter()
                t_sup += (b - a); t_agg += (c - b); n += 1
    return t_sup, t_agg, n


def replay_incremental():
    """Read the whole session ONCE, advance running max/min/sum per scan -> O(scans)."""
    t0 = time.perf_counter()
    for sym in SYMS:
        full = minute_supplier(sym, scans[-1])  # all session bars once
        if full is None or len(full) == 0:
            continue
        cols = {c.lower(): c for c in full.columns}
        import numpy as np
        bar_ns = pd.to_datetime(full[cols["timestamp"]], utc=True).astype("int64").to_numpy()
        hi = full[cols["high"]].to_numpy(); lo = full[cols["low"]].to_numpy()
        vo = full[cols["volume"]].to_numpy(); cl = full[cols["close"]].to_numpy()
        op = full[cols["open"]].to_numpy()
        scan_ns = np.array([pd.Timestamp(t).tz_convert("UTC").value for t in scans], dtype="int64")
        idx = np.searchsorted(bar_ns, scan_ns, side="right")  # bars <= each scan
        run_h = -1e18; run_l = 1e18; run_v = 0.0; j = 0
        for k, t in enumerate(scans):
            end = idx[k]
            while j < end:                       # advance only NEW bars
                run_h = hi[j] if hi[j] > run_h else run_h
                run_l = lo[j] if lo[j] < run_l else run_l
                run_v += vo[j]; j += 1
            if j > 0:
                _ = {"session_open": float(op[0]), "session_high": run_h,
                     "session_low": run_l, "last_price": float(cl[j - 1]),
                     "session_volume": run_v, "session_range": run_h - run_l}
    return time.perf_counter() - t0


# 1) timing breakdown of the CURRENT per-scan path
t_sup, t_agg, n = replay_current(times=1)
print("\n=== CURRENT (re-fetch + re-aggregate per scan) ===")
print(f"  supplier fetch : {t_sup:.2f}s total  ({t_sup/n*1e6:.0f} us/scan)")
print(f"  aggregate bar  : {t_agg:.2f}s total  ({t_agg/n*1e6:.0f} us/scan)")
print(f"  per (sym*session): {(t_sup+t_agg)/len(SYMS)*1000:.0f} ms  -> x ~1150 syms x ~20 sess "
      f"= ~{(t_sup+t_agg)/len(SYMS)*1150*20/60:.0f} min/fold (this leg only)")

# 2) incremental alternative
t_inc = replay_incremental()
print("\n=== INCREMENTAL (read session once, advance running agg) ===")
print(f"  total          : {t_inc:.3f}s  ({t_inc/len(SYMS)*1000:.1f} ms/(sym*session))")
print(f"  SPEEDUP vs current fetch+agg: {(t_sup+t_agg)/max(t_inc,1e-9):.0f}x")

# 3) cProfile the current replay to expose function-level hotspots
pr = cProfile.Profile(); pr.enable(); replay_current(times=1); pr.disable()
buf = io.StringIO(); st = pstats.Stats(pr, stream=buf); st.sort_stats("tottime")
buf.write("\n===== cProfile: TOP 18 by self time (current per-scan replay) =====\n")
st.print_stats(18)
print(buf.getvalue())
