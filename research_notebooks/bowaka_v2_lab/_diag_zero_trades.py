"""Tightly focus on WHY 26 of 29 decisions are being rejected.
Run the same backtest, then group decisions by `decision` value and
`reason`, then dump a full rejected decision so we can see the rejection
reason in context."""
import sys
sys.path.insert(0, "src")
sys.path.insert(0, "../bowaka_common/src")

import datetime as dt
import json
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

cfg = load_config("configs/bowaka_v2_actual_iex_current_code.yml")
feed = cfg.get("market_data", {}).get("feed", "iex")
lake_root = resolve_lake_root(cfg)

session = dt.date(2025, 8, 27)
sessions = [session]

universe = build_pit_universe_for_sessions(sessions, cfg, MarketDataStore(lake_root))
sess_syms = eligible_symbols(universe.get(session, {}))
daily_cache = {session: build_daily_cache_from_lake(lake_root, sess_syms, session, feed=feed)}
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

print(f"candidates={len(res.candidate_events)}, decisions={len(res.decisions)}, trades={len(res.trades)}")

# Group decisions by `decision` value, then by `reason`.
print()
print("=== decisions grouped by .decision ===")
ctr_decision = Counter(d.get("decision", "<missing>") for d in res.decisions)
for k, v in ctr_decision.most_common():
    print(f"  {k:30s} {v}")

print()
print("=== rejected decisions grouped by .reason ===")
rejected = [d for d in res.decisions if d.get("decision") not in ("accept", "accepted", "ENTER", "enter")]
ctr_reason = Counter(d.get("reason", "<missing>") for d in rejected)
for k, v in ctr_reason.most_common():
    print(f"  {k:60s} {v}")

# What does an accepted decision look like? And a rejected one?
accepted = [d for d in res.decisions if d.get("decision") in ("accept", "accepted", "ENTER", "enter")]
print()
print(f"=== ONE accepted decision (of {len(accepted)}) ===")
if accepted:
    print(json.dumps(accepted[0], indent=2, default=str))

print()
print(f"=== ONE rejected decision (of {len(rejected)}) ===")
if rejected:
    print(json.dumps(rejected[0], indent=2, default=str))

print()
print(f"=== second rejected decision (different .reason if possible) ===")
seen_reasons = {rejected[0].get("reason")} if rejected else set()
for d in rejected[1:]:
    if d.get("reason") not in seen_reasons:
        print(json.dumps(d, indent=2, default=str))
        seen_reasons.add(d.get("reason"))
        break
