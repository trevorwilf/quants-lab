"""Quote-coverage vs ADV-floor curve (operator chose: find the ADV floor where
genuine single-emit quote coverage reaches 95%).

Efficient: raising the ADV floor only REMOVES symbols from the $2M-eligible set,
and each (sym,session)'s quote coverage is floor-independent. So compute, over the
$2M-eligible superset, per (sym,session): prior_adv + the sim-faithful single-emit
quote metrics; then sweep the floor by filtering prior_adv >= F.

Metrics (given the EMIT-LATCH = one quote shot at first-emit; emits only at scans
with a fresh bar within max_bar_age=90s):
  first_emit_15s   : quote within 15s at the FIRST fresh-bar scan (earliest emit).
  density_15s      : P(quote within 15s | scan has a fresh bar) per pair, averaged
                     (expected coverage of a random emit among tradeable scans).
Cross-check: build the REAL builder eligible map at one higher floor and confirm
it equals {$2M-eligible} ∩ {prior_adv >= floor}.
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
BD = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted"
MAX_BAR_AGE, MAX_QUOTE_AGE = 90, 15
FLOORS = [2e6, 3e6, 5e6, 7.5e6, 10e6, 15e6, 25e6, 50e6, 100e6]

cfg = load_config("/tmp/ir2m.yml")
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
sessions = sorted({pd.Timestamp(s).date() for s in cdf.session.unique()})[:5]
elig_map = eligible_per_session_map(LAKE, sessions, cfg=cfg)  # $2M superset

_qc, _bc, _dc = {}, {}, {}
def _times(cache, root, sym, sd):
    key = (sym, sd.year, sd.month)
    if key not in cache:
        f = f"{root}/symbol={sym}/year={sd.year:04d}/month={sd.month:02d}/part.parquet"
        cache[key] = (pd.to_datetime(pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True)
                      .dt.tz_convert("America/New_York")) if os.path.isfile(f) else None
    allts = cache[key]
    if allts is None:
        return None
    d = allts[allts.dt.date == sd]
    return d.sort_values().dt.tz_convert("UTC").dt.tz_localize(None).to_numpy() if len(d) else None

def has_within(arr, scan_ts, secs):
    if arr is None or len(arr) == 0:
        return False
    s = scan_ts.tz_convert("UTC").tz_localize(None)
    return bool(((arr >= (s - pd.Timedelta(seconds=secs)).to_datetime64()) & (arr <= s.to_datetime64())).any())

def prior_adv(sym, sd):
    if sym not in _dc:
        f = f"{BD}/symbol={sym}/part.parquet"
        if os.path.isfile(f):
            df = pd.read_parquet(f)
            df["d"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
            _dc[sym] = df.sort_values("d")
        else:
            _dc[sym] = None
    df = _dc[sym]
    if df is None:
        return 0.0
    p = df[df["d"] < sd].tail(20)
    if len(p) == 0:
        return 0.0
    return float((p["close"].astype(float) * p["volume"].astype(float)).mean())

rows = []  # (prior_adv, first_emit_15s, density_15s)
for sd in sessions:
    scans = list(scan_times_for_session(sd, cfg))
    for sym in sorted(elig_map.get(sd, set())):
        qt, bt = _times(_qc, Q, sym, sd), _times(_bc, B1, sym, sd)
        fb = [t for t in scans if has_within(bt, t, MAX_BAR_AGE)]
        if not fb:
            rows.append((prior_adv(sym, sd), 0, 0.0, False))  # flat: no emit possible
            continue
        first_emit = 1 if has_within(qt, fb[0], MAX_QUOTE_AGE) else 0
        dens = sum(1 for t in fb if has_within(qt, t, MAX_QUOTE_AGE)) / len(fb)
        rows.append((prior_adv(sym, sd), first_emit, dens, True))

df = pd.DataFrame(rows, columns=["adv", "first_emit", "density", "has_fb"])
print("computed %d eligible (sym,session) pairs ($2M superset; %d tradeable, %d flat)\n" % (
    len(df), int(df.has_fb.sum()), int((~df.has_fb).sum())))
print("%-10s %8s %12s %12s %14s" % ("ADV floor", "n_pairs", "first_emit%", "density%", "verdict(95%)"))
for F in FLOORS:
    sub = df[df.adv >= F]
    if len(sub) == 0:
        continue
    # tradeable pairs only for the coverage rate (flat pairs never emit/ never trade)
    trad = sub[sub.has_fb]
    fe = 100 * trad.first_emit.mean() if len(trad) else 0
    de = 100 * trad.density.mean() if len(trad) else 0
    verdict = "PASS" if de >= 95 else ("PASS(first_emit)" if fe >= 95 else "fail")
    print("$%-9s %8d %11.2f%% %11.2f%% %14s" % (
        ("%.1fM" % (F / 1e6)), len(sub), fe, de, verdict))

# cross-check: real builder eligible map at $10M vs the filter
print("\n--- cross-check eligibility approximation at $10M ---")
cfg10 = dict(cfg)
cfg10["universe"] = {**(cfg.get("universe") or {}), "min_adv_dollars": 10e6}
em10 = eligible_per_session_map(LAKE, sessions, cfg=cfg10)
real10 = {(sym, sd) for sd in sessions for sym in em10.get(sd, set())}
filt10 = set()
for sd in sessions:
    for sym in elig_map.get(sd, set()):
        if prior_adv(sym, sd) >= 10e6:
            filt10.add((sym, sd))
print("real builder $10M pairs: %d | {$2M-eligible ∩ adv>=10M}: %d | intersection: %d | symdiff: %d" % (
    len(real10), len(filt10), len(real10 & filt10), len(real10 ^ filt10)))
