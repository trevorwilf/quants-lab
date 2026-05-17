"""Phase 3: candidate schema v2 (legacy strategy compatibility)."""

from __future__ import annotations

import pytest

from bowaka_lab.data.schemas import build_candidate_v2, candidate_v2_doc


def test_v2_doc_requires_strategy():
    with pytest.raises(ValueError):
        candidate_v2_doc(payload={"generated_at": "x"})


def test_v2_doc_round_trip():
    payload = {
        "strategy": "bowaka",
        "generated_at": "2026-05-11T22:00:00Z",
        "as_of_date": "2026-05-11",
        "provider": "alpaca",
        "data_feed": "iex",
        "bar_timeframe": "1D",
        "config_hash": "sha256:abc",
        "universe_hash": "sha256:def",
        "candidates": [],
    }
    doc = candidate_v2_doc(payload=payload)
    assert doc["schema_version"] == 2
    assert doc["strategy"] == "bowaka"
    assert doc["candidates"] == []


def test_build_candidate_v2_fills_counts():
    doc = build_candidate_v2(
        strategy="bowaka",
        generated_at="2026-05-11T22:00:00Z",
        signal_date="2026-05-11",
        provider="alpaca",
        data_feed="iex",
        bar_timeframe="1D",
        config_hash="sha256:cfg",
        config_hash_short="cfg12345",
        universe_hash="sha256:u",
        latest_bar_timestamp="2026-05-11T20:00:00Z",
        counts={"n_universe_with_features": 11119, "n_passed_universe_gates": 1070, "n_candidates": 17, "n_excluded_by_instrument_class": 2},
        candidates=[],
    )
    assert doc["schema_version"] == 2
    assert doc["n_universe_with_features"] == 11119
    assert doc["n_passed_universe_gates"] == 1070
    assert doc["n_in_play"] == 17
    assert doc["n_excluded_by_instrument_class"] == 2
    assert doc["as_of_date"] == "2026-05-11"
