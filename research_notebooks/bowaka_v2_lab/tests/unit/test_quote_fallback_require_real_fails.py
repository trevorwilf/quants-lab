"""Phase 6 — realism mode + no historical quote → candidate rejected (missing_quote).

The ``require_real`` fallback policy (resolved from ``intended_realism`` mode)
synthesizes no quote: when the lake has no historical quote the candidate is
rejected with the canonical reason ``missing_quote`` and the consumer's
``missing_quote_count`` is incremented.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.quote_model import resolve_quote
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def test_require_real_resolves_to_missing_quote():
    res = resolve_quote(
        symbol="AAA", at=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        signal_price=100.0,
        historical_quote=None,
        quote_fallback_policy="require_real",
    )
    assert res.missing_quote is True
    assert res.quote is None


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
        # intended_realism resolves quote_fallback_policy -> require_real.
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


def test_consumer_rejects_candidate_with_missing_quote_in_realism():
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())

    # No historical quote supplied — require_real → reject.
    res = consumer.consume(
        _candidate(), decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=None,
    )
    assert res.missing_quote_count == 1
    assert len(res.decisions) == 1
    assert res.decisions[0]["decision"] == "rejected"
    assert res.decisions[0]["reason"] == "missing_quote"
    # No position created.
    assert len(res.new_positions) == 0
    assert len(p.open_positions) == 0


def test_consumer_accepts_when_historical_quote_present_in_realism():
    """With a real historical quote the realism candidate is NOT rejected."""
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())
    historical = {
        "bid": 99.99, "ask": 100.01, "mid": 100.0, "spread_pct": 0.0002,
        "bid_size": 5000, "ask_size": 5000,
        "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 0.5,
        "source": "historical",
    }
    res = consumer.consume(
        _candidate(), decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=historical,
    )
    assert res.missing_quote_count == 0
    assert not any(d["reason"] == "missing_quote" for d in res.decisions)
