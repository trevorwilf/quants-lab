"""Pending position read from features.signal_strength (§15.2 P1 fix)."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def _candidate(signal_strength: float = 5.0) -> dict:
    return {
        "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-04",
        "scan_timestamp": "2024-09-04T13:30:00Z",
        "forming_session_bar": {"last_price": 100.0, "session_high": 101.0, "session_low": 99.5},
        "features": {"signal_strength": signal_strength},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000},
    }


def _make_consumer(min_signal_strength: float):
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    return p, StrategyConsumer(
        portfolio=p, broker=SimulatedBroker(),
        cfg={
            "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                            "order_type": "marketable_limit"},
            "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000},
            "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                       "max_gross_exposure_pct": 0.5, "daily_loss_pct": 0.5,
                       "max_stopouts_per_day": 4,
                       "stop_trading_after_consecutive_stopouts": 3},
            "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 5},
            "scanner": {"min_signal_strength": min_signal_strength},
            "backtest": {"cost_stress": "base"},
        },
    )


def test_signal_strength_below_threshold_rejects() -> None:
    portfolio, consumer = _make_consumer(min_signal_strength=10.0)
    result = consumer.consume(_candidate(signal_strength=2.0),
                                decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    assert result.decisions[0]["decision"] == "rejected"
    assert result.decisions[0]["reason"] == "lost_signal_before_entry"


def test_signal_strength_above_threshold_accepts() -> None:
    portfolio, consumer = _make_consumer(min_signal_strength=1.0)
    result = consumer.consume(_candidate(signal_strength=5.0),
                                decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    assert len(result.new_positions) == 1
    assert result.decisions[0]["decision"] == "accepted"
