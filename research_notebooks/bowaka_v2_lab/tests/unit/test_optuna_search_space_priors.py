"""Search-space spec invariants (realism remediation Phase 9 rebuild).

The numeric ranges changed in Phase 9 — the search space is now rebuilt against
the live contract and every bound covers the live value. The structural
invariants tested here (known kinds, monotone bounds) survive the rebuild.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.search_space import (
    SEARCH_SPACE_SPEC,
    resolve_search_space,
    suggest_params,
)


def test_all_parameter_spec_kinds_are_known() -> None:
    valid = {"uniform", "int", "log_uniform", "categorical"}
    for name, spec in SEARCH_SPACE_SPEC.items():
        assert spec[0] in valid, f"unknown kind {spec[0]} for {name}"


def test_ranges_are_monotone_lo_lt_hi() -> None:
    for name, spec in SEARCH_SPACE_SPEC.items():
        if spec[0] in {"uniform", "log_uniform"}:
            assert spec[1] < spec[2], f"{name}: lo >= hi"
        elif spec[0] == "int":
            assert spec[1] <= spec[2], f"{name}: lo > hi"
        elif spec[0] == "categorical":
            assert len(spec[1]) >= 1, f"{name}: empty categorical choice set"


def test_rvol_lower_bound_covers_live_iex_value() -> None:
    """Audit P0-013: rvol_so_far_min lower bound must reach the live 0.7."""
    kind, lo, hi = SEARCH_SPACE_SPEC["signals.rvol_so_far_min"]
    assert kind == "uniform"
    assert lo <= 0.7 <= hi


def test_resolve_search_space_freeze_drops_parameter() -> None:
    spec = resolve_search_space({"exits.max_hold_days": "freeze"})
    assert "exits.max_hold_days" not in spec
    assert "signals.gap_pct_max" in spec  # untouched


def test_resolve_search_space_override_replaces_bounds() -> None:
    spec = resolve_search_space({"exits.stop_pct": ("uniform", 0.02, 0.04)})
    assert spec["exits.stop_pct"] == ("uniform", 0.02, 0.04)


class _FakeTrial:
    """Minimal Optuna-trial stand-in for suggest_params."""

    def suggest_float(self, name, lo, hi, log=False):  # noqa: ARG002
        return (lo + hi) / 2.0

    def suggest_int(self, name, lo, hi):  # noqa: ARG002
        return (lo + hi) // 2

    def suggest_categorical(self, name, choices):  # noqa: ARG002
        return choices[0]


def test_suggest_params_returns_every_spec_key() -> None:
    params = suggest_params(_FakeTrial())
    assert set(params) == set(SEARCH_SPACE_SPEC)


def test_suggest_params_honours_overrides() -> None:
    params = suggest_params(_FakeTrial(), overrides={"exits.max_hold_days": "freeze"})
    assert "exits.max_hold_days" not in params
