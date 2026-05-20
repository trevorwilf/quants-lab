"""Stop+target both touch in the same minute → stop_first by default; logged."""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.sim.ambiguity import resolve_same_bar
from bowaka_v2_lab.sim.exits import ExitEvent, evaluate_exits
from bowaka_v2_lab.sim.portfolio import Position


def test_default_policy_is_stop_first() -> None:
    assert resolve_same_bar() == "stop"
    assert resolve_same_bar("stop_first") == "stop"
    assert resolve_same_bar("target_first") == "target"


def test_unknown_policy_rejected() -> None:
    with pytest.raises(ValueError, match="unknown same-bar policy"):
        resolve_same_bar("flip_a_coin")


def test_same_bar_stop_first_resolves_to_stop() -> None:
    pos = Position(symbol="AAA", entry_date=_dt.date(2024, 9, 4),
                    entry_price=100.0, qty=10,
                    stop_pct=0.02, target_pct=0.05, max_hold_days=5)
    # Bar with low=97 (stop=98 hit) AND high=106 (target=105 hit).
    bar = {"high": 106, "low": 97, "close": 100}
    ev = evaluate_exits(pos, bar=bar, bar_date=_dt.date(2024, 9, 4),
                          exit_cfg={}, same_bar_policy="stop_first")
    assert ev is not None
    assert ev.exit_reason == "stop_loss"
    assert ev.ambiguous_bar_resolved is True
    assert ev.exit_price == pytest.approx(98.0)


def test_same_bar_target_first_resolves_to_target() -> None:
    pos = Position(symbol="AAA", entry_date=_dt.date(2024, 9, 4),
                    entry_price=100.0, qty=10,
                    stop_pct=0.02, target_pct=0.05, max_hold_days=5)
    bar = {"high": 106, "low": 97, "close": 100}
    ev = evaluate_exits(pos, bar=bar, bar_date=_dt.date(2024, 9, 4),
                          exit_cfg={}, same_bar_policy="target_first")
    assert ev.exit_reason == "take_profit"
    assert ev.ambiguous_bar_resolved is True
