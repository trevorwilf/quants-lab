"""Realism Phase 5 — `max_lots_per_symbol` caps concurrent lots per symbol.

With `risk.max_lots_per_symbol == 3`, a 4th entry attempt for the same symbol
is rejected with the canonical reason `max_lots_per_symbol`. Each of the first
three lots is opened on a distinct session so `same_symbol_entries_per_day`
does not pre-empt the cap.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def _candidate(session: str, ts: str) -> dict:
    return {
        "event_id": f"bowaka_v2:{session}:AAA:{ts}",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": session,
        "scan_timestamp": ts,
        "forming_session_bar": {"last_price": 100.0, "session_high": 101.0, "session_low": 99.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }


def _cfg(max_lots: int) -> dict:
    return {
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000,
                   "sizing_mode": "fixed_dollar", "max_concurrent_positions": 50},
        "risk": {"max_total_entries_per_day": 99,
                 "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99,
                 "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99,
                 "max_lots_per_symbol": max_lots},
        "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 30},
        "scanner": {"min_signal_strength": 0.0},
        "backtest": {"cost_stress": "base"},
    }


def test_fourth_lot_rejected_with_max_lots_per_symbol() -> None:
    p = Portfolio(initial_bankroll=1_000_000.0)
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg(max_lots=3))

    sessions = ["2024-09-04", "2024-09-05", "2024-09-06", "2024-09-09"]
    decisions = []
    for sess in sessions:
        p.begin_session(_dt.date.fromisoformat(sess))
        ts = f"{sess}T13:30:00Z"
        res = consumer.consume(_candidate(sess, ts),
                               decision_ts=pd.Timestamp(f"{sess} 13:30:01", tz="UTC"))
        decisions.append(res.decisions[-1])

    # First three sessions opened a lot each; the fourth is rejected.
    assert [d["decision"] for d in decisions] == ["accepted", "accepted", "accepted", "rejected"]
    assert decisions[3]["reason"] == "max_lots_per_symbol"
    assert p.lots_for_symbol("AAA") == 3


def test_max_lots_one_blocks_second_session_entry() -> None:
    # Default max_lots_per_symbol == 1 — a 2nd lot on a later session is rejected.
    p = Portfolio(initial_bankroll=1_000_000.0)
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg(max_lots=1))

    p.begin_session(_dt.date(2024, 9, 4))
    res1 = consumer.consume(_candidate("2024-09-04", "2024-09-04T13:30:00Z"),
                            decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    assert res1.decisions[-1]["decision"] == "accepted"

    p.begin_session(_dt.date(2024, 9, 5))
    res2 = consumer.consume(_candidate("2024-09-05", "2024-09-05T13:30:00Z"),
                            decision_ts=pd.Timestamp("2024-09-05 13:30:01", tz="UTC"))
    assert res2.decisions[-1]["decision"] == "rejected"
    assert res2.decisions[-1]["reason"] == "max_lots_per_symbol"
    assert p.lots_for_symbol("AAA") == 1
