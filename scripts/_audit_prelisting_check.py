"""Is audit_missing_sessions a PRE-LISTING artifact? For the 6 ever-eligible
symbols that carry all 1762 probe-universe missing sessions, compare the audit's
expected-session window (start/end) against the symbol's ACTUAL first daily bar
(listing date) and its eligible window. If the missing sessions are all before
the first bar (pre-listing), the count is benign; if they fall during the
trading/eligible window, it is a real data gap.
"""
import os
import sys
import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.data.data_quality import find_latest_audit  # noqa: E402

LAKE = "/opt/market_data_cache"
BD = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted"
B1 = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw"
SYMS = ["AIB", "LIFE", "VIA", "AKTS", "SZZL", "ASBP"]

adf = pd.read_parquet(find_latest_audit(LAKE, feed="sip"))
adf["_sym"] = adf["symbol"].astype(str)

for sym in SYMS:
    row = adf[adf["_sym"] == sym]
    if row.empty:
        print(sym, "no audit row"); continue
    r = row.iloc[0]
    # actual first/last daily bar (listing proxy)
    f = f"{BD}/symbol={sym}/part.parquet"
    first_bar = last_bar = n_daily = None
    if os.path.isfile(f):
        d = pd.read_parquet(f, columns=["timestamp"])
        ts = pd.to_datetime(d["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
        first_bar, last_bar, n_daily = ts.min(), ts.max(), len(ts)
    # minute-data months present (did it actually trade intraday, and when)
    md = f"{B1}/symbol={sym}"
    months = []
    if os.path.isdir(md):
        for p in sorted(__import__("pathlib").Path(md).rglob("part.parquet")):
            s = str(p)
            months.append(s.split("year=")[1][:4] + "-" + s.split("month=")[1][:2])
    print("\n=== %s ===" % sym)
    print("  audit: start=%s end=%s expected=%s observed=%s missing=%s" % (
        r.get("start"), r.get("end"), r.get("expected_sessions"),
        r.get("observed_sessions"), r.get("missing_sessions")))
    print("  daily bars: first=%s last=%s n=%s" % (first_bar, last_bar, n_daily))
    print("  minute months present: %d %s" % (len(months), months[:6] + (["..."] if len(months) > 6 else [])))
    # verdict heuristic
    if first_bar is not None and r.get("start") is not None:
        astart = pd.Timestamp(r.get("start")).date() if not isinstance(r.get("start"), float) else None
        if astart is not None:
            pre = (first_bar > astart)
            print("  -> first daily bar %s audit-start %s  => %s" % (
                first_bar, astart,
                "PRE-LISTING gap (audit window predates listing -> benign)" if pre
                else "audit starts at/after first bar (missing may be real)"))
