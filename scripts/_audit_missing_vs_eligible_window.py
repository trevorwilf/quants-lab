"""For the ever-eligible symbols carrying missing sessions, split their missing
sessions into BEFORE first-eligible vs ON/AFTER first-eligible. If essentially
all missing sessions are pre-eligibility (illiquid early life), then a
per-session-eligibility-scoped audit would count ~0 for them -> the study never
trades the missing sessions -> safe. Any missing session DURING the eligible
window is a real gap for a tradeable name and must NOT be hidden.
"""
import os
import sys
import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.data.data_quality import find_latest_audit  # noqa: E402
from bowaka_v2_lab.optuna.calendar_sessions import calendar_sessions_half_open  # noqa: E402

LAKE = "/opt/market_data_cache"
BD = f"{LAKE}/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted"
MIN_ADV, MIN_PX, MAX_PX = 2_000_000, 1.0, 20.0
# the 6 in-probe ever-eligible + a few more for completeness
SYMS = ["AIB", "LIFE", "VIA", "AKTS", "SZZL", "ASBP"]

adf = pd.read_parquet(find_latest_audit(LAKE, feed="sip"))
adf["_sym"] = adf["symbol"].astype(str)


def analyze(sym):
    f = f"{BD}/symbol={sym}/part.parquet"
    if not os.path.isfile(f):
        return None
    df = pd.read_parquet(f).sort_values("timestamp")
    df["d"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
    have = set(df["d"])
    close = df["close"].astype(float)
    vol = df["volume"].astype(float)
    adv20 = (close * vol).rolling(20, min_periods=20).mean()
    px_prior, adv_prior = close.shift(1), adv20.shift(1)
    elig_mask = (px_prior >= MIN_PX) & (px_prior <= MAX_PX) & (adv_prior >= MIN_ADV)
    elig_dates = sorted(df["d"][elig_mask])
    if not elig_dates:
        return None
    first_elig, last_elig = elig_dates[0], elig_dates[-1]
    # expected calendar sessions across the audit window
    row = adf[adf["_sym"] == sym].iloc[0]
    start, end = pd.Timestamp(row["start"]).date(), pd.Timestamp(row["end"]).date()
    # half-open [start, end+1) so the audit end date is included
    cal = calendar_sessions_half_open(start, end + pd.Timedelta(days=1).to_pytimedelta(), calendar="XNYS")
    missing = [d for d in cal if d not in have]
    miss_before = [d for d in missing if d < first_elig]
    miss_in_window = [d for d in missing if first_elig <= d <= last_elig]
    # of the eligible sessions, how many lack a daily bar (the real-gap metric)
    elig_missing = [d for d in elig_dates if d not in have]  # by construction ~0
    return {
        "missing": len(missing), "first_elig": first_elig, "last_elig": last_elig,
        "n_elig": len(elig_dates), "miss_before_elig": len(miss_before),
        "miss_in_elig_window": len(miss_in_window),
        "miss_in_window_examples": [d.isoformat() for d in miss_in_window[:8]],
        "eligible_sessions_missing_bar": len(elig_missing),
    }


print("%-7s %7s %9s %12s %14s %16s" % (
    "sym", "missing", "n_elig", "miss<elig", "miss_in_win", "eligSess_noBar"))
total_in_window = 0
for sym in SYMS:
    a = analyze(sym)
    if a is None:
        print("%-7s  (no eligible window / no daily file)" % sym); continue
    total_in_window += a["miss_in_elig_window"]
    print("%-7s %7d %9d %12d %14d %16d   win=[%s..%s] %s" % (
        sym, a["missing"], a["n_elig"], a["miss_before_elig"], a["miss_in_elig_window"],
        a["eligible_sessions_missing_bar"], a["first_elig"], a["last_elig"],
        a["miss_in_window_examples"] if a["miss_in_elig_window"] else ""))

print("\n=== VERDICT ===")
print("total missing sessions falling INSIDE an eligible window (across the 6):", total_in_window)
print("eligible_sessions that themselves lack a daily bar (the real-gap metric): see last col")
if total_in_window == 0:
    print("=> SAFE: all missing sessions are in the pre-eligible (illiquid early-life) period.")
    print("   A per-session-eligibility-scoped audit counts 0 for these -> the study never")
    print("   trades a missing session. The symbol-level audit over-counts illiquid history.")
else:
    print("=> NUANCE: some missing sessions fall in eligible windows -> investigate those dates.")
