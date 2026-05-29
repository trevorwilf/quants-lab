"""Bounded diagnostic: run the incumbent (actual-contract) params over a SINGLE
trading session (full universe) and report candidate / decision / trade counts.

Answers the -1.5-floor question fast (~minutes, one day) instead of a multi-hour
full fold:
  * candidate_events == 0  -> scanner/gates emit nothing (systemic, scanner-level)
  * candidates > 0, trades == 0 -> emitted but no fills (quote/fill/risk gate)
  * trades > 0             -> incumbent trades normally; -1.5 is unfit RANDOM
                             trial params, not a systemic bug

Run:
  cd research_notebooks/bowaka_v2_lab
  PYTHONPATH=src:../bowaka_common/src python scripts/diag_incumbent_session.py \
      --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--max-symbols", type=int, default=0,
                   help="Cap the universe to the first N eligible symbols (0 = full).")
    args = p.parse_args(argv)

    import pandas as pd

    from bowaka_common.marketdata import MarketDataStore
    from bowaka_v2_lab.config import load_config
    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.data.lineage import resolve_lake_root
    from bowaka_v2_lab.data.suppliers import (
        build_daily_cache_from_lake, make_forward_minute_supplier,
        make_lake_suppliers, make_quote_supplier, resolve_intraday_window_policy,
    )
    from bowaka_v2_lab.optuna.calendar_sessions import calendar_sessions_half_open
    from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
    from bowaka_v2_lab.optuna.walkforward_runner import (
        _incumbent_baseline_params, apply_trial_params,
    )
    from bowaka_v2_lab.sim.backtester import run_backtest
    from bowaka_v2_lab.sim.schedule import scan_times_for_session
    from bowaka_v2_lab.universe.builder import (
        build_pit_universe_for_sessions, eligible_symbols,
    )

    cfg = load_config(args.config)
    lake_root = resolve_lake_root(cfg)
    feed = str((cfg.get("market_data") or {}).get("feed", "iex"))
    bt = cfg.get("backtest") or {}
    wf = (cfg.get("optuna") or {}).get("walkforward") or {}
    plan = build_walkforward_splits(
        full_start=pd.Timestamp(bt["start_date"]).date(),
        full_end=pd.Timestamp(bt["end_date"]).date(),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    split = plan.splits[0]
    sessions = calendar_sessions_half_open(split.val_start, split.val_end)
    session = sessions[0]
    print(f"[diag] single session = {session} (first of val window "
          f"{split.val_start}..{split.val_end}, {len(sessions)} sessions)")

    # Disable per-study acceleration caches (they add the ~13-min content hash
    # cold cost; irrelevant for a one-session probe). Legacy scanner path.
    cfg = dict(cfg)
    cfg.setdefault("optuna", {})
    cfg["optuna"] = dict(cfg["optuna"])
    cfg["optuna"]["acceleration"] = {"scan_matrix": {"enabled": False}}

    store = MarketDataStore(lake_root)
    pit = build_pit_universe_for_sessions([session], dict(cfg), store)
    syms = sorted(eligible_symbols(pit.get(session, {})) or [])
    if args.max_symbols and len(syms) > args.max_symbols:
        syms = syms[: args.max_symbols]
    print(f"[diag] eligible symbols this session = {len(syms)}")

    policy = resolve_intraday_window_policy(cfg)
    minute_sup, daily_sup = make_lake_suppliers(
        lake_root, feed=feed, intraday_window_policy=policy,
    )
    quote_sup = make_quote_supplier(lake_root, feed=feed, default_max_age_seconds=60.0)
    fwd_sup = make_forward_minute_supplier(lake_root, feed=feed)
    daily_cache = build_daily_cache_from_lake(lake_root, syms, session, feed=feed)
    universe = {
        session: {
            "universe_hash": "sha256:diag",
            "symbols": [
                {"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                 "instrument_class": "operating_equity",
                 "eligible_for_bowaka_equity_bucket": True}
                for s in syms
            ],
        }
    }

    incumbent = _incumbent_baseline_params()
    cfg_inc = apply_trial_params(cfg, incumbent)
    repo_root = Path(__file__).resolve().parents[5]
    paths = BowakaV2Paths.from_config(cfg_inc, repo_root=repo_root)

    t0 = _dt.datetime.now()
    result = run_backtest(
        cfg=cfg_inc, sessions=[session],
        scan_times_per_session=lambda d: list(scan_times_for_session(d, dict(cfg_inc))),
        universe_snapshot_by_session=universe,
        daily_cache_by_session={session: daily_cache},
        minute_bars_supplier=minute_sup,
        daily_bars_supplier=daily_sup,
        quote_supplier=quote_sup,
        forward_minute_supplier=fwd_sup,
        initial_bankroll=100_000.0,
        paths=paths,
        artifact_mode="objective_minimal",
    )
    elapsed = (_dt.datetime.now() - t0).total_seconds()

    n_cand = len(result.candidate_events)
    n_dec = len(result.decisions)
    n_accepted = sum(1 for d in result.decisions if d.get("decision") == "accepted")
    n_orders = len(result.orders)
    n_fills = sum(1 for f in result.fills if f.get("filled"))
    n_trades = len(result.trades)
    print(f"[diag] elapsed={elapsed:.1f}s")
    print("[diag] counts:")
    print(json.dumps({
        "candidate_events": n_cand,
        "decisions": n_dec,
        "accepted_decisions": n_accepted,
        "orders": n_orders,
        "fills_filled": n_fills,
        "trades": n_trades,
    }, indent=2))
    # Scanner rejection breakdown (why candidates were/weren't emitted).
    sc = result.summary.get("scan_counts") if isinstance(result.summary, dict) else None
    if sc:
        print("[diag] scan_counts:", json.dumps(sc, indent=2, default=str)[:1500])
    if n_cand == 0:
        verdict = "SYSTEMIC (scanner emits NO candidates even with incumbent params)"
    elif n_trades == 0:
        verdict = "candidates emitted but NO trades (fill/quote/risk gate blocks entries)"
    else:
        verdict = "incumbent TRADES normally -> -1.5 is unfit RANDOM trial params, not systemic"
    print(f"[diag] VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
