"""Scout quote_coverage before fanning out. (1) Reproduce the real
probe_quote_coverage 57.5%. (2) Measure proper quote coverage over PIT-eligible
(sym,session) pairs under several criteria, reading SIP quote parquets directly.

Criteria per eligible (sym, session), scan grid = scan_times_for_session (60s):
  middle_15s / middle_60s : a quote within 15s / 60s of the MIDDLE scan (the
      single instant the preflight probes).
  anyscan_15s             : EXISTS a scan t with a quote in [t-15s, t] (the sim
      re-scans 346x with require_real, so it can trade at SOME scan) -- the
      sim-faithful "tradable" metric.
  any_session_quote       : >=1 quote anywhere in [09:45, 15:30].
  scan_density_15s        : fraction of the 346 scans with a quote within 15s.
"""
import os
import sys
from collections import defaultdict

import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.optuna.walkforward_runner import load_config  # noqa: E402
from bowaka_v2_lab.optuna.pit_universe import eligible_per_session_map  # noqa: E402
from bowaka_v2_lab.sim.schedule import scan_times_for_session  # noqa: E402
from bowaka_v2_lab.data.suppliers import make_quote_supplier  # noqa: E402
from bowaka_v2_lab.optuna.preflight import probe_quote_coverage  # noqa: E402
from bowaka_v2_lab.universe.builder import eligible_symbols  # noqa: E402

LAKE = "/opt/market_data_cache"
Q = f"{LAKE}/quotes/vendor=alpaca/feed=sip"
cfg = load_config("/tmp/ir2m.yml")
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
sessions = sorted({pd.Timestamp(s).date() for s in cdf.session.unique()})[:5]
elig_map = eligible_per_session_map(LAKE, sessions, cfg=cfg)
elig_union = sorted({s for sd in sessions for s in elig_map.get(sd, set())})
full_union = sorted({str(s) for s in cdf.symbol.dropna().unique()})
print("sessions:", [s.isoformat() for s in sessions], "| eligible union:", len(elig_union), "| full union:", len(full_union))

# (1) reproduce the real probe_quote_coverage (full union, 200-cap, middle scan, 60s)
qs = make_quote_supplier(LAKE, feed="sip")
repro = probe_quote_coverage(symbols=full_union, sessions=sessions, quote_supplier=qs,
                             scan_times_per_session=lambda d: scan_times_for_session(d, cfg))
print("\n(1) probe_quote_coverage REPRODUCED (full union, 200-cap, 60s):  %.2f%%  (gate needs 95%%)" % repro)
# same but restricted to eligible union (still 200-cap, middle scan, 60s)
repro_e = probe_quote_coverage(symbols=elig_union, sessions=sessions, quote_supplier=qs,
                               scan_times_per_session=lambda d: scan_times_for_session(d, cfg))
print("    probe_quote_coverage on ELIGIBLE union (200-cap, 60s):         %.2f%%" % repro_e)

# (2) proper per-(sym,session) measurement over the FULL eligible set, reading quotes directly
_qcache = {}
def session_quote_times(sym, sd):
    key = (sym, sd.year, sd.month)
    if key not in _qcache:
        f = f"{Q}/symbol={sym}/year={sd.year:04d}/month={sd.month:02d}/part.parquet"
        if os.path.isfile(f):
            ts = pd.to_datetime(pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True)
            _qcache[key] = ts.dt.tz_convert("America/New_York")
        else:
            _qcache[key] = None
    allts = _qcache[key]
    if allts is None:
        return None
    return allts[allts.dt.date == sd]

def has_within(qt, scan_ts, secs):
    if qt is None or len(qt) == 0:
        return False
    lo = scan_ts - pd.Timedelta(seconds=secs)
    return bool(((qt >= lo) & (qt <= scan_ts)).any())

cats = defaultdict(int)
n = 0
miss_anyscan_examples = []
for sd in sessions:
    scans = list(scan_times_for_session(sd, cfg))
    mid = scans[len(scans) // 2]
    for sym in sorted(elig_map.get(sd, set())):
        n += 1
        qt = session_quote_times(sym, sd)
        cats["middle_15s"] += has_within(qt, mid, 15)
        cats["middle_60s"] += has_within(qt, mid, 60)
        any_session = qt is not None and len(qt) > 0
        cats["any_session_quote"] += any_session
        # anyscan_15s: any scan with a quote within 15s
        anyscan = False
        covered = 0
        if qt is not None and len(qt) > 0:
            qtv = qt.sort_values()
            for t in scans:
                if has_within(qtv, t, 15):
                    anyscan = True
                    covered += 1
        cats["anyscan_15s"] += anyscan
        cats["scan_density_15s_sum"] += (covered / len(scans)) if scans else 0
        if not anyscan and len(miss_anyscan_examples) < 8:
            miss_anyscan_examples.append("%s@%s(qrows=%d)" % (sym, sd.isoformat(), 0 if qt is None else len(qt)))

print("\n(2) PROPER coverage over %d PIT-eligible (sym,session) pairs:" % n)
for k in ["middle_15s", "middle_60s", "any_session_quote", "anyscan_15s"]:
    print("    %-20s %5d  (%.2f%%)" % (k, cats[k], 100 * cats[k] / max(n, 1)))
print("    scan_density_15s mean (avg fraction of 346 scans covered): %.2f%%" % (100 * cats["scan_density_15s_sum"] / max(n, 1)))
print("    anyscan_15s MISS examples (eligible, no quote near any scan):", miss_anyscan_examples)
# decompose: of eligible misses under middle_60s, how many have ANY session quote (=> single-instant artifact)
print("\n  middle_60s MISS but HAS any_session_quote (single-instant artifact): see anyscan vs middle gap above")
