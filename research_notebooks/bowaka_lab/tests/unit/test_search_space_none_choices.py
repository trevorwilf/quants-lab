"""Phase 9: search space honors `None` choices for nullable maxes."""

from __future__ import annotations

from bowaka_lab.optuna.search_space import suggest_params


class _StubTrial:
    """Replays a recorded set of suggestions for a deterministic test."""

    def __init__(self, decisions: dict):
        self.decisions = decisions

    def suggest_float(self, name, low, high):
        return self.decisions.get(name, (low + high) / 2.0)

    def suggest_int(self, name, low, high):
        return self.decisions.get(name, low)

    def suggest_categorical(self, name, choices):
        return self.decisions.get(name, choices[0])


def test_none_max_is_passed_as_none():
    decisions = {
        "rvol_max": "None",
        "range_expansion_max": "None",
        "gap_pct_max": "None",
        "entry_rule": "fixed_time_0945",
        "signal_fade_threshold": "None",
    }
    params = suggest_params(_StubTrial(decisions))
    assert params["rvol_max"] is None
    assert params["range_expansion_max"] is None
    assert params["gap_pct_max"] is None
    assert params["signal_fade_threshold"] is None


def test_numeric_max_is_parsed_as_float():
    decisions = {
        "rvol_max": "5.0",
        "range_expansion_max": "4.0",
        "gap_pct_max": "0.30",
        "entry_rule": "fixed_time_0945",
        "signal_fade_threshold": "8",
    }
    params = suggest_params(_StubTrial(decisions))
    assert params["rvol_max"] == 5.0
    assert params["gap_pct_max"] == 0.30
    assert params["signal_fade_threshold"] == 8
