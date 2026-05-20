"""Numeric ranges match [Report §14.2]."""
from __future__ import annotations

from bowaka_v2_lab.optuna.search_space import SEARCH_SPACE_SPEC


def test_all_parameter_spec_kinds_are_known() -> None:
    valid = {"uniform", "int", "log_uniform"}
    for name, spec in SEARCH_SPACE_SPEC.items():
        assert spec[0] in valid, f"unknown kind {spec[0]} for {name}"


def test_numeric_ranges() -> None:
    s = SEARCH_SPACE_SPEC
    assert s["signals.rvol_so_far_min"] == ("uniform", 1.0, 5.0)
    assert s["signals.projected_full_day_rvol_min"] == ("uniform", 1.0, 5.0)
    assert s["signals.range_expansion_so_far_min"] == ("uniform", 1.0, 3.5)
    assert s["signals.close_location_so_far_min"] == ("uniform", 0.3, 0.95)
    assert s["signals.gap_pct_max"] == ("uniform", 0.02, 0.50)
    assert s["exits.max_hold_days"] == ("int", 1, 10)
    assert s["sizing.dollars_per_position"] == ("int", 500, 10_000)


def test_ranges_are_monotone_lo_lt_hi() -> None:
    for name, spec in SEARCH_SPACE_SPEC.items():
        if spec[0] in {"uniform", "log_uniform"}:
            assert spec[1] < spec[2], f"{name}: lo >= hi"
        elif spec[0] == "int":
            assert spec[1] <= spec[2], f"{name}: lo > hi"
