"""Realism Phase 5 — `accepted_event_sequencing == "post_submit"` (realism).

In post_submit mode `submitted_pending` is emitted after the gates pass;
`accepted` is emitted ONLY after the broker confirms. A broker reject produces
`submitted_pending` THEN `broker_reject` — never `accepted` — and no position.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def _candidate() -> dict:
    return {
        "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-04",
        "scan_timestamp": "2024-09-04T13:30:00Z",
        "forming_session_bar": {"last_price": 100.0, "session_high": 101.0, "session_low": 99.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }


def _cfg() -> dict:
    return {
        # intended_realism resolves accepted_event_sequencing -> post_submit.
        "simulation": {"mode": "intended_realism"},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000,
                   "sizing_mode": "fixed_dollar", "max_concurrent_positions": 50},
        "risk": {"max_total_entries_per_day": 99,
                 "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99,
                 "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99,
                 "max_lots_per_symbol": 5},
        "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 30},
        "scanner": {"min_signal_strength": 0.0},
        "backtest": {"cost_stress": "base"},
    }


def test_post_submit_broker_reject_emits_submitted_pending_then_broker_reject() -> None:
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    rejecting_broker = SimulatedBroker(
        fail_predicate=lambda po: {"code": "INSUFFICIENT_BP", "msg": "no buying power"}
    )
    consumer = StrategyConsumer(portfolio=p, broker=rejecting_broker, cfg=_cfg())
    assert consumer.accepted_event_sequencing == "post_submit"

    res = consumer.consume(_candidate(),
                           decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))

    decisions = res.decisions
    # submitted_pending first, broker_reject second — and NEVER `accepted`.
    assert len(decisions) == 2
    assert decisions[0]["decision"] == "submitted_pending"
    assert decisions[1]["reason"] == "broker_reject"
    assert all(d["decision"] != "accepted" for d in decisions)

    # The broker rejected → no position created.
    assert len(p.open_positions) == 0
    assert len(res.new_positions) == 0


def test_post_submit_broker_accept_emits_submitted_pending_then_accepted() -> None:
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())

    res = consumer.consume(_candidate(),
                           decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    # Broker confirmed — submitted_pending THEN accepted, in that order.
    assert [d["decision"] for d in res.decisions] == ["submitted_pending", "accepted"]
    assert res.decisions[1]["reason"] == "all_gates_passed"
    assert len(p.open_positions) == 1
