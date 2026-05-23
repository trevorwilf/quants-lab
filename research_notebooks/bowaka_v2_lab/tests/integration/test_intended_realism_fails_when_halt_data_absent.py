"""Audit P0-009: ``intended_realism`` rejects when the status supplier returns None.

When the halt gate is enabled but the status supplier returns ``None`` (no data
for this candidate), the gate's policy depends on simulation mode:

- ``intended_realism`` → reject with ``halt_data_unavailable``.
- ``current_code_parity`` → warn + fail-open (matches live wart).
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
        "forming_session_bar": {"last_price": 10.0, "session_high": 11.0, "session_low": 9.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }


def _quote() -> dict:
    return {
        "bid": 9.99, "ask": 10.01, "mid": 10.0, "spread_pct": 0.0002,
        "bid_size": 5000, "ask_size": 5000,
        "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 0.5,
        "source": "historical",
    }


def _cfg(mode: str) -> dict:
    return {
        "simulation": {"mode": mode},
        "execution": {"max_spread_bps": 1000, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit",
                      "price_chase_gate": {"enabled": False},
                      "halt_gate": {"enabled": True,
                                    "block_on_halt_or_pending_review": True}},
        "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000,
                   "sizing_mode": "fixed_dollar", "max_concurrent_positions": 50},
        "risk": {"max_total_entries_per_day": 99, "max_gross_exposure_pct": 0.99,
                 "daily_loss_pct": 0.99, "max_stopouts_per_day": 99,
                 "stop_trading_after_consecutive_stopouts": 99,
                 "max_lots_per_symbol": 5},
        "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 30},
        "scanner": {"min_signal_strength": 0.0},
        "backtest": {"cost_stress": "base"},
    }


def _none_supplier(symbol, ts):
    return None


def test_intended_realism_rejects_when_halt_data_absent() -> None:
    """``intended_realism`` + no status data → reject ``halt_data_unavailable``."""
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(
        portfolio=p, broker=SimulatedBroker(), cfg=_cfg("intended_realism"),
    )
    res = consumer.consume(
        _candidate(),
        decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=_quote(),
        status_supplier=_none_supplier,
    )
    rejects = [d for d in res.decisions if d.get("decision") == "rejected"]
    assert len(rejects) >= 1
    assert rejects[0]["reason"] == "halt_data_unavailable"
    assert len(res.new_positions) == 0


def test_current_code_parity_fails_open_when_halt_data_absent() -> None:
    """``current_code_parity`` + no status data → fails open (no reject)."""
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(
        portfolio=p, broker=SimulatedBroker(), cfg=_cfg("current_code_parity"),
    )
    res = consumer.consume(
        _candidate(),
        decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=_quote(),
        status_supplier=_none_supplier,
    )
    # Fail-open: no halt_data_unavailable / halt_or_pending_review reject.
    halt_rejects = [
        d for d in res.decisions
        if d.get("reason") in ("halt_data_unavailable", "halt_or_pending_review")
    ]
    assert len(halt_rejects) == 0
