"""Scout the two remaining intended_realism gates before fanning out:
  (1) audit_missing_sessions (count=1762) — read the lake audit parquet, decompose
      the missing_sessions total by whether the symbol is EVER PIT-eligible in the
      probe window (same over-inclusion test as audit #1).
  (2) coverage_missing first-scan (09:45) — from the staged _pair_dataset.csv,
      split the eligible misses into daily-leg vs minute-leg, and within the
      minute leg: traded-later-that-day (carry-forward-able) vs no-session-bars.
"""
import sys
import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]

print("=" * 70)
print("(1) audit_missing_sessions — lake audit parquet")
print("=" * 70)
from bowaka_v2_lab.data.data_quality import find_latest_audit  # noqa: E402

audit_path = find_latest_audit("/opt/market_data_cache", feed="sip")
print("audit_path:", audit_path)
if audit_path is not None:
    adf = pd.read_parquet(audit_path)
    print("rows:", len(adf), "| columns:", list(adf.columns))
    if "missing_sessions" in adf.columns:
        ms = pd.to_numeric(adf["missing_sessions"], errors="coerce").fillna(0).astype(int)
        print("total missing_sessions (ALL audit rows):", int(ms.sum()))
        print("symbols with missing_sessions>0:", int((ms > 0).sum()))
        # decompose vs ever-eligible in the probe window (from the staged CSV)
        cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
        ever_elig = set(cdf[cdf.daily_eligible == 1].symbol.astype(str))
        probe_syms = set(cdf.symbol.astype(str))
        adf["_sym"] = adf["symbol"].astype(str)
        adf["_ms"] = ms
        in_probe = adf[adf["_sym"].isin(probe_syms)]
        print("\n-- restricted to the 2425 probe symbols (what the check sums) --")
        print("  missing_sessions total:", int(in_probe["_ms"].sum()))
        elig = in_probe[in_probe["_sym"].isin(ever_elig)]
        inelig = in_probe[~in_probe["_sym"].isin(ever_elig)]
        tot = int(in_probe["_ms"].sum()) or 1
        print("  ever-eligible symbols : %d rows, missing_sessions=%d (%.1f%%)" % (
            len(elig), int(elig["_ms"].sum()), 100 * int(elig["_ms"].sum()) / tot))
        print("  never-eligible symbols: %d rows, missing_sessions=%d (%.1f%%)" % (
            len(inelig), int(inelig["_ms"].sum()), 100 * int(inelig["_ms"].sum()) / tot))
        print("  examples never-eligible w/ missing_sessions:",
              inelig[inelig["_ms"] > 0].sort_values("_ms", ascending=False)["_sym"].head(8).tolist())

print()
print("=" * 70)
print("(2) coverage_missing — first scan (09:45 ET), eligible pairs only")
print("=" * 70)
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
elig = cdf[cdf.daily_eligible == 1].copy()
print("eligible (symbol,session) pairs:", len(elig), "(expected_g was 5758)")
# first-scan miss proxy: the coverage_missing minute leg probes 09:45 only.
# has_session_bars==0 -> no trade at all that day (minute leg missing for sure).
# has_session_bars==1 but first_trade_et > 09:45 -> traded later (carry-forward-able first-scan miss).
# has_session_bars==1 and first_trade_et <= 09:45 -> had a 09:45 bar (not a first-scan miss).
def ft_after_0945(ft):
    try:
        hh, mm = str(ft)[:5].split(":")
        return (int(hh) * 60 + int(mm)) > (9 * 60 + 45)
    except Exception:
        return True  # no first_trade -> didn't trade -> miss
elig["no_session_bars"] = elig.has_session_bars == 0
elig["traded_after_0945"] = elig.apply(lambda r: (r.has_session_bars == 1) and ft_after_0945(r.first_trade_et), axis=1)
elig["had_0945_bar"] = (elig.has_session_bars == 1) & (~elig["traded_after_0945"])
n = len(elig)
print("  no_session_bars (no trade all day)      : %d (%.1f%%)" % (elig.no_session_bars.sum(), 100*elig.no_session_bars.sum()/n))
print("  traded_after_0945 (carry-forward-able)  : %d (%.1f%%)" % (elig.traded_after_0945.sum(), 100*elig.traded_after_0945.sum()/n))
print("  had_0945_bar (not a first-scan miss)    : %d (%.1f%%)" % (elig.had_0945_bar.sum(), 100*elig.had_0945_bar.sum()/n))
# of the no_session_bars eligible: do they at least have a daily bar that day? (daily leg)
print("\n  no_session_bars breakdown (the 'genuine no-trade' bucket):")
nsb = elig[elig.no_session_bars]
print("    has_min_month_file=1 (month file, 0 bars that date):", int((nsb.has_min_month_file==1).sum()))
print("    has_min_month_file=0 (no minute file at all)       :", int((nsb.has_min_month_file==0).sum()))
# carry-forward-able total = had a prior_close => price exists to carry
print("\n  eligible misses with a prior_close (carry-forward price available):",
      int(((elig.no_session_bars | elig.traded_after_0945) & elig.prior_close.notna()).sum()),
      "/", int((elig.no_session_bars | elig.traded_after_0945).sum()))
