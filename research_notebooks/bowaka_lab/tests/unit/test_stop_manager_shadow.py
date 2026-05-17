"""Phase 5: stop-manager shadow models."""

from __future__ import annotations

import pytest

from bowaka_lab.sim.stop_manager import (
    BreakevenAfter5PctStopManager,
    MfeLadderStopManager,
    NoOpStopManager,
    get_stop_manager,
    list_stop_managers,
)


def test_noop_never_updates():
    sm = NoOpStopManager()
    assert sm.maybe_update(entry_price=10, current_stop=9.2, mfe_pct=0.10) is None


def test_breakeven_triggers_at_5pct():
    sm = BreakevenAfter5PctStopManager()
    up = sm.maybe_update(entry_price=10, current_stop=9.2, mfe_pct=0.05)
    assert up is not None
    assert up.new_stop_price == 10.0
    assert up.reason == "breakeven_after_5pct"


def test_breakeven_no_update_when_already_above_be():
    sm = BreakevenAfter5PctStopManager()
    up = sm.maybe_update(entry_price=10, current_stop=10.5, mfe_pct=0.10)
    assert up is None


def test_breakeven_no_update_below_trigger():
    sm = BreakevenAfter5PctStopManager()
    assert sm.maybe_update(entry_price=10, current_stop=9.2, mfe_pct=0.03) is None


def test_mfe_ladder_transitions():
    sm = MfeLadderStopManager()
    # MFE 5% → stop at entry (0%)
    up = sm.maybe_update(entry_price=10, current_stop=9.2, mfe_pct=0.05)
    assert up is not None
    assert up.new_stop_price == pytest.approx(10.0)
    # MFE 8% → stop at +3%
    up = sm.maybe_update(entry_price=10, current_stop=10.0, mfe_pct=0.08)
    assert up is not None
    assert up.new_stop_price == pytest.approx(10.30)
    # MFE 12% → stop at +6%
    up = sm.maybe_update(entry_price=10, current_stop=10.30, mfe_pct=0.12)
    assert up is not None
    assert up.new_stop_price == pytest.approx(10.60)


def test_mfe_ladder_no_downgrade():
    sm = MfeLadderStopManager()
    # Already at +6% stop; MFE drops to 5% (ladder rung would be 0%) — do not lower.
    up = sm.maybe_update(entry_price=10, current_stop=10.60, mfe_pct=0.05)
    assert up is None


def test_registry_lookup():
    assert isinstance(get_stop_manager("none"), NoOpStopManager)
    assert isinstance(get_stop_manager("breakeven_after_5pct"), BreakevenAfter5PctStopManager)
    assert isinstance(get_stop_manager("mfe_ladder_v1"), MfeLadderStopManager)


def test_registry_lookup_unknown_raises():
    with pytest.raises(ValueError):
        get_stop_manager("bogus")


def test_list_stop_managers_contains_built_ins():
    names = list_stop_managers()
    assert "none" in names
    assert "mfe_ladder_v1" in names
