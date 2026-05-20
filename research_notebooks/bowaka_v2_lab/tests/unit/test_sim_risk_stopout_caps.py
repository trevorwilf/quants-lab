"""Third stop in a row → no new entries; max_stopouts_per_day enforced."""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.portfolio import Portfolio, Position
from bowaka_v2_lab.sim.risk_gates import evaluate_risk_gates


def _close_at_loss(p: Portfolio, sym: str, *, date: _dt.date) -> None:
    p.add_position(Position(symbol=sym, entry_date=date, entry_price=100.0, qty=10,
                              stop_pct=0.02, target_pct=0.05, max_hold_days=5,
                              current_price=100.0))
    p.close_position(sym, exit_price=98.0, exit_reason="stop_loss", exit_date=date)


def test_third_consecutive_stopout_kills_new_entries() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    _close_at_loss(p, "S1", date=_dt.date(2024, 9, 4))
    _close_at_loss(p, "S2", date=_dt.date(2024, 9, 4))
    _close_at_loss(p, "S3", date=_dt.date(2024, 9, 4))
    assert p.state.consecutive_stopouts == 3
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={"max_stopouts_per_day": 10,
                   "stop_trading_after_consecutive_stopouts": 3,
                   "max_concurrent_positions": 5,
                   "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.5,
                   "daily_loss_pct": 0.50},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=1000,
    )
    assert not gate.accepted
    assert gate.reject_reason == "kill_switch"


def test_max_stopouts_per_day_enforced() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    # Wins after each stopout reset consecutive counter but stopouts_today still increments.
    for i, sym in enumerate(["S1", "S2", "S3", "S4"]):
        p.add_position(Position(symbol=sym, entry_date=_dt.date(2024, 9, 4),
                                  entry_price=100.0, qty=10,
                                  stop_pct=0.02, target_pct=0.05, max_hold_days=5,
                                  current_price=100.0))
        p.close_position(sym, exit_price=98.0, exit_reason="stop_loss", exit_date=_dt.date(2024, 9, 4))
    assert p.state.stopouts_today == 4
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={"max_stopouts_per_day": 4,
                   "stop_trading_after_consecutive_stopouts": 99,
                   "max_concurrent_positions": 5,
                   "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.5,
                   "daily_loss_pct": 0.50},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=1000,
    )
    assert not gate.accepted
