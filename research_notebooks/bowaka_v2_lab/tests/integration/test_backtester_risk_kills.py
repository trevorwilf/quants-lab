"""daily_loss_pct breach mid-session → kill_switch_state set; no more entries."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.sim.portfolio import Portfolio, Position
from bowaka_v2_lab.sim.risk_gates import evaluate_risk_gates


def test_daily_loss_breach_kills_kill_switch() -> None:
    p = Portfolio(initial_bankroll=10_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    # Pre-load a realized loss of 3% (> 2% daily_loss_pct cap).
    p.state.daily_realized_pnl = -300.0
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.02,
                   "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=500,
    )
    assert not gate.accepted
    assert gate.reject_reason == "kill_switch"
    assert p.state.kill_switch_state == "daily_loss"


def test_kill_switch_set_persists_for_subsequent_gates() -> None:
    p = Portfolio(initial_bankroll=10_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.state.kill_switch_state = "daily_loss"
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                   "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=500,
    )
    assert not gate.accepted
    assert gate.reject_reason == "kill_switch"


def test_gross_exposure_cap_blocks_oversize_entry() -> None:
    p = Portfolio(initial_bankroll=10_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.add_position(Position(symbol="OLD", entry_date=_dt.date(2024, 9, 4),
                              entry_price=100.0, qty=40,   # 4k exposure
                              stop_pct=0.02, target_pct=0.05, max_hold_days=5,
                              current_price=100.0))
    # max_gross_exposure_pct=0.5 means cap = 5000; old uses 4000, new attempt of 2000 → 6000 > 5000.
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.5, "daily_loss_pct": 0.5,
                   "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=2000,
    )
    assert not gate.accepted
    assert gate.reject_reason == "gross_exposure_cap"
