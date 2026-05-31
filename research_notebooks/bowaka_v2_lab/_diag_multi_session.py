import sys
sys.path.insert(0, "src")
sys.path.insert(0, "../bowaka_common/src")
import datetime as dt
from collections import Counter

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
from bowaka_v2_lab.optuna.calendar_sessions import calendar_sessions_half_open

cfg = load_config("configs/bowaka_v2_actual_iex_current_code.yml")
feed = cfg.get("market_data", {}).get("feed", "iex")
lake_root = resolve_lake_root(cfg)

# 10 consecutive trading sessions ending 2025-08-27.
sessions = calendar_sessions_half_open(dt.date(2025, 8, 13), dt.date(2025, 8, 28))
print(f"Testing across {len(sessions)} sessions: {sessions[0]} .. {sessions[-1]}")

universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
daily_cache = {
    s: build_daily_cache_from_lake(lake_root, eligible_symbols(universe.get(s, {})), s, feed=feed)
    for s in sessions
}
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

print()
print(f"=== totals across {len(sessions)} sessions ===")
print(f"candidates:    {len(res.candidate_events)}")
print(f"decisions:     {len(res.decisions)}")
print(f"  accepted:    {sum(1 for d in res.decisions if d.get('decision') == 'accepted')}")
print(f"  rejected:    {sum(1 for d in res.decisions if d.get('decision') == 'rejected')}")
print(f"trades:        {len(res.trades)}")

# Per-session trade distribution.
by_session = Counter()
for d in res.decisions:
    if d.get("decision") == "accepted":
        by_session[d.get("session_date")] += 1

print()
print("=== trades per session ===")
for s in sessions:
    n = by_session.get(str(s), 0)
    print(f"  {s}: {n:3d} trades  {'#' * n}")

print()
print(f"avg trades/session: {len(res.trades) / len(sessions):.2f}")
print(f"min_trades_per_fold for audit Phase 5: 5")
print(f"with this avg, a fold passes if it spans >= {5 / max(len(res.trades) / len(sessions), 0.01):.0f} sessions")
