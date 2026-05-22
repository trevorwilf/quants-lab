"""Realism Phase 5 — `same_symbol_entries_per_day` caps per-session entries.

A symbol may be re-entered across sessions (up to `max_lots_per_symbol`), but a
SECOND entry for the same symbol within ONE session is rejected with the
canonical reason `same_symbol_entries_per_day` (default cap: 1).
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def _candidate(ts: str) -> dict:
    return {
        "event_id": f"bowaka_v2:2024-09-04:AAA:{ts}",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-04",
        "scan_timestamp": ts,
        "forming_session_bar": {"last_price": 100.0, "session_high": 101.0, "session_low": 99.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }


def _cfg() -> dict:
    return {
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000,
                   "sizing_mode": "fixed_dollar", "max_concurrent_positions": 50},
        "risk": {"max_total_entries_per_day": 99,
                 "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99,
                 "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99,
                 # Plenty of lot headroom — the per-day cap, not the lot cap,
                 # must be what rejects the 2nd same-session entry.
                 "max_lots_per_symbol": 5},
        "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 30},
        "scanner": {"min_signal_strength": 0.0},
        "backtest": {"cost_stress": "base"},
    }


def test_second_same_session_entry_rejected() -> None:
    p = Portfolio(initial_bankroll=1_000_000.0)
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())
    p.begin_session(_dt.date(2024, 9, 4))

    res1 = consumer.consume(_candidate("2024-09-04T13:30:00Z"),
                            decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    assert res1.decisions[-1]["decision"] == "accepted"

    # Second candidate for AAA in the SAME session.
    res2 = consumer.consume(_candidate("2024-09-04T14:00:00Z"),
                            decision_ts=pd.Timestamp("2024-09-04 14:00:01", tz="UTC"))
    assert res2.decisions[-1]["decision"] == "rejected"
    assert res2.decisions[-1]["reason"] == "same_symbol_entries_per_day"
    # Only one lot opened despite two candidates.
    assert p.lots_for_symbol("AAA") == 1


def test_next_session_entry_allowed_after_per_day_cap() -> None:
    # The per-day cap is per session — a fresh session re-allows the symbol.
    p = Portfolio(initial_bankroll=1_000_000.0)
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())

    p.begin_session(_dt.date(2024, 9, 4))
    consumer.consume(_candidate("2024-09-04T13:30:00Z"),
                     decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))

    p.begin_session(_dt.date(2024, 9, 5))
    ev = {
        "event_id": "bowaka_v2:2024-09-05:AAA:2024-09-05T13:30:00Z",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-05",
        "scan_timestamp": "2024-09-05T13:30:00Z",
        "forming_session_bar": {"last_price": 100.0, "session_high": 101.0, "session_low": 99.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }
    res = consumer.consume(ev, decision_ts=pd.Timestamp("2024-09-05 13:30:01", tz="UTC"))
    assert res.decisions[-1]["decision"] == "accepted"
    assert p.lots_for_symbol("AAA") == 2
