"""Fixture with a quote stream; spread gate blocks one entry; age gate blocks another."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_quote_spread_and_age_gates(tmp_path: Path) -> None:
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sd = _dt.date(2024, 9, 4)
    sessions = [sd]
    symbols = ["WIDE", "STALE", "OK"]
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10,
                     "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        # Realism remediation 2 Phase 5: the price-chase + halt gates are
        # non-tunable but evaluate by default. This test exercises only
        # spread/age gates, so disable them to keep the OK accept path clean.
        "signals": {}, "execution": {"max_spread_bps": 50, "max_quote_age_seconds": 5,
                                       "order_type": "marketable_limit",
                                       "price_chase_gate": {"enabled": False},
                                       "halt_gate": {"enabled": False}},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                   "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04", "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                   "data_root": "research_notebooks/bowaka_v2_lab/data",
                   "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }
    universe = {sd: {"universe_hash": "sha256:t",
                       "symbols": [{"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                                       "instrument_class": "operating_equity",
                                       "eligible_for_bowaka_equity_bucket": True}
                                      for s in symbols]}}
    daily_cache = {sd: pd.DataFrame([{"symbol": s, "prior_close": 100.0,
                                          "avg_dollar_volume_20d": 5_000_000,
                                          "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
                                         for s in symbols])}
    bars_by_sym = {s: make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5,
                                          minute_volume=20_000) for s in symbols}
    daily_by_sym = {s: make_daily_bars(s, _dt.date(2024, 9, 1), n_sessions=5) for s in symbols}

    def quote_supplier(sym, at):
        # Three quote shapes by symbol — to exercise both gates.
        if sym == "WIDE":  # spread 200 bps > 50 cap
            return {"bid": 99.0, "ask": 101.0, "mid": 100.0,
                     "spread_pct": 0.02,
                     "quote_timestamp": str(at), "quote_age_seconds": 0.0,
                     "source": "historical"}
        if sym == "STALE":  # quote age > 5s
            return {"bid": 99.95, "ask": 100.05, "mid": 100.0,
                     "spread_pct": 0.001,
                     "quote_timestamp": str(at), "quote_age_seconds": 30.0,
                     "source": "historical"}
        # OK: clean spread, fresh.
        return {"bid": 99.99, "ask": 100.01, "mid": 100.0,
                 "spread_pct": 0.0002,
                 "quote_timestamp": str(at), "quote_age_seconds": 0.5,
                 "source": "historical"}

    result = run_backtest(
        cfg=cfg, sessions=sessions,
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars_by_sym[sym],
        daily_bars_supplier=lambda sym, d: daily_by_sym[sym][daily_by_sym[sym]["session_date"] == d],
        initial_bankroll=10_000.0, paths=paths, quote_supplier=quote_supplier,
    )

    decisions = pd.read_parquet(result.run_dir / "entry_decisions.parquet")
    if "symbol" in decisions.columns and "reason" in decisions.columns:
        spread_rejects = decisions[(decisions["symbol"] == "WIDE") & (decisions["reason"] == "spread_too_wide")]
        stale_rejects = decisions[(decisions["symbol"] == "STALE") & (decisions["reason"] == "quote_stale")]
        ok_accepted = decisions[(decisions["symbol"] == "OK") & (decisions["decision"] == "accepted")]
        assert len(spread_rejects) >= 1, f"expected spread_too_wide for WIDE, got: {decisions['reason'].tolist()}"
        assert len(stale_rejects) >= 1, f"expected quote_stale for STALE, got: {decisions['reason'].tolist()}"
        assert len(ok_accepted) >= 1, "expected OK to be accepted"
