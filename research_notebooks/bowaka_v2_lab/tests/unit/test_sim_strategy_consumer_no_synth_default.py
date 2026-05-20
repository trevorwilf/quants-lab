"""Comprehensive sim does NOT use _synth_* suppliers by default.

Regression for [Report §1.6 #1 / §15.1 P0]: production simulator must read
real (fixture-or-loaded) data; the _synth_minute_bars / _synth_daily_bars
helpers belong to the smoke harness.
"""
from __future__ import annotations

import inspect

import bowaka_v2_lab.sim.backtester as bt


def test_backtester_has_no_synth_default_imports() -> None:
    src = inspect.getsource(bt)
    # The comprehensive backtester must not call _synth_minute_bars or _synth_daily_bars.
    assert "_synth_minute_bars" not in src
    assert "_synth_daily_bars" not in src


def test_backtester_takes_explicit_suppliers() -> None:
    sig = inspect.signature(bt.run_backtest)
    assert "minute_bars_supplier" in sig.parameters
    assert "daily_bars_supplier" in sig.parameters
