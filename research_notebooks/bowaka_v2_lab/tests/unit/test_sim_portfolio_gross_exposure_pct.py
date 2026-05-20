"""gross_exposure_pct = dollars / bankroll. Regression for [Report §15.2 P1]."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.portfolio import Portfolio, Position


def test_gross_exposure_pct_computed_not_zero() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.add_position(Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4),
        entry_price=100.0, qty=200,  # 20k notional out of 100k
        stop_pct=0.02, target_pct=0.05, max_hold_days=5,
        current_price=100.0,
    ))
    assert p.state.gross_exposure_dollars == 20_000.0
    assert abs(p.state.gross_exposure_pct - 0.20) < 1e-9
