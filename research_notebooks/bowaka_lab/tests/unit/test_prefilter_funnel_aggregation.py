"""Tests for ``aggregate_prefilter_funnel``."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from bowaka_lab.features.prefilter import (
    FUNNEL_TOTAL_KEYS,
    aggregate_prefilter_funnel,
)


# Phase fidelity-2 added ``by_instrument_class`` to the top-level funnel block.
_EXPECTED_TOP_KEYS = {
    "universe_with_features",
    "passed_universe_gates",
    "candidates",
    "rejected_by_signal_gates",
    "excluded_by_instrument_class",
    "per_session",
    "by_instrument_class",
}


def _cset(**counts):
    return SimpleNamespace(metadata=counts)


def test_aggregate_prefilter_funnel_empty_dict_returns_zero_totals():
    out = aggregate_prefilter_funnel({})
    for k in FUNNEL_TOTAL_KEYS:
        assert out[k] == 0
    assert out["per_session"] == {}


def test_aggregate_prefilter_funnel_sums_across_sessions():
    csets = {
        date(2026, 5, 1): _cset(
            n_universe_with_features=11_000,
            n_passed_universe_gates=1_000,
            n_candidates=20,
            n_rejected_by_signal_gates=980,
            n_excluded_by_instrument_class=2,
        ),
        date(2026, 5, 2): _cset(
            n_universe_with_features=11_500,
            n_passed_universe_gates=1_050,
            n_candidates=25,
            n_rejected_by_signal_gates=1_020,
            n_excluded_by_instrument_class=5,
        ),
    }
    out = aggregate_prefilter_funnel(csets)
    assert out["universe_with_features"] == 22_500
    assert out["passed_universe_gates"] == 2_050
    assert out["candidates"] == 45
    assert out["rejected_by_signal_gates"] == 2_000
    assert out["excluded_by_instrument_class"] == 7


def test_aggregate_prefilter_funnel_emits_per_session_dict():
    csets = {
        date(2026, 5, 1): _cset(
            n_universe_with_features=10,
            n_passed_universe_gates=4,
            n_candidates=1,
            n_rejected_by_signal_gates=3,
            n_excluded_by_instrument_class=0,
        ),
    }
    out = aggregate_prefilter_funnel(csets)
    assert "2026-05-01" in out["per_session"]
    row = out["per_session"]["2026-05-01"]
    assert row["universe_with_features"] == 10
    assert row["candidates"] == 1


def test_aggregate_prefilter_funnel_keys_match_section_5_schema():
    out = aggregate_prefilter_funnel({})
    assert set(out.keys()) == _EXPECTED_TOP_KEYS


def test_aggregate_prefilter_funnel_missing_metadata_field_treated_as_zero():
    csets = {date(2026, 5, 1): _cset(n_candidates=3)}
    out = aggregate_prefilter_funnel(csets)
    assert out["candidates"] == 3
    assert out["universe_with_features"] == 0
