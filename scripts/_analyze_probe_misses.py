"""Categorize the instrumented preflight minute-bar probe misses.

Input: /quants-lab/scripts/_probe_log_2m.jsonl — one JSON per real probe the
$2M intended_realism preflight made: {"sym","ts","n"} where n = bars returned by
minute_bars_supplier(sym, [09:45 ET, ts]).

Question: are the n==0 misses REAL no-trade (the lake faithfully has no bar
because no trade printed) or DATA DEFECTS (the lake is missing a bar that should
exist)?

Categories of each (sym, session) that has >=1 miss:
  - intra_session_sparse : the symbol DID trade in the regular session that day
        (max_n > 0 across its 8 scans), so the misses are early scans BEFORE its
        first trade in [09:45, scan]. Real no-trade in the early window.
  - no_regular_bars_traded_premarket_only : has bars that day but none 09:30-15:59
  - no_session_bars_has_month_file : month file exists, zero bars on that date
        (eligible by DAILY criteria but did not trade intraday). Real no-trade.
  - no_minute_file : no minute parquet for that symbol-month at all (the only
        category that could be a backfill gap vs a genuinely untraded symbol).
"""
import json
import functools
from pathlib import Path
from collections import defaultdict

import pandas as pd

B = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw")
Q = Path("/opt/market_data_cache/quotes/vendor=alpaca/feed=sip")
LOG = Path("/quants-lab/scripts/_probe_log_2m.jsonl")

agg = defaultdict(lambda: [0, 0, 0])  # (sym, session) -> [probes, misses, max_n]
for line in open(LOG):
    try:
        d = json.loads(line)
    except Exception:
        continue
    ts = pd.Timestamp(d["ts"])
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    sess = ts.tz_convert("America/New_York").date().isoformat()
    a = agg[(d["sym"], sess)]
    a[0] += 1
    if d["n"] == 0:
        a[1] += 1
    if d["n"] > a[2]:
        a[2] = d["n"]

total_probes = sum(a[0] for a in agg.values())
total_miss = sum(a[1] for a in agg.values())


@functools.lru_cache(maxsize=None)
def session_status(sym, sess):
    y, m = sess[:4], sess[5:7]
    f = B / f"symbol={sym}/year={y}/month={m}/part.parquet"
    if not f.exists():
        return "no_minute_file"
    try:
        ts = pd.to_datetime(pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True).dt.tz_convert("America/New_York")
        day = ts[ts.dt.date == pd.Timestamp(sess).date()]
        if len(day) == 0:
            return "no_session_bars_has_month_file"
        reg = day[(day.dt.time >= pd.Timestamp("09:30").time()) & (day.dt.time <= pd.Timestamp("15:59").time())]
        return "has_regular_bars" if len(reg) > 0 else "no_regular_bars_premarket_only"
    except Exception:
        return "read_error"


@functools.lru_cache(maxsize=None)
def has_quote_file(sym, sess):
    y, m = sess[:4], sess[5:7]
    return (Q / f"symbol={sym}/year={y}/month={m}/part.parquet").exists()


cat_miss = defaultdict(int)
cat_pairs = defaultdict(int)
examples = defaultdict(list)
nofile_quote = [0, 0]  # [has_quote, no_quote] for no_minute_file misses
for (sym, sess), (p, miss, maxn) in agg.items():
    if miss == 0:
        continue
    if maxn > 0:
        c = "intra_session_sparse"
    else:
        c = session_status(sym, sess)
        if c == "no_minute_file":
            nofile_quote[0 if has_quote_file(sym, sess) else 1] += 1
    cat_miss[c] += miss
    cat_pairs[c] += 1
    if len(examples[c]) < 5:
        examples[c].append(f"{sym}@{sess}(miss {miss}/{p}, maxn {maxn})")

print(f"=== PROBE MISS CATEGORIZATION ($2M intended_realism preflight) ===")
print(f"total probes={total_probes}  total misses={total_miss} ({100*total_miss/total_probes:.1f}%)")
print(f"unique (sym,session) pairs={len(agg)}  pairs with >=1 miss={sum(1 for a in agg.values() if a[1]>0)}")
print(f"\n{'category':42s} {'misses':>8s} {'%miss':>7s} {'pairs':>7s}")
for c, v in sorted(cat_miss.items(), key=lambda x: -x[1]):
    print(f"  {c:40s} {v:8d} {100*v/total_miss:6.1f}% {cat_pairs[c]:7d}")
    for ex in examples[c]:
        print(f"        e.g. {ex}")
print(f"\nno_minute_file misses by quote presence: has_quote_file={nofile_quote[0]} pairs, no_quote_file={nofile_quote[1]} pairs")
real = sum(v for c, v in cat_miss.items() if c != "no_minute_file")
print(f"\nREAL no-trade (symbol present, just didn't trade the probed window/day): {real} ({100*real/total_miss:.1f}% of misses)")
print(f"POTENTIAL defect (no minute file at all): {cat_miss.get('no_minute_file',0)} ({100*cat_miss.get('no_minute_file',0)/total_miss:.1f}% of misses)")
