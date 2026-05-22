"""Realism Phase 5 parity — `max_concurrent_positions` is read from `sizing`.

Live `bowaka_v2_strategy.py:444-446` (`_risk_gates`):

    max_concurrent = int(sizing_cfg.get("max_concurrent_positions", 18))

i.e. the cap comes from the SIZING config, not the RISK config.
`risk.max_concurrent_positions` is honored only as a legacy fallback when
`sizing` omits the key.
"""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.sim.portfolio import Portfolio, Position
from bowaka_v2_lab.sim.risk_gates import evaluate_risk_gates


def _fill(p: Portfolio, n: int) -> None:
    """Open ``n`` lots so the next candidate sees ``n`` open positions."""
    for i in range(n):
        p.add_position(Position(
            symbol=f"S{i}", entry_date=_dt.date(2024, 9, 4), entry_price=100.0,
            qty=1, stop_pct=0.02, target_pct=0.05, max_hold_days=30,
            current_price=100.0, entry_session=_dt.date(2024, 9, 4),
        ))


_RISK_PERMISSIVE = {
    "max_total_entries_per_day": 99, "max_gross_exposure_pct": 0.99,
    "daily_loss_pct": 0.99, "max_stopouts_per_day": 99,
    "stop_trading_after_consecutive_stopouts": 99,
}


def test_max_concurrent_read_from_sizing_config() -> None:
    # sizing caps at 3; with 3 lots open the next candidate is rejected.
    p = Portfolio(initial_bankroll=10_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    _fill(p, 3)
    gate = evaluate_risk_gates(
        portfolio=p, risk_cfg=_RISK_PERMISSIVE,
        sizing_cfg={"max_concurrent_positions": 3},
        candidate_adv=5_000_000, target_notional=1000, symbol="NEW",
    )
    assert gate.accepted is False
    assert gate.reject_reason == "max_concurrent_positions"


def test_sizing_value_overrides_risk_value() -> None:
    # risk says 2, sizing says 10. The live code uses sizing -> 10.
    # With 3 lots open the candidate must still be ACCEPTED (3 < 10), proving
    # the sizing value, not the stricter risk value, governs.
    p = Portfolio(initial_bankroll=10_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    _fill(p, 3)
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={**_RISK_PERMISSIVE, "max_concurrent_positions": 2},
        sizing_cfg={"max_concurrent_positions": 10},
        candidate_adv=5_000_000, target_notional=1000, symbol="NEW",
    )
    assert gate.accepted is True


def test_risk_value_used_only_as_fallback_when_sizing_omits_key() -> None:
    # sizing omits the key -> fall back to risk.max_concurrent_positions (3).
    p = Portfolio(initial_bankroll=10_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    _fill(p, 3)
    gate = evaluate_risk_gates(
        portfolio=p,
        risk_cfg={**_RISK_PERMISSIVE, "max_concurrent_positions": 3},
        sizing_cfg={},  # no max_concurrent_positions here
        candidate_adv=5_000_000, target_notional=1000, symbol="NEW",
    )
    assert gate.accepted is False
    assert gate.reject_reason == "max_concurrent_positions"
