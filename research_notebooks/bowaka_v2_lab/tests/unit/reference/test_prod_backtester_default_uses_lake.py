"""Regression for the 2026-05-29 dead-ternary bug.

The production backtester ``bowaka_v2_backtest.py`` MUST default to lake-backed
data suppliers when ``--synth`` is not passed. This test asserts the source code
no longer contains the dead-ternary pattern and that the new lake-supplier
helpers exist.
"""
from __future__ import annotations

import ast
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[3]   # tests/unit/reference/<this> -> lab root
    / "reference" / "source_strategy" / "scripts"
    / "bowaka_v2_backtest.py"
)


def test_no_dead_ternary_in_supplier_selection() -> None:
    src = _SCRIPT.read_text(encoding="utf-8")
    assert "_synth_minute_bars if args.synth else _synth_minute_bars" not in src
    assert "_synth_daily_bars if args.synth else _synth_daily_bars" not in src


def test_lake_supplier_helper_present() -> None:
    src = _SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn_names = {
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    }
    assert "_make_lake_suppliers" in fn_names
    assert "_resolve_backtest_lake_root" in fn_names
    assert "_resolve_required_adjustment" in fn_names
