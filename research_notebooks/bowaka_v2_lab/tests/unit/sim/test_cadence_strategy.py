"""``CadenceConfig.cadence_strategy`` selects preload vs lazy.

Speedup report §6.3 / §11.2 Phase 6. Default ``"preload"`` preserves
bit-identical behaviour. ``"lazy"`` is parsed but the backtester refuses
to opt in until the Phase 6 parity matrix proves identical FoldResults.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from bowaka_v2_lab.sim.event_loop import (
    CadenceConfig,
    preload_session_events,
    preload_session_events_lazy,
    next_tick_at_or_after,
)


def test_default_cadence_strategy_is_preload():
    c = CadenceConfig()
    assert c.cadence_strategy == "preload"


def test_from_cfg_reads_strategy_from_session_block():
    c = CadenceConfig.from_cfg({"session": {"cadence_strategy": "lazy"}})
    assert c.cadence_strategy == "lazy"


def test_from_cfg_reads_strategy_from_simulation_block():
    c = CadenceConfig.from_cfg({"simulation": {"cadence_strategy": "lazy"}})
    assert c.cadence_strategy == "lazy"


def test_from_cfg_default_is_preload():
    c = CadenceConfig.from_cfg({})
    assert c.cadence_strategy == "preload"


def test_invalid_strategy_raises():
    with pytest.raises(ValueError):
        CadenceConfig.from_cfg({"session": {"cadence_strategy": "warp9"}})


def test_lazy_preload_emits_only_scan_and_eod():
    sd = dt.date(2024, 9, 4)
    scan_times = [pd.Timestamp(f"2024-09-04T{h:02d}:00:00", tz="UTC") for h in (14, 15)]
    events = preload_session_events_lazy(
        session_date=sd, scan_times=scan_times, cadence=CadenceConfig(),
    )
    types = [e.type.name for e in events]
    assert types.count("SCAN") == 2
    assert types.count("EOD_MARK") == 1
    assert "PROTECTION_CHECK" not in types
    assert "QUOTE" not in types
    assert "TIME_STOP_CHECK" not in types


def test_preload_emits_full_event_set():
    """Sanity: the legacy preload still includes every event type."""
    sd = dt.date(2024, 9, 4)
    scan_times = [pd.Timestamp(f"2024-09-04T{h:02d}:00:00", tz="UTC") for h in (14, 15)]
    events = preload_session_events(
        session_date=sd, scan_times=scan_times, cadence=CadenceConfig(),
    )
    types = {e.type.name for e in events}
    assert "SCAN" in types
    assert "EOD_MARK" in types
    assert "PROTECTION_CHECK" in types
    assert "QUOTE" in types
    assert "TIME_STOP_CHECK" in types


def test_next_tick_at_or_after_aligns_to_grid():
    anchor = pd.Timestamp("2024-09-04T14:00:00", tz="UTC")
    # 5s grid: next tick after 14:00:03 is 14:00:05.
    ts = pd.Timestamp("2024-09-04T14:00:03", tz="UTC")
    assert next_tick_at_or_after(ts, 5, anchor=anchor) == \
        pd.Timestamp("2024-09-04T14:00:05", tz="UTC")
    # Exact alignment returns the same ts.
    assert next_tick_at_or_after(anchor, 5, anchor=anchor) == anchor
    # 60s grid: 14:00:01 → 14:01:00.
    assert next_tick_at_or_after(
        pd.Timestamp("2024-09-04T14:00:01", tz="UTC"), 60, anchor=anchor,
    ) == pd.Timestamp("2024-09-04T14:01:00", tz="UTC")


def test_backtester_refuses_lazy_strategy(tmp_path):
    """The backtester refuses cadence_strategy='lazy' until the parity matrix lands."""
    import datetime as _dt
    from pathlib import Path

    import pandas as pd

    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.sim.backtester import run_backtest
    from tests.fixtures.build_daily_fixture import make_daily_bars
    from tests.fixtures.build_minute_fixture import make_minute_bars

    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5,
                             minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {
        sd: {"universe_hash": "sha256:t",
             "symbols": [{"symbol": "AAA", "exchange": "NASDAQ",
                          "venue_code": "XNAS",
                          "instrument_class": "operating_equity",
                          "eligible_for_bowaka_equity_bucket": True}]}
    }
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                       "avg_dollar_volume_20d": 5_000_000,
                                       "prior_atr_pct": 0.02,
                                       "ema_slope_prior": 0.01}])}
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {}, "execution": {"max_spread_bps": 200,
                                       "max_quote_age_seconds": 60,
                                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                  "max_gross_exposure_pct": 0.5, "daily_loss_pct": 0.5,
                  "max_stopouts_per_day": 4,
                  "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10,
                   "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                      "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "session": {"cadence_strategy": "lazy"},
    }
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    with pytest.raises(RuntimeError, match="lazy"):
        run_backtest(
            cfg=cfg, sessions=[sd],
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=lambda sym, ts: bars,
            daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
            initial_bankroll=10_000.0, paths=paths,
        )
