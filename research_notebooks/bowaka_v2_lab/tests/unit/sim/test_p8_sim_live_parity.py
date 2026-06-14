"""P8 — sim<->live parity divergences (L14, L15, daily_loss basis).

The sim modeled exits/risk-caps the LIVE strategy does not have:
- L14: an always-on intraday time-stop (15:30/15:45 force-close) while live holds
  to bracket/max_hold.
- L15: two stopout caps (max_stopouts_per_day, stop_trading_after_consecutive_
  stopouts) firing via hard-coded 4/3 defaults even when a config omits them.
- daily_loss: the kill summed a stale daily_unrealized_pnl; live refuses new
  entries on the daily REALIZED loss only.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.sim.exits import _walk_lot_exit_pandas
from bowaka_v2_lab.sim.portfolio import Portfolio, Position
from bowaka_v2_lab.sim.risk_gates import evaluate_risk_gates

_ET = "America/New_York"
_SD = _dt.date(2024, 9, 4)


# --------------------------------------------------------------------------
# L14 — intraday time-stop suppressed for the live-matching contracts
# --------------------------------------------------------------------------
def _exit_lot() -> Position:
    base = pd.Timestamp("2024-09-04 09:30", tz=_ET).tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=_SD, entry_price=100.0, qty=10,
        stop_pct=0.20, target_pct=0.30, max_hold_days=5,
        entry_session=_SD, entry_timestamp=base.isoformat(),
        stop_price=80.0, target_price=130.0,  # neither bracket hits
    )


def _bars_past_exit_time() -> pd.DataFrame:
    rows = []
    for clk in ("09:31", "15:44", "15:46"):  # 15:46 ET is past the 15:45 time-stop
        ts = pd.Timestamp(f"2024-09-04 {clk}", tz=_ET).tz_convert("UTC")
        rows.append({"symbol": "AAA", "timestamp": ts, "open": 100.0,
                     "high": 100.5, "low": 99.5, "close": 100.0, "volume": 1000.0})
    return pd.DataFrame(rows)


_TS_CFG = {"time_stop": {"enabled": True, "exit_time": "15:45"}, "signal_fade": {}}


def test_l14_time_stop_fires_without_contract_and_under_smoke() -> None:
    # A direct caller (no mode) keeps the engine time-stop — it fires at 15:46.
    ev = _walk_lot_exit_pandas(_exit_lot(), _bars_past_exit_time(), exit_cfg=_TS_CFG)
    assert ev is not None and ev.exit_reason == "time_stop"
    # smoke_fixture also keeps it (deterministic fixture behavior).
    ev_s = _walk_lot_exit_pandas(_exit_lot(), _bars_past_exit_time(), exit_cfg=_TS_CFG,
                                 simulation_mode="smoke_fixture")
    assert ev_s is not None and ev_s.exit_reason == "time_stop"


@pytest.mark.parametrize("mode", ["current_code_parity", "intended_realism", "fast_realism"])
def test_l14_time_stop_suppressed_for_live_matching_contracts(mode: str) -> None:
    # Live has no intraday time-stop -> suppressed; the lot holds (no time_stop exit).
    ev = _walk_lot_exit_pandas(_exit_lot(), _bars_past_exit_time(), exit_cfg=_TS_CFG,
                               simulation_mode=mode)
    assert ev is None or ev.exit_reason != "time_stop"


# --------------------------------------------------------------------------
# L15 — stopout caps gate behind KEY PRESENCE (no hard-coded 4/3 default)
# --------------------------------------------------------------------------
_BASE_RISK = {"max_concurrent_positions": 50, "max_total_entries_per_day": 999,
              "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99}


def _stopout_portfolio(n: int) -> Portfolio:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_SD)
    for i in range(n):
        sym = f"S{i}"
        p.add_position(Position(symbol=sym, entry_date=_SD, entry_price=100.0, qty=10,
                                stop_pct=0.02, target_pct=0.05, max_hold_days=5,
                                current_price=100.0))
        p.close_position(sym, exit_price=98.0, exit_reason="stop_loss", exit_date=_SD)
    return p


def test_l15_omitted_stopout_caps_do_not_gate() -> None:
    # 10 consecutive stopouts, caps OMITTED -> no kill (live has neither cap).
    gate = evaluate_risk_gates(
        portfolio=_stopout_portfolio(10), risk_cfg=dict(_BASE_RISK), sizing_cfg={},
        candidate_adv=5_000_000, target_notional=1000,
    )
    assert gate.accepted, "L15: omitted stopout caps must NOT gate (was a hard-coded 4/3 default)"


def test_l15_present_stopout_cap_still_gates() -> None:
    gate = evaluate_risk_gates(
        portfolio=_stopout_portfolio(5),
        risk_cfg={**_BASE_RISK, "max_stopouts_per_day": 4},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=1000,
    )
    assert not gate.accepted and gate.reject_reason == "kill_switch"


def test_l15_present_consecutive_cap_still_gates() -> None:
    gate = evaluate_risk_gates(
        portfolio=_stopout_portfolio(3),
        risk_cfg={**_BASE_RISK, "stop_trading_after_consecutive_stopouts": 3},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=1000,
    )
    assert not gate.accepted and gate.reject_reason == "kill_switch"


# --------------------------------------------------------------------------
# daily_loss kill uses REALIZED pnl only (not stale unrealized) — §sim_core.md:57
# --------------------------------------------------------------------------
def test_daily_loss_ignores_stale_unrealized_uses_realized() -> None:
    p = Portfolio(initial_bankroll=100_000.0)
    p.begin_session(_SD)
    # A 10% UNREALIZED loss (stale intraday) must NOT trip the kill (live = realized-only).
    p.state.daily_unrealized_pnl = -10_000.0
    p.state.daily_realized_pnl = 0.0
    gate = evaluate_risk_gates(
        portfolio=p, risk_cfg={**_BASE_RISK, "daily_loss_pct": 0.02},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=1000,
    )
    assert gate.accepted, "daily_loss must ignore stale unrealized PnL (live refuses on realized loss)"
    # A REALIZED 10% loss DOES trip it.
    p.state.daily_realized_pnl = -10_000.0
    gate2 = evaluate_risk_gates(
        portfolio=p, risk_cfg={**_BASE_RISK, "daily_loss_pct": 0.02},
        sizing_cfg={}, candidate_adv=5_000_000, target_notional=1000,
    )
    assert not gate2.accepted and gate2.reject_reason == "kill_switch"
