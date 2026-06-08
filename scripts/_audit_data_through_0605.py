"""Verify the lake is COMPLETE through 2026-06-05 (last trading day).
For every symbol that has a 2026-06 minute file, tally per-session coverage of
minute bars + SIP quotes across the recent trading sessions 06-01..06-05. A
'cliff' (e.g. 06-05 << 06-04) would reveal a missing-day gap the resume-skip hid.
"""
import os
import glob
from collections import defaultdict

import pandas as pd

LAKE = "/opt/market_data_cache"
B1 = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw"
Q = f"{LAKE}/quotes/vendor=alpaca/feed=sip"
SESS = [pd.Timestamp(d).date() for d in ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05"]]

min_syms = sorted(p.split("symbol=")[1].split("/")[0]
                  for p in glob.glob(f"{B1}/symbol=*/year=2026/month=06/part.parquet"))
q_syms = set(p.split("symbol=")[1].split("/")[0]
             for p in glob.glob(f"{Q}/symbol=*/year=2026/month=06/part.parquet"))
print("symbols with a 2026-06 MINUTE file:", len(min_syms))
print("symbols with a 2026-06 QUOTE  file:", len(q_syms))

def dates_in(path):
    if not os.path.isfile(path):
        return set()
    try:
        ts = pd.to_datetime(pd.read_parquet(path, columns=["timestamp"])["timestamp"], utc=True)
        return set(ts.dt.tz_convert("America/New_York").dt.date)
    except Exception:
        return set()

min_cov = defaultdict(int)
q_cov = defaultdict(int)
both_cov = defaultdict(int)
n = 0
for sym in min_syms:
    n += 1
    md = dates_in(f"{B1}/symbol={sym}/year=2026/month=06/part.parquet")
    qd = dates_in(f"{Q}/symbol={sym}/year=2026/month=06/part.parquet")
    for s in SESS:
        if s in md:
            min_cov[s] += 1
        if s in qd:
            q_cov[s] += 1
        if s in md and s in qd:
            both_cov[s] += 1

print("\nper-session coverage over %d minute-universe symbols:" % n)
print("%-12s %10s %10s %10s" % ("session", "minute", "quote", "both"))
for s in SESS:
    print("%-12s %10d %10d %10d" % (s.isoformat(), min_cov[s], q_cov[s], both_cov[s]))

# cliff test: is 06-05 within 5% of the 06-01..06-04 median?
import statistics
m_prior = statistics.median(min_cov[s] for s in SESS[:-1])
q_prior = statistics.median(q_cov[s] for s in SESS[:-1])
print("\nCLIFF CHECK (06-05 vs prior-4 median):")
print("  minute: 06-05=%d vs median %d -> %s" % (
    min_cov[SESS[-1]], m_prior,
    "OK" if min_cov[SESS[-1]] >= 0.95 * m_prior else "GAP (06-05 low!)"))
print("  quote : 06-05=%d vs median %d -> %s" % (
    q_cov[SESS[-1]], q_prior,
    "OK" if q_cov[SESS[-1]] >= 0.95 * q_prior else "GAP (06-05 low!)"))
