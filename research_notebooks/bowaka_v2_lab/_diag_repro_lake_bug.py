"""Confirm the lake-root bug by deliberately passing a bad path.
Expected output: 0 candidates, 0 trades, no error — matches walkforward worker."""
import sys, datetime as dt
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, "../bowaka_common/src")

from bowaka_common.marketdata.store import MarketDataStore
from bowaka_v2_lab.config import load_config
from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config
from bowaka_v2_lab.data.suppliers import (
    make_lake_suppliers, make_quote_supplier, make_forward_minute_supplier,
    build_daily_cache_from_lake, resolve_intraday_window_policy,
)
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions, eligible_symbols

cfg = load_config("configs/bowaka_v2_actual_iex_current_code.yml")
feed = cfg.get("market_data", {}).get("feed", "iex")

# DELIBERATELY BAD: simulate what the worker sees when md.get("shared_root") = None
bad_lake = Path("None")
print(f"Forcing bad lake_root: {bad_lake.resolve()}")

minute_supplier, daily_supplier = make_lake_suppliers(
    bad_lake, feed=feed,
    intraday_window_policy=resolve_intraday_window_policy(cfg),
    daily_adjustment=daily_adjustment_for_config(cfg),
)
quote_supplier = make_quote_supplier(bad_lake, feed=feed, default_max_age_seconds=60)
forward_minute_supplier = make_forward_minute_supplier(bad_lake, feed=feed)

# Universe building uses MarketDataStore directly. Use the real lake for this
# so we get a non-empty universe — that mirrors the parent's preflight which
# DID find 697 symbols, before handing off to workers that read no actual bars.
real_universe = build_pit_universe_for_sessions(
    [dt.date(2025, 8, 27)], cfg,
    MarketDataStore(Path("../market_data"))   # use real lake
)
sess_syms = eligible_symbols(real_universe.get(dt.date(2025, 8, 27), {}))
print(f"Universe (from real lake): {len(sess_syms)} symbols")

# Daily cache from real lake (mimics parent doing the cache, then workers
# reading bars via the bad supplier).
daily_cache = {dt.date(2025, 8, 27): build_daily_cache_from_lake(
    Path("../market_data"), sess_syms, dt.date(2025, 8, 27), feed=feed)}

res = run_backtest(
    cfg=cfg, sessions=[dt.date(2025, 8, 27)],
    scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
    universe_snapshot_by_session=real_universe,
    daily_cache_by_session=daily_cache,
    minute_bars_supplier=minute_supplier,   # BAD — reads from "None/..."
    daily_bars_supplier=daily_supplier,     # BAD — reads from "None/..."
    quote_supplier=quote_supplier,
    forward_minute_supplier=forward_minute_supplier,
)

print()
print("=== if lake-root bug is the cause, expect 0/0/0 ===")
print(f"candidates: {len(res.candidate_events)}")
print(f"decisions:  {len(res.decisions)}")
print(f"trades:     {len(res.trades)}")
print(f"quote_coverage_pct: {res.summary.get('historical_quote_coverage_pct')}")
