"""Efficient safety check for the audit_missing_sessions eligible-union fix.

The fix restricts the audit-check denominator to PIT-eligible symbols. It is SAFE
iff no symbol that actually HAS missing sessions is ever PIT-eligible (else the
fix would hide a real data gap for a tradeable name).

So: take every symbol with missing_sessions>0 in the latest audit parquet, and
check whether it is EVER eligible (prior-day close in [1,20] AND trailing-20d
prior ADV >= $2M) on ANY day in its daily history (a superset of the study
window -> conservative). Cheap: per-symbol daily scan, not a full PIT union.
"""
import sys
import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.data.data_quality import find_latest_audit  # noqa: E402

LAKE = "/opt/market_data_cache"
BD = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted"
MIN_ADV, MIN_PX, MAX_PX = 2_000_000, 1.0, 20.0

ap = find_latest_audit(LAKE, feed="sip")
adf = pd.read_parquet(ap)
adf["_ms"] = pd.to_numeric(adf["missing_sessions"], errors="coerce").fillna(0).astype(int)
miss = adf[adf["_ms"] > 0].copy()
print("audit parquet:", ap)
print("symbols with missing_sessions>0:", len(miss), "| total missing:", int(miss["_ms"].sum()))

# probe universe (what the check actually sums over)
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
probe_syms = set(cdf.symbol.astype(str))
miss["_in_probe"] = miss["symbol"].astype(str).isin(probe_syms)
print("of those, in the 2425 probe universe:", int(miss["_in_probe"].sum()),
      "| their missing total:", int(miss[miss["_in_probe"]]["_ms"].sum()))


def ever_eligible(sym):
    """Return (ever_eligible_bool, n_eligible_days, first_elig_date, example)."""
    import os
    f = f"{BD}/symbol={sym}/part.parquet"
    if not os.path.isfile(f):
        return (False, 0, None, "no_daily_file")
    df = pd.read_parquet(f)
    if df.empty or "close" not in df.columns:
        return (False, 0, None, "empty")
    df = df.sort_values("timestamp")
    df["d"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
    close = df["close"].astype(float)
    vol = df["volume"].astype(float)
    dollar = close * vol
    adv20 = dollar.rolling(20, min_periods=20).mean()
    # eligibility uses PRIOR-day close + PRIOR trailing-20 ADV -> shift by 1
    px_prior = close.shift(1)
    adv_prior = adv20.shift(1)
    elig = (px_prior >= MIN_PX) & (px_prior <= MAX_PX) & (adv_prior >= MIN_ADV)
    n = int(elig.sum())
    if n == 0:
        return (False, 0, None, "")
    first = df["d"].iloc[int(elig.values.argmax())]
    ex = "px=%.2f adv=%.2fM" % (px_prior[elig].iloc[0], adv_prior[elig].iloc[0] / 1e6)
    return (True, n, first, ex)


rows = []
for _, r in miss.iterrows():
    sym = str(r["symbol"])
    ev, n, first, ex = ever_eligible(sym)
    rows.append((sym, int(r["_ms"]), bool(r["_in_probe"]), ev, n, str(first), ex))

print("\n%-8s %6s %6s %10s %8s  %s" % ("symbol", "miss", "inprob", "everElig", "nDays", "firstElig / why"))
ever_elig_with_miss = []
for sym, ms, inp, ev, n, first, ex in sorted(rows, key=lambda x: (-x[3], -x[1])):
    flag = "ELIGIBLE!" if ev else "never"
    print("%-8s %6d %6s %10s %8d  %s %s" % (sym, ms, inp, flag, n, first if ev else "-", ex))
    if ev and inp:
        ever_elig_with_miss.append((sym, ms, n, first))

print("\n=== SAFETY VERDICT ===")
print("probe-universe symbols with missing_sessions that are EVER eligible (all daily history):",
      len(ever_elig_with_miss))
if not ever_elig_with_miss:
    print("=> SAFE: every probe symbol with missing sessions is NEVER PIT-eligible.")
    print("   Restricting the audit check to the eligible union hides NO tradeable-symbol gap.")
else:
    print("=> NEEDS REVIEW: these ever-eligible symbols carry missing sessions:")
    for s, ms, n, first in ever_elig_with_miss:
        print("     %s: missing=%d, eligible_days=%d, first_elig=%s" % (s, ms, n, first))
