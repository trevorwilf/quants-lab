"""Phase 3: candidate schema v3 (research-only)."""

from __future__ import annotations

import pytest

from bowaka_lab.data.schemas import build_candidate_v3, candidate_v3_doc


def test_v3_requires_signal_and_trade_date():
    with pytest.raises(ValueError):
        candidate_v3_doc(payload={"strategy": "bowaka", "generated_at": "x"})


def test_v3_includes_dataset_hash_and_all_decisions_path():
    doc = build_candidate_v3(
        strategy="bowaka",
        generated_at="2026-05-11T22:00:00Z",
        signal_date="2026-05-11",
        trade_date="2026-05-12",
        provider="alpaca",
        data_feed="iex",
        bar_timeframe="1D",
        adjustment="raw",
        config_hash="sha256:cfg",
        dataset_hash="sha256:dataset",
        universe_hash="sha256:u",
        candidates=[],
        all_decisions_path="parquet/.../decisions.parquet",
    )
    assert doc["schema_version"] == 3
    assert doc["signal_date"] == "2026-05-11"
    assert doc["trade_date"] == "2026-05-12"
    assert doc["dataset_hash"] == "sha256:dataset"
    assert doc["all_decisions_path"].endswith("decisions.parquet")
