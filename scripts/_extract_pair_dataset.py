"""Stage a clean per-(symbol, session) dataset from the instrumented probe log +
lake, so downstream analysis needs no further lake access. Writes a CSV the
workflow agents read on the host.

Columns: symbol, session, n_probes, n_miss, max_n, has_min_month_file,
has_session_bars, has_regular_bars, prior_close, prior_adv, has_quote_month_file,
daily_eligible, first_trade_et, category
"""
import json
import csv
from pathlib import Path
from collections import defaultdict

import pandas as pd

B1 = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw")
BD = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted")
Q = Path("/opt/market_data_cache/quotes/vendor=alpaca/feed=sip")
OUT = "/quants-lab/scripts/_pair_dataset.csv"
MIN_ADV, MIN_PX, MAX_PX = 2_000_000, 1.0, 20.0

agg = defaultdict(lambda: [0, 0, 0])  # (sym,sess) -> probes, miss, max_n
for line in open("/quants-lab/scripts/_probe_log_2m.jsonl"):
    try:
        d = json.loads(line)
    except Exception:
        continue
    ts = pd.Timestamp(d["ts"])
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    sess = ts.tz_convert("America/New_York").date().isoformat()
    a = agg[(d["sym"], sess)]
    a[0] += 1
    a[1] += 1 if d["n"] == 0 else 0
    if d["n"] > a[2]:
        a[2] = d["n"]

# Per-symbol daily cache (read once)
_daily = {}
def daily(sym):
    if sym not in _daily:
        f = BD / f"symbol={sym}/part.parquet"
        if f.is_file():
            df = pd.read_parquet(f)
            df["sd"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
            _daily[sym] = df.sort_values("sd")
        else:
            _daily[sym] = None
    return _daily[sym]

# Per-symbol minute month cache
_minfile = {}
def has_min_file(sym, sess):
    y, m = sess[:4], sess[5:7]
    return (B1 / f"symbol={sym}/year={y}/month={m}/part.parquet").is_file()

def session_bars(sym, sess):
    """(has_session_bars, has_regular_bars, first_trade_et)"""
    y, m = sess[:4], sess[5:7]
    f = B1 / f"symbol={sym}/year={y}/month={m}/part.parquet"
    if not f.is_file():
        return 0, 0, ""
    try:
        ts = pd.to_datetime(pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True).dt.tz_convert("America/New_York")
        day = ts[ts.dt.date == pd.Timestamp(sess).date()]
        if len(day) == 0:
            return 0, 0, ""
        reg = day[(day.dt.time >= pd.Timestamp("09:30").time()) & (day.dt.time <= pd.Timestamp("15:59").time())]
        return 1, (1 if len(reg) else 0), str(day.min().time())[:5]
    except Exception:
        return 0, 0, ""

def prior(sym, sess):
    df = daily(sym)
    if df is None:
        return None, None
    d = pd.Timestamp(sess).date()
    p = df[df["sd"] < d].tail(20)
    if len(p) == 0:
        return None, None
    close = p["close"].astype(float)
    return float(close.iloc[-1]), float((close * p["volume"].astype(float)).mean())

rows = []
for (sym, sess), (np_, nm, mx) in agg.items():
    hmf = 1 if has_min_file(sym, sess) else 0
    hsb, hrb, ft = (session_bars(sym, sess) if hmf else (0, 0, ""))
    pc, pa = prior(sym, sess)
    hqf = 1 if (Q / f"symbol={sym}/year={sess[:4]}/month={sess[5:7]}/part.parquet").is_file() else 0
    elig = 1 if (pc is not None and pa is not None and MIN_PX <= pc <= MAX_PX and pa >= MIN_ADV) else 0
    if mx > 0:
        cat = "intra_session_sparse"
    elif hmf and hsb:
        cat = "no_regular_bars"
    elif hmf:
        cat = "no_session_bars_has_month_file"
    elif pc is None:
        cat = "no_daily_history"
    else:
        cat = "no_minute_file"
    rows.append([sym, sess, np_, nm, mx, hmf, hsb, hrb,
                 "" if pc is None else round(pc, 3), "" if pa is None else round(pa, 0),
                 hqf, elig, ft, cat])

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["symbol", "session", "n_probes", "n_miss", "max_n", "has_min_month_file",
                "has_session_bars", "has_regular_bars", "prior_close", "prior_adv",
                "has_quote_month_file", "daily_eligible", "first_trade_et", "category"])
    w.writerows(rows)

print("wrote", OUT, "rows:", len(rows))
# quick summary
import collections
tp = sum(r[2] for r in rows); tm = sum(r[3] for r in rows)
print("total probes:", tp, "misses:", tm, "(%.1f%%)" % (100 * tm / tp))
bycat = collections.Counter()
for r in rows:
    bycat[r[13]] += r[3]
for k, v in bycat.most_common():
    print("  miss[%s] = %d (%.1f%%)" % (k, v, 100 * v / tm))
# genuine gap: miss among pairs that HAVE a minute month file
mf_probes = sum(r[2] for r in rows if r[5] == 1)
mf_miss = sum(r[3] for r in rows if r[5] == 1)
print("MISS restricted to symbols WITH minute data that month: %d/%d = %.1f%% (vs 5%% threshold)" % (mf_miss, mf_probes, 100 * mf_miss / max(mf_probes, 1)))
# miss among eligible+has-minute
e_probes = sum(r[2] for r in rows if r[5] == 1 and r[11] == 1)
e_miss = sum(r[3] for r in rows if r[5] == 1 and r[11] == 1)
print("MISS restricted to daily-eligible AND has-minute-month: %d/%d = %.1f%%" % (e_miss, e_probes, 100 * e_miss / max(e_probes, 1)))
