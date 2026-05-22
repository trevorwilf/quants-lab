"""Realism Phase 5 — closing one lot leaves a symbol's other lots open.

`close_position_by_id` closes exactly the named lot. The back-compat
`close_position(symbol, ...)` closes the OLDEST lot of the symbol.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.sim.portfolio import Portfolio, Position


def _lot(symbol: str, *, session: _dt.date, price: float, qty: int = 10) -> Position:
    return Position(
        symbol=symbol, entry_date=session, entry_price=price, qty=qty,
        stop_pct=0.02, target_pct=0.05, max_hold_days=30,
        current_price=price, entry_session=session,
    )


def _portfolio_with_three_lots() -> tuple[Portfolio, list[Position]]:
    p = Portfolio(initial_bankroll=1_000_000.0)
    lots = []
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5), _dt.date(2024, 9, 6)]
    for i, sess in enumerate(sessions):
        p.begin_session(sess)
        lot = _lot("AAA", session=sess, price=100.0 + i)
        p.add_position(lot)
        lots.append(lot)
    return p, lots


def test_close_one_lot_by_id_leaves_others_open() -> None:
    p, lots = _portfolio_with_three_lots()
    assert p.lots_for_symbol("AAA") == 3

    middle = lots[1]
    trade = p.close_position_by_id(
        middle.position_id, exit_price=120.0,
        exit_reason="take_profit", exit_date=_dt.date(2024, 9, 10),
    )
    assert trade["position_id"] == middle.position_id
    assert trade["symbol"] == "AAA"

    # The other two lots remain open; the closed one is gone.
    assert p.lots_for_symbol("AAA") == 2
    remaining_ids = {pos.position_id for pos in p.positions_for_symbol("AAA")}
    assert middle.position_id not in remaining_ids
    assert remaining_ids == {lots[0].position_id, lots[2].position_id}


def test_close_position_by_id_records_pnl() -> None:
    p, lots = _portfolio_with_three_lots()
    bankroll_before = p.state.bankroll
    # Lot 0: entry 100.0, qty 10. Exit at 105.0 → +50 realized PnL.
    p.close_position_by_id(
        lots[0].position_id, exit_price=105.0,
        exit_reason="take_profit", exit_date=_dt.date(2024, 9, 10),
    )
    assert p.state.bankroll == pytest.approx(bankroll_before + 50.0)
    assert len(p.closed_trades) == 1


def test_back_compat_close_position_closes_oldest_lot() -> None:
    p, lots = _portfolio_with_three_lots()
    # lots[0] is the oldest (lot_index 0). close_position(symbol) closes it.
    trade = p.close_position(
        "AAA", exit_price=110.0, exit_reason="time_stop",
        exit_date=_dt.date(2024, 9, 10),
    )
    assert trade["position_id"] == lots[0].position_id
    assert p.lots_for_symbol("AAA") == 2
    assert lots[0].position_id not in p.open_positions


def test_close_position_by_id_unknown_id_raises() -> None:
    p, _ = _portfolio_with_three_lots()
    with pytest.raises(KeyError):
        p.close_position_by_id(
            "no-such-id", exit_price=100.0,
            exit_reason="time_stop", exit_date=_dt.date(2024, 9, 10),
        )
