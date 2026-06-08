"""Re-measure quote coverage given the EMIT-LATCH (confirmed: scan_loop.py:302-313
keys same_symbol_entries_per_day=1 on the emit counter, incremented at emit BEFORE
quote resolution; symbol_cooldown_minutes=390). So each (sym,session) gets ONE
quote shot at its first-emit scan, NOT "any scan". anyscan_15s (98.33%) is only an
optimistic bound.

Realism-faithful proxies (the true first-emit scan is signal/trial-dependent; a
symbol can only emit at a scan where it has a FRESH bar within max_bar_age=90s):
  first_freshbar_quote_15s : quote within 15s at the symbol's FIRST fresh-bar scan
      (earliest possible emit — a lower bound on the emit scan).
  freshbar_quote_density   : per (sym,session), fraction of fresh-bar scans that
      ALSO have a quote within 15s, averaged (the chance a random emit is covered).
  all_freshbar_have_quote  : every fresh-bar scan has a quote (pessimistic: emit
      could land anywhere).
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

LAKE = "/opt/market_data_cache"
Q = f"{LAKE}/quotes/vendor=alpaca/feed=sip"
B1 = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw"
MAX_BAR_AGE, MAX_QUOTE_AGE = 90, 15
cfg = load_config("/tmp/ir2m.yml")
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
sessions = sorted({pd.Timestamp(s).date() for s in cdf.session.unique()})[:5]
elig_map = eligible_per_session_map(LAKE, sessions, cfg=cfg)

_qc, _bc = {}, {}
def _times(cache, root, sym, sd):
    key = (sym, sd.year, sd.month)
    if key not in cache:
        f = f"{root}/symbol={sym}/year={sd.year:04d}/month={sd.month:02d}/part.parquet"
        if os.path.isfile(f):
            ts = pd.to_datetime(pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True).dt.tz_convert("America/New_York")
            cache[key] = ts
        else:
            cache[key] = None
    allts = cache[key]
    if allts is None:
        return None
    d = allts[allts.dt.date == sd]
    if not len(d):
        return None
    return d.sort_values().dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()

def has_within(arr, scan_ts, secs):
    if arr is None or len(arr) == 0:
        return False
    s = scan_ts.tz_convert("UTC").tz_localize(None)
    lo = (s - pd.Timedelta(seconds=secs)).to_datetime64()
    hi = s.to_datetime64()
    return bool(((arr >= lo) & (arr <= hi)).any())

cats = defaultdict(float)
n = 0
for sd in sessions:
    scans = list(scan_times_for_session(sd, cfg))
    for sym in sorted(elig_map.get(sd, set())):
        n += 1
        qt = _times(_qc, Q, sym, sd)
        bt = _times(_bc, B1, sym, sd)
        # fresh-bar scans = scans where a minute bar falls in [t-90s, t]
        freshbar_scans = [t for t in scans if has_within(bt, t, MAX_BAR_AGE)]
        if not freshbar_scans:
            cats["no_freshbar_scan"] += 1   # symbol never tradeable (flat session)
            continue
        first_fb = freshbar_scans[0]
        cats["first_freshbar_quote_15s"] += has_within(qt, first_fb, MAX_QUOTE_AGE)
        covered = sum(1 for t in freshbar_scans if has_within(qt, t, MAX_QUOTE_AGE))
        cats["freshbar_quote_density_sum"] += covered / len(freshbar_scans)
        cats["all_freshbar_have_quote"] += (covered == len(freshbar_scans))
        cats["has_freshbar"] += 1

print("eligible pairs:", n, "| with >=1 fresh-bar scan:", int(cats["has_freshbar"]),
      "| flat (no fresh-bar scan):", int(cats["no_freshbar_scan"]))
hb = max(cats["has_freshbar"], 1)
print("\n--- realism-faithful (given EMIT-LATCH: one shot at first-emit scan) ---")
print("  first_freshbar_quote_15s  %5d/%d  (%.2f%% of fresh-bar pairs | %.2f%% of all eligible)" % (
    cats["first_freshbar_quote_15s"], hb, 100*cats["first_freshbar_quote_15s"]/hb, 100*cats["first_freshbar_quote_15s"]/n))
print("  freshbar_quote_density    mean %.2f%%  (avg fraction of a symbol's fresh-bar scans with a quote)" % (
    100*cats["freshbar_quote_density_sum"]/hb))
print("  all_freshbar_have_quote   %5d/%d  (%.2f%%)  [pessimistic: emit could land anywhere]" % (
    cats["all_freshbar_have_quote"], hb, 100*cats["all_freshbar_have_quote"]/hb))
print("\n  (anyscan_15s optimistic bound was 98.33%; flat-no-trade pairs ~94 excluded as before)")
