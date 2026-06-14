"""P6 §3.6 — net_return_pct units contract: a DECIMAL fraction, not ×100 percent.

``build_summary`` stores ``net_return_pct`` as a decimal (0.15 == +15%) despite the
``_pct`` suffix, and the objective's MetricUnits guard REQUIRES decimal returns. A
future "×100 fix" of the field would either 100×-inflate reports/objective terms or
trip MetricUnitsError. These pin the contract so that mistake fails loudly.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.objective import MetricUnits, MetricUnitsError
from bowaka_v2_lab.sim.metrics import build_summary


def _summary(initial: float, final: float) -> dict:
    return build_summary(
        trades=[], candidate_events_count=0, entry_decisions_count=0,
        accepted_count=0, rejected_count=0, broker_reject_count=0,
        initial_bankroll=initial, final_bankroll=final,
        ambiguous_bar_count=0, cost_stress="base", feed="sip", run_id="t",
    )


def test_net_return_pct_is_decimal_fraction_not_times_100() -> None:
    s = _summary(100_000.0, 115_000.0)           # +15%
    assert s["net_return_pct"] == pytest.approx(0.15)
    assert abs(s["net_return_pct"]) < 1.0        # decimal-scaled, not percent (15.0)
    assert _summary(100_000.0, 92_000.0)["net_return_pct"] == pytest.approx(-0.08)


def test_metricunits_accepts_decimal_rejects_times_100_net_return() -> None:
    base = dict(max_drawdown=0.05, worst_day_loss=0.03, quote_coverage=1.0, fill_rate=0.9)
    MetricUnits.build(net_return=0.15, **base)    # decimal +15% accepted
    # The ×100 "fix" (15.0) is rejected as percent — the guard that makes a future
    # net_return_pct rescale fail LOUDLY rather than silently 100×-inflate.
    with pytest.raises(MetricUnitsError):
        MetricUnits.build(net_return=15.0, **base)


def test_summary_net_return_feeds_metricunits_without_rescale() -> None:
    s = _summary(100_000.0, 103_000.0)           # +3% -> 0.03
    MetricUnits.build(
        net_return=s["net_return_pct"], max_drawdown=0.05, worst_day_loss=0.03,
        quote_coverage=1.0, fill_rate=0.9,
    )
    assert s["net_return_pct"] == pytest.approx(0.03)
