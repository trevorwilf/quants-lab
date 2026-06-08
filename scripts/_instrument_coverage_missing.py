"""Instrument the REAL coverage_missing first-scan (09:45 ET) probe over the
eligible (symbol, session) pairs, and prototype the audit_missing_sessions
eligible-union restriction.

coverage_missing categorization (eligible pairs only):
  - daily_leg_miss   : no daily bar on the session day (daily_bars_supplier empty)
  - minute_leg_miss  : no minute bar in the [09:45,09:45] window (the first scan)
      * traded_later  : has >=1 bar in [09:45, close]  -> carry-forward-able
      * no_trade_today: no bar at all from 09:45 onward -> genuine flat day
"""
import sys
from collections import Counter

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
import pandas as pd  # noqa: E402

from bowaka_v2_lab.optuna.walkforward_runner import load_config  # noqa: E402
from bowaka_v2_lab.data.suppliers import make_lake_suppliers, resolve_intraday_window_policy  # noqa: E402
from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config  # noqa: E402
from bowaka_v2_lab.optuna.pit_universe import eligible_per_session_map  # noqa: E402
from bowaka_v2_lab.sim.schedule import scan_times_for_session  # noqa: E402

LAKE = "/opt/market_data_cache"
cfg = load_config("/tmp/ir2m.yml")
feed = "sip"

# 5 probe sessions (same window the study-start preflight uses) from the CSV.
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
sessions = sorted({pd.Timestamp(s).date() for s in cdf.session.unique()})[:5]
print("sessions:", [s.isoformat() for s in sessions])

minute_supplier, daily_supplier = make_lake_suppliers(
    LAKE, feed=feed,
    intraday_window_policy=resolve_intraday_window_policy(cfg),
    daily_adjustment=daily_adjustment_for_config(cfg),
)
elig_map = eligible_per_session_map(LAKE, sessions, cfg=cfg)
print("eligible map sizes:", {s.isoformat(): len(elig_map.get(s, set())) for s in sessions})


def nonempty(x):
    return x is not None and len(x) > 0


cat = Counter()
examples = {}
n_eligible = 0
for sd in sessions:
    scan_times = list(scan_times_for_session(sd, cfg))
    probe_ts = scan_times[0]           # 09:45 — the coverage_missing minute probe
    last_ts = scan_times[-1]           # last scan — widest [09:45, last] window
    for sym in sorted(elig_map.get(sd, set())):
        n_eligible += 1
        try:
            day_ok = nonempty(daily_supplier(sym, sd))
        except Exception:
            day_ok = False
        try:
            min0945_ok = nonempty(minute_supplier(sym, probe_ts))
        except Exception:
            min0945_ok = False
        if day_ok and min0945_ok:
            cat["ok"] += 1
            continue
        # a miss (daily leg OR minute leg)
        if not day_ok and not min0945_ok:
            c = "both_legs_miss"
        elif not day_ok:
            c = "daily_leg_miss_only"
        else:
            # minute-leg miss only: traded later that day?
            try:
                traded_session = nonempty(minute_supplier(sym, last_ts))
            except Exception:
                traded_session = False
            c = "minute_leg_miss_traded_later" if traded_session else "minute_leg_miss_no_trade_today"
        cat[c] += 1
        examples.setdefault(c, [])
        if len(examples[c]) < 6:
            examples[c].append("%s@%s" % (sym, sd.isoformat()))

total_miss = sum(v for k, v in cat.items() if k != "ok")
print("\n=== coverage_missing eligible-pair categorization ===")
print("eligible pairs probed:", n_eligible, "| ok:", cat["ok"], "| MISS:", total_miss,
      "(%.2f%%)" % (100 * total_miss / max(n_eligible, 1)))
for k, v in sorted(cat.items(), key=lambda x: -x[1]):
    if k == "ok":
        continue
    print("  %-32s %5d (%.1f%% of miss)  e.g. %s" % (k, v, 100 * v / max(total_miss, 1), examples.get(k, [])))

# carry-forward-able share = any miss where a price exists to carry (daily prior
# close exists for eligible names by construction; minute-leg-traded-later also).
cf = cat["minute_leg_miss_traded_later"]
flat = cat["minute_leg_miss_no_trade_today"]
print("\n  minute-leg first-minute sparsity (traded later, carry-forward-able): %d" % cf)
print("  minute-leg genuine flat day (no trade 09:45->close)               : %d" % flat)
print("  daily-leg involved (delisted/halted session-day daily gap)        : %d" % (cat["daily_leg_miss_only"] + cat["both_legs_miss"]))

print("\n" + "=" * 60)
print("audit_missing_sessions — eligible-union restriction prototype")
print("=" * 60)
from bowaka_v2_lab.data.data_quality import find_latest_audit  # noqa: E402
ap = find_latest_audit(LAKE, feed=feed)
adf = pd.read_parquet(ap)
adf["_sym"] = adf["symbol"].astype(str)
adf["_ms"] = pd.to_numeric(adf["missing_sessions"], errors="coerce").fillna(0).astype(int)
probe_syms = set(cdf.symbol.astype(str))
ever_elig = set()
for sd in sessions:
    ever_elig |= elig_map.get(sd, set())
ever_elig = {str(s) for s in ever_elig}
full = int(adf[adf["_sym"].isin(probe_syms)]["_ms"].sum())
gated = int(adf[adf["_sym"].isin(ever_elig)]["_ms"].sum())
print("requested = full PIT union (2425):  missing_sessions =", full, "-> FAIL (gate=0)")
print("restricted to ever-eligible union:  missing_sessions =", gated,
      "->", "PASS" if gated == 0 else "still FAIL")
print("ever-eligible union size:", len(ever_elig), "| probe symbols:", len(probe_syms))
