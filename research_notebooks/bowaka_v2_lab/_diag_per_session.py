"""Per-session loop with progress prints. Tests just 5 sessions to start.
If you see consistent ~1 minute per session, run with more dates. If session 1
hangs, we know something else is wrong."""
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

# Build suppliers once (they're stateless).
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

# Five recent dates — hand-picked, not via calendar (so we're sure they
# are actually trading days in your lake).
test_sessions = [
    dt.date(2025, 8, 20),
    dt.date(2025, 8, 21),
    dt.date(2025, 8, 22),
    dt.date(2025, 8, 25),
    dt.date(2025, 8, 26),
]

total_candidates = 0
total_decisions = 0
total_accepted = 0
total_trades = 0

print(f"Lake: {lake_root}")
print(f"Testing {len(test_sessions)} sessions ({test_sessions[0]} .. {test_sessions[-1]})")
print()
print(f"  {'session':12s}  {'candidates':>10s}  {'decisions':>10s}  {'accepted':>10s}  {'trades':>8s}  {'elapsed':>8s}")
print(f"  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*8}")

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
    total_candidates += len(res.candidate_events)
    total_decisions += len(res.decisions)
    total_accepted += n_acc
    total_trades += len(res.trades)
    print(f"  {session}:  {len(res.candidate_events):10d}  {len(res.decisions):10d}  {n_acc:10d}  {len(res.trades):8d}  {elapsed:7.1f}s",
          flush=True)

print()
total_elapsed = time.time() - t0_total
n_done = len([s for s in test_sessions if True])  # just count
print(f"=== totals over {n_done} sessions ({total_elapsed:.1f}s) ===")
print(f"  candidates:  {total_candidates}")
print(f"  decisions:   {total_decisions}")
print(f"  accepted:    {total_accepted}")
print(f"  trades:      {total_trades}")
print(f"  avg trades/session: {total_trades / max(n_done, 1):.2f}")
print()
if total_trades > 0:
    sessions_for_5_trades = 5 / (total_trades / max(n_done, 1))
    print(f"At this rate, a fold needs ~{sessions_for_5_trades:.0f} sessions to clear min_trades_per_fold=5.")
