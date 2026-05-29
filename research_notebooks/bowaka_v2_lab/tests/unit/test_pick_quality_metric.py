"""Per-pick quality: build_summary computes it; the objective penalizes duds.

Operator goal (2026-05-28): each pick should make a minimum of 0.5% profit,
ideally above 4%. The objective now penalizes the fraction of trades that
fail the 0.5% bar (``pick_quality``), with ``net_return`` still primary.
"""
from __future__ import annotations

import math

from bowaka_v2_lab.sim.metrics import (
    PICK_QUALITY_MIN_PCT, PICK_QUALITY_STRETCH_PCT, build_summary,
)
from bowaka_v2_lab.optuna.objective import (
    DEFAULT_PENALTY_WEIGHTS, FoldResult, compute_objective, fold_penalties,
)


def _trade(pnl: float, entry_price: float = 100.0, qty: int = 10) -> dict:
    return {"symbol": "AAA", "pnl": pnl, "entry_price": entry_price, "qty": qty}


def _summary(trades: list[dict]) -> dict:
    return build_summary(
        trades=trades, candidate_events_count=len(trades),
        entry_decisions_count=len(trades), accepted_count=len(trades),
        rejected_count=0, broker_reject_count=0,
        initial_bankroll=100_000.0,
        final_bankroll=100_000.0 + sum(t["pnl"] for t in trades),
        ambiguous_bar_count=0, cost_stress="base", feed="iex", run_id="t",
    )


# --- build_summary computes the per-pick metrics -------------------------

def test_summary_frac_ge_min_all_clear() -> None:
    # qty*entry = 1000; pnl 10 -> 1% return (>= 0.5%); pnl 50 -> 5% (>= 4%).
    s = _summary([_trade(10.0), _trade(50.0), _trade(20.0)])
    assert s["frac_trades_ge_min_profit"] == 1.0
    # only the 5% trade clears the 4% stretch bar.
    assert math.isclose(s["frac_trades_ge_stretch_profit"], 1 / 3)


def test_summary_frac_ge_min_with_duds() -> None:
    # 1% (pass), -2% loss (dud), +0.3% (dud, below 0.5%), +6% (pass).
    s = _summary([_trade(10.0), _trade(-20.0), _trade(3.0), _trade(60.0)])
    assert math.isclose(s["frac_trades_ge_min_profit"], 0.5)  # 2 of 4 clear 0.5%
    assert math.isclose(s["frac_trades_ge_stretch_profit"], 0.25)  # only +6%


def test_summary_zero_trades_is_neutral() -> None:
    s = _summary([])
    assert s["frac_trades_ge_min_profit"] == 1.0  # neutral, low_trade handles it
    assert s["frac_trades_ge_stretch_profit"] == 0.0


def test_thresholds_exported() -> None:
    assert PICK_QUALITY_MIN_PCT == 0.005
    assert PICK_QUALITY_STRETCH_PCT == 0.04


# --- objective penalizes the dud fraction --------------------------------

def _fold(frac_ge_min: float, *, n_trades: int = 50) -> FoldResult:
    return FoldResult(
        fold_id="f0", net_return=0.05, max_drawdown=0.0, turnover=0.0,
        concentration=0.0, n_trades=n_trades, worst_day_loss=0.0,
        quote_coverage=1.0, fill_rate=1.0,
        frac_trades_ge_min_profit=frac_ge_min,
    )


def test_all_picks_clear_min_no_penalty() -> None:
    pen = fold_penalties(_fold(1.0))
    assert pen["pick_quality"] == 0.0


def test_half_duds_partial_penalty() -> None:
    pen = fold_penalties(_fold(0.5))
    assert math.isclose(
        pen["pick_quality"], DEFAULT_PENALTY_WEIGHTS.pick_quality * 0.5
    )


def test_all_duds_max_penalty() -> None:
    pen = fold_penalties(_fold(0.0))
    assert math.isclose(pen["pick_quality"], DEFAULT_PENALTY_WEIGHTS.pick_quality)


def test_penalty_monotonic_in_dud_fraction() -> None:
    p_clean = fold_penalties(_fold(0.9))["pick_quality"]
    p_mid = fold_penalties(_fold(0.5))["pick_quality"]
    p_bad = fold_penalties(_fold(0.1))["pick_quality"]
    assert p_clean < p_mid < p_bad


def test_net_return_stays_primary() -> None:
    """A high-PnL config with some duds still beats a low-PnL all-clean one —
    net_return remains the dominant driver at the default weight."""
    high_pnl_some_duds = FoldResult(
        fold_id="f0", net_return=0.08, max_drawdown=0.0, turnover=0.0,
        concentration=0.0, n_trades=50, worst_day_loss=0.0,
        quote_coverage=1.0, fill_rate=1.0, frac_trades_ge_min_profit=0.6,
    )
    low_pnl_all_clean = FoldResult(
        fold_id="f0", net_return=0.02, max_drawdown=0.0, turnover=0.0,
        concentration=0.0, n_trades=50, worst_day_loss=0.0,
        quote_coverage=1.0, fill_rate=1.0, frac_trades_ge_min_profit=1.0,
    )
    o_high = compute_objective([high_pnl_some_duds]).objective
    o_low = compute_objective([low_pnl_all_clean]).objective
    assert o_high > o_low


def test_stub_fold_without_field_is_penalty_free() -> None:
    """fold_penalties on an object lacking the field defaults to no penalty."""
    from types import SimpleNamespace
    stub = SimpleNamespace(
        net_return=0.05, max_drawdown=0.0, worst_day_loss=0.0, turnover=0.0,
        concentration=0.0, n_trades=50, missing_quote_count=0,
        quote_coverage=1.0, fill_rate=1.0,
    )
    pen = fold_penalties(stub)
    assert pen["pick_quality"] == 0.0
