"""Phase 3 validation of the T3_NBBO_DEPTH fill model against REAL lake data.

For a sample of PIT-eligible first-emit scans, build the real SIP NBBO quote
(bid/ask + bid_size/ask_size) + the emit-minute volume, then run BOTH fill
models on the same ~$4000 order and tabulate:
  OLD  = simulate_market_fill(has_nbbo_depth=False)  -- 5%-ADV proxy + flat slip
  NEW  = simulate_market_fill(has_nbbo_depth=True)    -- real touch + 10% minute
         volume cap + sqrt impact (the §10f T3 model)
Demonstrates the realism upgrade: NEW caps fills at real liquidity, pays real
impact, produces partials/no-fills where OLD filled ~100% at trivial slippage.
"""
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.optuna.walkforward_runner import load_config  # noqa: E402
from bowaka_v2_lab.optuna.pit_universe import eligible_per_session_map  # noqa: E402
from bowaka_v2_lab.sim.schedule import scan_times_for_session  # noqa: E402
from bowaka_v2_lab.sim.fills import simulate_market_fill  # noqa: E402
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot, SOURCE_HISTORICAL  # noqa: E402

LAKE = "/opt/market_data_cache"
Q = f"{LAKE}/quotes/vendor=alpaca/feed=sip"
B1 = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw"
MAX_BAR_AGE, MAX_QUOTE_AGE = 90, 60   # 60s quote window (sticky NBBO, §10e)
ORDER_NOTIONAL, MIN_NOTIONAL = 4000.0, 500.0
cfg = load_config("/tmp/ir2m.yml")
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
adv_by = {(str(r.symbol), str(r.session)): float(r.prior_adv) for r in cdf.itertuples() if not pd.isna(r.prior_adv)}
sessions = sorted({pd.Timestamp(s).date() for s in cdf.session.unique()})[:5]
elig_map = eligible_per_session_map(LAKE, sessions, cfg=cfg)

_qc, _bc = {}, {}
def _read(cache, root, sym, sd, cols):
    key = (sym, sd.year, sd.month)
    if key not in cache:
        f = f"{root}/symbol={sym}/year={sd.year:04d}/month={sd.month:02d}/part.parquet"
        cache[key] = pd.read_parquet(f, columns=cols) if os.path.isfile(f) else None
    df = cache[key]
    if df is None:
        return None
    d = df.copy()
    d["t"] = pd.to_datetime(d["timestamp"], utc=True).dt.tz_convert("America/New_York")
    return d[d["t"].dt.date == sd].sort_values("t")

old_out, new_out = Counter(), Counter()
old_fillfrac, new_fillfrac, new_impact = [], [], []
n = 0
import math
for sd in sessions:
    scans = list(scan_times_for_session(sd, cfg))
    for sym in sorted(elig_map.get(sd, set())):
        q = _read(_qc, Q, sym, sd, ["timestamp", "bid", "ask", "bid_size", "ask_size"])
        b = _read(_bc, B1, sym, sd, ["timestamp", "volume", "close"])
        if q is None or b is None or len(b) == 0:
            continue
        # first fresh-bar scan (emit proxy)
        bt = b["t"]
        emit = None
        for t in scans:
            lo = (t - pd.Timedelta(seconds=MAX_BAR_AGE))
            if ((bt >= lo) & (bt <= t)).any():
                emit = t
                break
        if emit is None:
            continue
        # NBBO at/before emit within 60s
        qq = q[(q["t"] <= emit) & (q["t"] >= emit - pd.Timedelta(seconds=MAX_QUOTE_AGE))]
        if len(qq) == 0:
            continue
        row = qq.iloc[-1]
        ask, bid = float(row["ask"]), float(row["bid"])
        asz, bsz = float(row["ask_size"] or 0), float(row["bid_size"] or 0)
        if ask <= 0:
            continue
        # emit-minute bar (volume)
        mb = b[(b["t"] >= emit - pd.Timedelta(seconds=60)) & (b["t"] <= emit)]
        minute_vol = float(mb["volume"].iloc[-1]) if len(mb) else 0.0
        mid = (bid + ask) / 2.0 if bid > 0 else ask
        quote = QuoteSnapshot(bid=bid, ask=ask, mid=round(mid, 4),
                              spread_pct=((ask - bid) / mid if mid > 0 else 0.0),
                              quote_timestamp=str(emit), quote_age_seconds=0.0,
                              source=SOURCE_HISTORICAL, bid_size=bsz, ask_size=asz)
        qty = int(ORDER_NOTIONAL / ask)
        if qty <= 0:
            continue
        n += 1
        adv = adv_by.get((sym, sd.isoformat()), 0.0)
        liq_proxy = (adv / ask) * 0.05 if adv > 0 else None
        mbars = pd.DataFrame({"timestamp": [pd.Timestamp(emit).tz_convert("UTC")], "volume": [minute_vol], "close": [ask]})
        # OLD
        fo = simulate_market_fill(side="buy", requested_qty=qty, quote=quote,
                                  liquidity_proxy_shares=liq_proxy, cost_stress="conservative",
                                  adv_participation_frac=0.002, min_order_notional=MIN_NOTIONAL)
        # NEW (T3)
        fn = simulate_market_fill(side="buy", requested_qty=qty, quote=quote,
                                  liquidity_proxy_shares=liq_proxy, cost_stress="conservative",
                                  adv_participation_frac=0.002, min_order_notional=MIN_NOTIONAL,
                                  has_nbbo_depth=True, minute_bars=mbars, scan_ts=pd.Timestamp(emit).tz_convert("UTC"),
                                  participation_cap=0.10, market_impact_coef_bps=10.0, market_impact_model="sqrt")
        old_out["fill" if fo.filled and not fo.is_partial else ("partial" if fo.filled else "no_fill")] += 1
        new_out["fill" if fn.filled and not fn.is_partial else ("partial" if fn.filled else "no_fill")] += 1
        if fo.filled:
            old_fillfrac.append(fo.filled_qty / qty)
        if fn.filled:
            new_fillfrac.append(fn.filled_qty / qty)
            new_impact.append(fn.slippage_bps_total)

def pct(c, k):
    return 100 * c[k] / max(sum(c.values()), 1)
print("validated %d eligible first-emit orders ($4000 each), conservative stress\n" % n)
print("%-10s %10s %10s %10s" % ("outcome", "OLD %", "NEW(T3) %", ""))
for k in ["fill", "partial", "no_fill"]:
    print("%-10s %9.1f%% %9.1f%%" % (k, pct(old_out, k), pct(new_out, k)))
print("\nmedian fill fraction (filled_qty/requested):  OLD %.3f   NEW %.3f" % (
    np.median(old_fillfrac) if old_fillfrac else 0, np.median(new_fillfrac) if new_fillfrac else 0))
print("median slippage_bps paid (NEW only, OLD~flat): NEW %.1f bps (p90 %.1f)" % (
    np.median(new_impact) if new_impact else 0, np.percentile(new_impact, 90) if new_impact else 0))
print("\n=> NEW caps fills at real touch+10%% minute volume and pays real sqrt impact;")
print("   OLD filled the full order off a 5%%-ADV proxy at trivial slippage.")
