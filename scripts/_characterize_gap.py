"""For the no_minute_file (symbol, month) preflight misses, determine whether the
symbol was daily-eligible AND trading that month (=> a fixable minute-backfill
coverage gap) vs not (=> PIT over-inclusion / genuinely untraded)."""
import json
from pathlib import Path
from collections import defaultdict

import pandas as pd

B1 = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw")
BD = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted")
MIN_ADV = 2_000_000
MIN_PX, MAX_PX = 1.0, 20.0

# probe (sym, session) that are no_minute_file: max_n==0 across the session AND no month file
agg = defaultdict(lambda: [0, 0])  # (sym, sess) -> [miss, maxn]
for line in open("/quants-lab/scripts/_probe_log_2m.jsonl"):
    try:
        d = json.loads(line)
    except Exception:
        continue
    ts = pd.Timestamp(d["ts"])
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    sess = ts.tz_convert("America/New_York").date().isoformat()
    a = agg[(d["sym"], sess)]
    a[0] += 1 if d["n"] == 0 else 0
    if d["n"] > a[1]:
        a[1] = d["n"]

nofile = []
for (sym, sess), (miss, maxn) in agg.items():
    if miss > 0 and maxn == 0:
        y, m = sess[:4], sess[5:7]
        if not (B1 / f"symbol={sym}/year={y}/month={m}/part.parquet").exists():
            nofile.append((sym, sess))

print("no_minute_file (sym,session) pairs:", len(nofile))

# Daily eligibility + trading for each no_minute_file pair, sampled
import itertools
sample = nofile[:600]
buckets = defaultdict(int)
ex = defaultdict(list)


def daily_for_month(sym, sess):
    f = BD / f"symbol={sym}/part.parquet"
    if not f.is_file():
        return None
    try:
        df = pd.read_parquet(f)
        df["sd"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
        d = pd.Timestamp(sess).date()
        # 20-session trailing window ending at/just before the probe date
        prior = df[df["sd"] <= d].tail(20)
        if len(prior) == 0:
            return ("no_daily_history", 0, 0)
        adv = float((prior["close"] * prior["volume"]).mean())
        px = float(prior["close"].iloc[-1])
        return ("ok", adv, px)
    except Exception:
        return ("read_error", 0, 0)


for sym, sess in sample:
    r = daily_for_month(sym, sess)
    if r is None:
        buckets["no_daily_file"] += 1
        continue
    status, adv, px = r
    if status != "ok":
        buckets[status] += 1
        continue
    eligible = (MIN_PX <= px <= MAX_PX) and (adv >= MIN_ADV)
    key = "DAILY-ELIGIBLE+traded (FIXABLE minute gap)" if eligible else "not-daily-eligible (px/adv) -> PIT mismatch"
    buckets[key] += 1
    if len(ex[key]) < 6:
        ex[key].append("%s@%s px=$%.2f adv=$%.1fM" % (sym, sess, px, adv / 1e6))

print("\n=== no_minute_file pairs by daily-eligibility (sample of %d) ===" % len(sample))
for k, v in sorted(buckets.items(), key=lambda x: -x[1]):
    print("  %-46s %4d (%.0f%%)" % (k, v, 100 * v / len(sample)))
    for e in ex[k]:
        print("        %s" % e)
