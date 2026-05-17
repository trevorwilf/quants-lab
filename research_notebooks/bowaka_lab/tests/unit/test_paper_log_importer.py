"""Phase 7: paper log importer."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.reconcile.paper_log_importer import (
    load_candidate_file,
    load_daily_summary,
    load_per_trade_logs,
    load_trade_ledger,
)


@pytest.fixture
def minimal(fixtures_dir: Path) -> Path:
    return fixtures_dir / "paper_trade_logs_minimal"


def test_load_candidate_file(minimal: Path):
    payload = load_candidate_file(minimal / "in_play_candidates.json")
    assert payload["schema_version"] == 2
    assert payload["strategy"] == "bowaka"
    assert len(payload["candidates"]) == 4


def test_load_daily_summary(minimal: Path):
    res = load_daily_summary(minimal / "daily_summary.jsonl")
    assert not res.df.empty
    assert "AAA" in res.df["ticker"].values
    assert res.errors.empty


def test_load_trade_ledger(minimal: Path):
    res = load_trade_ledger(minimal / "trade_ledger.jsonl")
    assert not res.df.empty
    assert "event_type" in res.df.columns


def test_load_per_trade_logs(minimal: Path):
    res = load_per_trade_logs(minimal / "trades")
    assert not res.df.empty
    files = res.df["source_file"].unique().tolist()
    assert "BOWAKA-AAA-1001.jsonl" in files
    assert "BOWAKA-BBB-1002.jsonl" in files
    assert "BOWAKA-CCC-1003.jsonl" in files
    assert "BOWAKA-DDD-1004.jsonl" in files


def test_missing_candidate_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_candidate_file(tmp_path / "does_not_exist.json")


def test_malformed_jsonl_lines_recorded_not_raised(tmp_path):
    p = tmp_path / "broken.jsonl"
    p.write_text('{"valid": 1}\nnot-json\n{"valid": 2}\n', encoding="utf-8")
    res = load_daily_summary(p)
    assert res.df.shape[0] == 2
    assert res.errors.shape[0] == 1
    assert res.errors.iloc[0]["lineno"] == 2
