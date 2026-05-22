"""Realism Phase 5 — a symbol may hold several concurrent lots.

Opening the same symbol on three consecutive sessions leaves all three lots
co-existing (open_positions is keyed by position_id, not symbol).
"""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.portfolio import Portfolio, Position


def _lot(symbol: str, *, session: _dt.date, price: float) -> Position:
    return Position(
        symbol=symbol, entry_date=session, entry_price=price, qty=10,
        stop_pct=0.02, target_pct=0.05, max_hold_days=20,
        current_price=price, entry_session=session,
    )


def test_three_lots_same_symbol_coexist() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5), _dt.date(2024, 9, 6)]
    for i, sess in enumerate(sessions):
        p.begin_session(sess)
        p.add_position(_lot("AAA", session=sess, price=100.0 + i))

    # All three lots co-exist under distinct position_id keys.
    assert len(p.open_positions) == 3
    assert p.lots_for_symbol("AAA") == 3
    assert len({k for k in p.open_positions}) == 3  # all keys distinct
    assert all(pos.symbol == "AAA" for pos in p.open_positions.values())


def test_lot_index_increments_per_lot() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5), _dt.date(2024, 9, 6)]
    for sess in sessions:
        p.begin_session(sess)
        p.add_position(_lot("AAA", session=sess, price=100.0))
    assert sorted(pos.lot_index for pos in p.positions_for_symbol("AAA")) == [0, 1, 2]


def test_open_positions_keyed_by_position_id() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    lot = _lot("AAA", session=_dt.date(2024, 9, 4), price=100.0)
    p.add_position(lot)
    # The dict key is the lot's position_id (a UUID string), not the symbol.
    assert lot.position_id in p.open_positions
    assert "AAA" not in p.open_positions
    assert p.open_positions[lot.position_id] is lot


def test_multi_lot_gross_exposure_sums_all_lots() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5), _dt.date(2024, 9, 6)]
    for sess in sessions:
        p.begin_session(sess)
        p.add_position(_lot("AAA", session=sess, price=100.0))  # 10 * 100 each
    # begin_session on session 3 recomputed gross from the 2 prior lots; the
    # 3rd add_position adds the third. 3 lots * 1000 = 3000.
    assert p.state.gross_exposure_dollars == 3_000.0
