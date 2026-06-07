"""Verify whether the dominant preflight miss category (no_minute_file) is a
minute-backfill coverage gap (PIT-eligible symbols absent from the minute lake)
rather than illiquid no-trade microstructure."""
import json
from pathlib import Path

B1 = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw")
BD = Path("/opt/market_data_cache/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted")

print("=== no_minute_file examples: do they have DAILY bars? any minute anywhere? ===")
for sym in ["AAOI", "ABTS", "ACON", "ADNT", "ACHC", "ABX"]:
    sd = B1 / ("symbol=" + sym)
    months = sorted(set(str(p).split("year=")[1][:7].replace("/month=", "-")
                        for p in sd.rglob("part.parquet"))) if sd.is_dir() else []
    daily = (BD / ("symbol=" + sym + "/part.parquet")).is_file()
    print("  %-6s daily=%-5s minute_months=%d %s" % (sym, daily, len(months), months[:5]))

minute_syms = set(p.name.split("=", 1)[1] for p in B1.glob("symbol=*"))
probe_syms = set()
for line in open("/quants-lab/scripts/_probe_log_2m.jsonl"):
    try:
        probe_syms.add(json.loads(line)["sym"])
    except Exception:
        pass
both = probe_syms & minute_syms
miss = probe_syms - minute_syms
print("=== overlap: PIT-probe symbols vs minute-lake symbols ===")
print("  minute-lake symbols      : %d" % len(minute_syms))
print("  PIT-probe symbols        : %d" % len(probe_syms))
print("  probe WITH minute anywhere: %d (%d%%)" % (len(both), round(100 * len(both) / len(probe_syms))))
print("  probe with NO minute file : %d (%d%%)" % (len(miss), round(100 * len(miss) / len(probe_syms))))
print("  sample missing           : %s" % sorted(miss)[:12])
