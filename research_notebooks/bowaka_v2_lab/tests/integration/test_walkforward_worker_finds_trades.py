"""Confirm trial 0 against the operator's real lake produces non-trivial
trade activity. Skipif lake not present (CI).
"""
from __future__ import annotations

import datetime as dt

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def lake_root():
    """Resolve the lake root via the lab's resolver. Skip if missing."""
    from bowaka_v2_lab.data.lineage import resolve_lake_root

    cfg = {"market_data": {"feed": "iex"}}
    try:
        root = resolve_lake_root(cfg)
    except RuntimeError:
        pytest.skip("lake not resolvable in this environment")
    if not root.is_dir():
        pytest.skip(f"lake root {root} does not exist")
    # Quick sanity probe: at least one split_adjusted symbol partition.
    probe = (
        root / "bars" / "vendor=alpaca" / "feed=iex"
        / "timeframe=1d" / "adjustment=split_adjusted"
    )
    if not probe.is_dir() or not any(probe.iterdir()):
        pytest.skip(f"no split_adjusted partitions at {probe}")
    return root


@pytest.mark.timeout(1200)  # 20-min upper bound for one fold-0-val session
def test_single_session_produces_nonzero_candidates(lake_root):
    """The post-fix lab must produce a non-trivial candidate count against
    the operator's real lake on a known-active session.

    Pre-fix symptom (reproduced 2026-05-29): 0 candidates, 100% quote
    coverage, fold_status='ok'.

    Post-fix expected: dozens of candidates, several trades, and
    ``historical_quote_coverage_pct: 0.0`` (IEX has no NBBO quotes).
    """
    from bowaka_common.marketdata.store import MarketDataStore

    from bowaka_v2_lab.config import load_config
    from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config
    from bowaka_v2_lab.data.suppliers import (
        build_daily_cache_from_lake,
        make_forward_minute_supplier,
        make_lake_suppliers,
        make_quote_supplier,
        resolve_intraday_window_policy,
    )
    from bowaka_v2_lab.sim.backtester import run_backtest
    from bowaka_v2_lab.sim.schedule import scan_times_for_session
    from bowaka_v2_lab.universe.builder import (
        build_pit_universe_for_sessions,
        eligible_symbols,
    )

    cfg = load_config("configs/bowaka_v2_actual_iex_current_code.yml")
    feed = cfg.get("market_data", {}).get("feed", "iex")
    session = dt.date(2025, 8, 27)
    sessions = [session]

    universe = build_pit_universe_for_sessions(
        sessions, cfg, MarketDataStore(lake_root),
    )
    sess_syms = eligible_symbols(universe.get(session, {}))
    if not sess_syms:
        pytest.skip(f"empty PIT universe for {session}")
    daily_cache = {
        session: build_daily_cache_from_lake(
            lake_root, sess_syms, session, feed=feed,
        )
    }
    minute_supplier, daily_supplier = make_lake_suppliers(
        lake_root, feed=feed,
        intraday_window_policy=resolve_intraday_window_policy(cfg),
        daily_adjustment=daily_adjustment_for_config(cfg),
    )
    quote_supplier = make_quote_supplier(
        lake_root, feed=feed,
        default_max_age_seconds=float(
            cfg.get("execution", {}).get("max_quote_age_seconds", 60)
        ),
    )
    forward_minute_supplier = make_forward_minute_supplier(
        lake_root, feed=feed,
    )
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
    # Pre-fix symptom regression markers:
    n_candidates = len(res.candidate_events)
    quote_coverage = res.summary.get("historical_quote_coverage_pct")
    assert n_candidates > 0, (
        f"expected nonzero candidates on a known-active fold-0-val session; "
        f"got {n_candidates}. Did the lake-root resolver regress?"
    )
    # IEX has no NBBO quotes, so coverage must be 0%, not 100%. 100% with
    # n_candidates>0 would mean a different but adjacent bug — quote-
    # coverage denominator-zero handling. We assert 0% here so we get a
    # clear signal if that regresses too.
    assert quote_coverage == 0.0 or quote_coverage is None, (
        f"expected 0% historical quote coverage on IEX; got "
        f"{quote_coverage}. The pre-fix bug reported 100% because the "
        f"denominator was zero — if it's 100% here, the resolver may have "
        f"regressed differently."
    )
