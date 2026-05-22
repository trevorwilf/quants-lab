"""Realism Phase 5 parity — ADV cap binds the AGGREGATE symbol notional.

Matches live `bowaka_v2_strategy.py:474-488` (`_risk_gates`): the ADV-tier cap
is applied to `_symbol_open_notional(state, symbol) + target_notional`, NOT to
the candidate notional alone. Stacking lots across days therefore cannot blow
through the symbol's liquidity limit.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.sim.portfolio import Portfolio, Position
from bowaka_v2_lab.sim.risk_gates import evaluate_risk_gates


def _lot(symbol: str, *, entry_price: float, qty: int) -> Position:
    return Position(
        symbol=symbol, entry_date=_dt.date(2024, 9, 4), entry_price=entry_price,
        qty=qty, stop_pct=0.02, target_pct=0.05, max_hold_days=30,
        current_price=entry_price, entry_session=_dt.date(2024, 9, 4),
    )


# adv * max_position_as_adv_frac is the symbol's aggregate dollar cap.
# adv = 1,000,000 ; frac = 0.05 -> cap = 50,000.
_ADV = 1_000_000.0
_RISK = {
    "max_total_entries_per_day": 99, "max_gross_exposure_pct": 0.99,
    "daily_loss_pct": 0.99, "max_stopouts_per_day": 99,
    "stop_trading_after_consecutive_stopouts": 99,
    "max_position_as_adv_frac": 0.05,  # flat ADV policy (no tiers)
}
_SIZING = {"max_concurrent_positions": 50}


@pytest.mark.parametrize(
    "existing_notional,candidate_notional,expect_accepted",
    [
        # No existing lot — candidate alone under the 50k cap.
        (0.0, 40_000.0, True),
        # No existing lot — candidate alone over the 50k cap.
        (0.0, 60_000.0, False),
        # Existing 30k + candidate 15k = 45k <= 50k -> accepted.
        (30_000.0, 15_000.0, True),
        # Existing 30k + candidate 25k = 55k > 50k -> rejected (aggregate cap).
        (30_000.0, 25_000.0, False),
        # Existing 49k + a tiny 2k candidate = 51k > 50k -> rejected.
        (49_000.0, 2_000.0, False),
    ],
)
def test_adv_cap_binds_aggregate_symbol_notional(
    existing_notional: float, candidate_notional: float, expect_accepted: bool
) -> None:
    p = Portfolio(initial_bankroll=10_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    if existing_notional > 0:
        # One open lot of XYZ carrying `existing_notional` dollars
        # (qty * entry_price). symbol_open_notional uses qty * entry_price.
        p.add_position(_lot("XYZ", entry_price=existing_notional, qty=1))
        assert p.symbol_open_notional("XYZ") == pytest.approx(existing_notional)

    gate = evaluate_risk_gates(
        portfolio=p, risk_cfg=_RISK, sizing_cfg=_SIZING,
        candidate_adv=_ADV, target_notional=candidate_notional, symbol="XYZ",
    )
    assert gate.accepted is expect_accepted
    if not expect_accepted:
        assert gate.reject_reason == "adv_cap"


def test_other_symbol_lots_do_not_count_toward_the_cap() -> None:
    # A large lot in a DIFFERENT symbol must not consume XYZ's ADV budget.
    p = Portfolio(initial_bankroll=10_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.add_position(_lot("OTHER", entry_price=49_000.0, qty=1))  # not XYZ

    gate = evaluate_risk_gates(
        portfolio=p, risk_cfg=_RISK, sizing_cfg=_SIZING,
        candidate_adv=_ADV, target_notional=40_000.0, symbol="XYZ",
    )
    # XYZ has no open lots; 40k candidate alone is under the 50k cap.
    assert gate.accepted is True


def test_tiered_adv_policy_aggregate_cap() -> None:
    # Ordered tier policy: ADV 1M falls in the <=2M tier, frac 0.04 -> cap 40k.
    risk = {
        **{k: v for k, v in _RISK.items() if k != "max_position_as_adv_frac"},
        "adv_tier_caps": [
            {"max_adv_dollars": 2_000_000, "max_position_as_adv_frac": 0.04},
            {"max_adv_dollars": None, "max_position_as_adv_frac": 0.10},
        ],
    }
    p = Portfolio(initial_bankroll=10_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    p.add_position(_lot("XYZ", entry_price=25_000.0, qty=1))  # existing 25k

    # 25k + 20k = 45k > 40k tier cap -> rejected on the aggregate.
    gate = evaluate_risk_gates(
        portfolio=p, risk_cfg=risk, sizing_cfg=_SIZING,
        candidate_adv=_ADV, target_notional=20_000.0, symbol="XYZ",
    )
    assert gate.accepted is False
    assert gate.reject_reason == "adv_cap"

    # 25k + 10k = 35k <= 40k -> accepted.
    gate_ok = evaluate_risk_gates(
        portfolio=p, risk_cfg=risk, sizing_cfg=_SIZING,
        candidate_adv=_ADV, target_notional=10_000.0, symbol="XYZ",
    )
    assert gate_ok.accepted is True
