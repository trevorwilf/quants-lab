import sys
sys.path.insert(0, "src")
sys.path.insert(0, "../bowaka_common/src")
import datetime as dt
import time

from bowaka_common.marketdata.store import MarketDataStore
from bowaka_v2_lab.config import load_config
from bowaka_v2_lab.data.lineage import resolve_lake_root
from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config
from bowaka_v2_lab.data.suppliers import (
    make_lake_suppliers, make_quote_supplier, make_forward_minute_supplier,
    build_daily_cache_from_lake, resolve_intraday_window_policy,
)
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from bowaka_v2_lab.universe.builder import (
    build_pit_universe_for_sessions, eligible_symbols,
)

cfg = load_config("configs/bowaka_v2_actual_iex_current_code.yml")
feed = cfg.get("market_data", {}).get("feed", "iex")
lake_root = resolve_lake_root(cfg)

minute_supplier, daily_supplier = make_lake_suppliers(
    lake_root, feed=feed,
    intraday_window_policy=resolve_intraday_window_policy(cfg),
    daily_adjustment=daily_adjustment_for_config(cfg),
)
quote_supplier = make_quote_supplier(
    lake_root, feed=feed,
    default_max_age_seconds=float(cfg.get("execution", {}).get("max_quote_age_seconds", 60)),
)
forward_minute_supplier = make_forward_minute_supplier(lake_root, feed=feed)

# Dates spread across Fold 0's validation window (2025-08-27 to 2025-09-27).
test_sessions = [
    dt.date(2025, 9, 3),
    dt.date(2025, 9, 15),
    dt.date(2025, 9, 25),
]

print(f"Testing {len(test_sessions)} sessions inside Fold 0's val window")
print(f"  {'session':12s}  {'candidates':>10s}  {'decisions':>10s}  {'accepted':>10s}  {'trades':>8s}  {'elapsed':>8s}")

total_trades = 0
t0_total = time.time()
for session in test_sessions:
    t0 = time.time()
    sessions = [session]
    universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
    sess_syms = eligible_symbols(universe.get(session, {}))
    if not sess_syms:
        print(f"  {session}: empty universe, skipping")
        continue
    daily_cache = {session: build_daily_cache_from_lake(lake_root, sess_syms, session, feed=feed)}
    res = run_backtest(
        cfg=cfg, sessions=sessions,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        quote_supplier=quote_supplier,
        forward_minute_supplier=forward_minute_supplier,
    )
    n_acc = sum(1 for d in res.decisions if d.get("decision") == "accepted")
    elapsed = time.time() - t0
    total_trades += len(res.trades)
    print(f"  {session}:  {len(res.candidate_events):10d}  {len(res.decisions):10d}  {n_acc:10d}  {len(res.trades):8d}  {elapsed:7.1f}s",
          flush=True)

print()
print(f"=== if these 3 sessions also produce 5-10 trades each, the walkforward IS BUGGY ===")
print(f"trades across {len(test_sessions)} fold-0-val sessions: {total_trades}")
print(f"({time.time()-t0_total:.1f}s wall)")
