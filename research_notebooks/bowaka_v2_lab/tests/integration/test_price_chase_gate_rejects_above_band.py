"""Audit P0-009: price-chase gate rejects when mid is too far ABOVE the signal price.

The gate refuses to chase a runaway quote. With ``max_pct_above_signal_price``
defaulting to ``+0.10`` (audit), a quote mid of 11.5 on a signal of 10.0 is 15%
above and must reject with ``price_chase_band`` BEFORE the risk gates run.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def _candidate(signal_price: float) -> dict:
    return {
        "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-04",
        "scan_timestamp": "2024-09-04T13:30:00Z",
        "forming_session_bar": {"last_price": signal_price, "session_high": 11.0, "session_low": 9.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }


def _cfg(*, mode: str = "current_code_parity") -> dict:
    return {
        "simulation": {"mode": mode},
        "execution": {"max_spread_bps": 1000, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit",
                      # Defaults match the actual contract.
                      "price_chase_gate": {"enabled": True,
                                            "max_pct_above_signal_price": 0.10,
                                            "min_pct_below_signal_price": -0.03},
                      "halt_gate": {"enabled": False}},
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


def test_price_chase_gate_rejects_above_band() -> None:
    """Signal 10.0, quote mid 11.5 (15% above) → reject ``price_chase_band``."""
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())
    quote = {
        "bid": 11.49, "ask": 11.51, "mid": 11.5, "spread_pct": 0.001,
        "bid_size": 5000, "ask_size": 5000,
        "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 0.5,
        "source": "historical",
    }
    res = consumer.consume(
        _candidate(signal_price=10.0),
        decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=quote,
    )
    rejects = [d for d in res.decisions if d.get("decision") == "rejected"]
    assert len(rejects) >= 1, (
        f"expected price_chase_band reject, got: {[d.get('reason') for d in res.decisions]}"
    )
    assert rejects[0]["reason"] == "price_chase_band"
    assert len(res.new_positions) == 0
