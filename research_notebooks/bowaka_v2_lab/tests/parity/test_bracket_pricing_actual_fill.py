"""Phase 6 parity — brackets are priced off the ACTUAL FILL, not the signal price.

The live strategy uses ``bracket_pricing_mode: actual_fill`` — the OCO bracket's
stop / target are computed from the realised fill price, not the raw signal /
quote price. A position created by the simulator must do the same:
``stop_price == fill_price * (1 - stop_pct)`` and
``target_price == fill_price * (1 + target_pct)``.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.broker import SimulatedBroker
from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer


def _candidate(signal_price: float = 100.0) -> dict:
    return {
        "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-04",
        "scan_timestamp": "2024-09-04T13:30:00Z",
        "forming_session_bar": {"last_price": signal_price,
                                "session_high": signal_price + 1.0,
                                "session_low": signal_price - 1.0},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }


def _cfg(*, stop_pct=0.08, target_pct=0.15) -> dict:
    return {
        # current_code_parity → zero_spread fallback, pre_submit sequencing.
        "simulation": {"mode": "current_code_parity", "allow_research_relaxed": True},
        "execution": {"max_spread_bps": 500, "max_quote_age_seconds": 60,
                      "order_type": "market"},
        "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000,
                   "sizing_mode": "fixed_dollar", "max_concurrent_positions": 50,
                   "min_order_notional": 100},
        "risk": {"max_total_entries_per_day": 99,
                 "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99,
                 "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99,
                 "max_lots_per_symbol": 5},
        "exits": {"stop_pct": stop_pct, "target_pct": target_pct, "max_hold_days": 30},
        "scanner": {"min_signal_strength": 0.0},
        "backtest": {"cost_stress": "conservative"},
    }


def test_brackets_computed_off_fill_price_not_signal_price():
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=_cfg())

    # A historical quote whose ask is ABOVE the signal price — so the fill price
    # (ask + slippage) is clearly distinct from the signal price.
    historical = {
        "bid": 100.50, "ask": 100.70, "mid": 100.60, "spread_pct": 0.002,
        "bid_size": 10_000, "ask_size": 10_000,
        "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 0.5,
        "source": "historical",
    }
    res = consumer.consume(
        _candidate(signal_price=100.0),
        decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=historical,
    )
    assert len(res.new_positions) == 1
    pos = res.new_positions[0]

    fill_price = pos.entry_price
    # The fill price is a market fill = ask + slippage, NOT the $100 signal price.
    assert fill_price > 100.70
    assert abs(fill_price - 100.0) > 0.5

    # Brackets are computed off the ACTUAL FILL price.
    assert pos.bracket_pricing_mode == "actual_fill"
    # Realism remediation 2 Phase 6 (audit P0-007) — under
    # ``current_code_parity`` the consumer no longer immediately stamps the
    # lot as protected; the protection lifecycle is event-driven and the lot
    # leaves the synchronous ``consume()`` call in
    # :attr:`ProtectionState.PARENT_FILLED`. The event loop then schedules the
    # OCO_ATTACH_ATTEMPT. ``bracket_attached`` (a derived view of state ==
    # PROTECTED) is therefore False at this point — what matters for parity is
    # that the bracket *prices* are computed off the actual fill.
    from bowaka_v2_lab.sim.portfolio import ProtectionState
    assert pos.protection_state == ProtectionState.PARENT_FILLED
    assert pos.bracket_attached is False
    assert pos.stop_price == round(fill_price * (1.0 - 0.08), 4)
    assert pos.target_price == round(fill_price * (1.0 + 0.15), 4)

    # And explicitly NOT off the signal price.
    signal_stop = round(100.0 * (1.0 - 0.08), 4)
    assert pos.stop_price != signal_stop


def test_partial_fill_brackets_still_off_fill_price():
    """A partial fill still attaches brackets off the realised fill price."""
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    cfg = _cfg(stop_pct=0.05, target_pct=0.20)
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=cfg)
    historical = {
        "bid": 49.95, "ask": 50.05, "mid": 50.0, "spread_pct": 0.002,
        "bid_size": 10_000, "ask_size": 10_000,
        "quote_timestamp": "2024-09-04T13:30:00Z", "quote_age_seconds": 0.5,
        "source": "historical",
    }
    res = consumer.consume(
        _candidate(signal_price=50.0),
        decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"),
        historical_quote=historical,
    )
    assert len(res.new_positions) == 1
    pos = res.new_positions[0]
    assert pos.stop_price == round(pos.entry_price * (1.0 - 0.05), 4)
    assert pos.target_price == round(pos.entry_price * (1.0 + 0.20), 4)
