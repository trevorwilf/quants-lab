"""Held overnight positions contribute gross_exposure_dollars next day.

Regression for [Report §15.1 P0]: begin_session must recompute exposure
from open_positions, not assume it.
"""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.portfolio import Portfolio, Position


def test_overnight_position_contributes_next_day_exposure() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.add_position(Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4),
        entry_price=100.0, qty=50,
        stop_pct=0.02, target_pct=0.05, max_hold_days=5,
        current_price=100.0,
    ))
    assert p.state.gross_exposure_dollars == 5000.0
    # End of session, no exit. Next day's begin_session recomputes from open_positions.
    p.end_session(_dt.date(2024, 9, 4))
    p.begin_session(_dt.date(2024, 9, 5))
    # The position should still contribute to exposure.
    assert p.state.gross_exposure_dollars == 5000.0
    assert p.state.entries_today == 0  # counter reset
