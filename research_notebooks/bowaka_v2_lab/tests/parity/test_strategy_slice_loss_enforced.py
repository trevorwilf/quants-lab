"""Realism Phase 5 — `strategy_slice_loss_pct` kill switch is enforced.

At `strategy_slice_loss_pct: 0.025`, a slice loss of 0.026 of bankroll trips
the kill switch: the gate rejects with the canonical `kill_switch` reason and
`portfolio.state.kill_switch_state` becomes `"strategy_loss"`.

See `docs/current_code_vs_intended_realism.md` §6 — this is an additive
intended-realism extension; the live `_risk_gates` enforces only
`daily_loss_pct`. Enforced against `bankroll * strategy_slice_loss_pct`.
"""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.portfolio import Portfolio
from bowaka_v2_lab.sim.risk_gates import evaluate_risk_gates

# Permissive on every other control so only the slice-loss gate can fire.
_RISK_BASE = {
    "max_concurrent_positions": 99, "max_total_entries_per_day": 99,
    "max_gross_exposure_pct": 0.99,
    "daily_loss_pct": 0.99,  # well above the slice loss — must not pre-empt
    "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99,
}
_SIZING = {"max_concurrent_positions": 99}


def test_slice_loss_over_threshold_trips_kill_switch() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    # Realized loss of 2.6% of bankroll: -2,600 on 100,000.
    p.state.daily_realized_pnl = -2_600.0

    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={**_RISK_BASE, "strategy_slice_loss_pct": 0.025},
        sizing_cfg=_SIZING, candidate_adv=5_000_000, target_notional=500,
        symbol="AAA",
    )
    assert gate.accepted is False
    assert gate.reject_reason == "kill_switch"
    assert p.state.kill_switch_state == "strategy_loss"


def test_slice_loss_under_threshold_does_not_trip() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    # Realized loss of 2.4% — under the 2.5% slice cap.
    p.state.daily_realized_pnl = -2_400.0

    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={**_RISK_BASE, "strategy_slice_loss_pct": 0.025},
        sizing_cfg=_SIZING, candidate_adv=5_000_000, target_notional=500,
        symbol="AAA",
    )
    assert gate.accepted is True
    assert p.state.kill_switch_state is None


def test_slice_loss_counts_unrealized_pnl_too() -> None:
    # The gate uses total PnL = realized + unrealized.
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.state.daily_realized_pnl = -1_000.0
    p.state.daily_unrealized_pnl = -1_700.0  # total -2,700 = 2.7%

    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={**_RISK_BASE, "strategy_slice_loss_pct": 0.025},
        sizing_cfg=_SIZING, candidate_adv=5_000_000, target_notional=500,
        symbol="AAA",
    )
    assert gate.accepted is False
    assert p.state.kill_switch_state == "strategy_loss"


def test_no_slice_gate_when_key_absent() -> None:
    # Parity: omitting strategy_slice_loss_pct reproduces the live single-gate
    # behavior — a 2.6% loss with daily_loss_pct=0.99 passes.
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.state.daily_realized_pnl = -2_600.0

    gate = evaluate_risk_gates(
        portfolio=p, risk_cfg=dict(_RISK_BASE),  # no strategy_slice_loss_pct
        sizing_cfg=_SIZING, candidate_adv=5_000_000, target_notional=500,
        symbol="AAA",
    )
    assert gate.accepted is True
