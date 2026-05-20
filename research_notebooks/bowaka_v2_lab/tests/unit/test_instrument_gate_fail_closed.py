"""Per [Report §8.6]: instrument_gate is fail-closed by default."""
from __future__ import annotations

import pytest

from bowaka_v2_lab.features import apply_v2_gates, instrument_gate


def test_default_rejects_none() -> None:
    assert instrument_gate(None) is False


def test_default_rejects_unknown_class() -> None:
    assert instrument_gate("etf") is False
    assert instrument_gate("spac") is False


def test_default_accepts_operating_equity() -> None:
    assert instrument_gate("operating_equity") is True


def test_research_mode_accepts_none() -> None:
    assert instrument_gate(None, allow_unknown_for_research=True) is True


def test_research_mode_still_rejects_explicit_unknown() -> None:
    # The opt-in only relaxes the None case, not explicit non-equity classes.
    assert instrument_gate("etf", allow_unknown_for_research=True) is False


def test_apply_v2_gates_threads_through_signals_cfg() -> None:
    # With allow_unknown=False (default), None instrument_class fails.
    _, gates_strict = apply_v2_gates(
        features={}, signals_cfg={"allow_unknown_instrument_class_for_research": False},
        instrument_class=None,
    )
    assert gates_strict["instrument_gate"] is False
    # With opt-in, None passes.
    _, gates_research = apply_v2_gates(
        features={}, signals_cfg={"allow_unknown_instrument_class_for_research": True},
        instrument_class=None,
    )
    assert gates_research["instrument_gate"] is True
