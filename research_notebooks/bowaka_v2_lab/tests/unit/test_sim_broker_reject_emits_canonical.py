"""Submit-failure path emits decision rejected with reason=broker_reject."""
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
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000},
    }


def test_broker_reject_path_emits_canonical_decision() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    rejecting_broker = SimulatedBroker(
        fail_predicate=lambda po: {"code": "INSUFFICIENT_BP", "msg": "no buying power"}
    )
    consumer = StrategyConsumer(
        portfolio=p, broker=rejecting_broker,
        cfg={
            "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                            "order_type": "marketable_limit"},
            "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000},
            "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                       "max_gross_exposure_pct": 0.5, "daily_loss_pct": 0.5,
                       "max_stopouts_per_day": 4,
                       "stop_trading_after_consecutive_stopouts": 3},
            "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 5},
            "scanner": {"min_signal_strength": 0.0},
            "backtest": {"cost_stress": "base"},
        },
    )
    result = consumer.consume(_candidate(), decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    assert len(result.decisions) == 1
    dec = result.decisions[0]
    assert dec["decision"] == "rejected"
    assert dec["reason"] == "broker_reject"
    assert "broker_status" in dec
    assert "raw_response_summary" in dec
    # No position was added because broker rejected.
    assert len(p.open_positions) == 0
