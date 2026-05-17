"""Phase 4: §F.2 same-bar stop+target → ambiguity policy applies."""

from __future__ import annotations

from bowaka_lab.sim.ambiguity import resolve


def test_stop_first_default_when_both_hit():
    res = resolve(bar_high=11.70, bar_low=9.10, stop_price=9.20, target_price=11.50, policy="stop_first")
    assert res.outcome == "stop"
    assert res.ambiguous_bar


def test_target_first_when_configured():
    res = resolve(bar_high=11.70, bar_low=9.10, stop_price=9.20, target_price=11.50, policy="target_first")
    assert res.outcome == "target"
    assert res.ambiguous_bar


def test_skip_when_configured():
    res = resolve(bar_high=11.70, bar_low=9.10, stop_price=9.20, target_price=11.50, policy="skip")
    assert res.outcome == "none"
    assert res.ambiguous_bar


def test_only_stop_when_target_not_hit():
    res = resolve(bar_high=11.0, bar_low=9.1, stop_price=9.2, target_price=11.5, policy="stop_first")
    assert res.outcome == "stop"
    assert not res.ambiguous_bar


def test_only_target_when_stop_not_hit():
    res = resolve(bar_high=11.7, bar_low=9.5, stop_price=9.2, target_price=11.5, policy="stop_first")
    assert res.outcome == "target"
    assert not res.ambiguous_bar


def test_neither_when_neither_hit():
    res = resolve(bar_high=11.0, bar_low=9.5, stop_price=9.2, target_price=11.5, policy="stop_first")
    assert res.outcome == "none"
    assert not res.ambiguous_bar
