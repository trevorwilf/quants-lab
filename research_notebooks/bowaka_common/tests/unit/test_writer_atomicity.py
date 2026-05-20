"""Writer atomicity: partial-write failure leaves no half-written file."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from bowaka_common.artifacts.writer import write_json, write_jsonl, write_parquet, write_run_dir


def test_write_json_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "manifest.json"
    write_json(p, {"a": 1, "b": [2, 3]})
    assert p.is_file()
    assert "a" in p.read_text()


def test_write_jsonl_creates_file_and_counts(tmp_path: Path) -> None:
    p = tmp_path / "events.jsonl"
    n = write_jsonl(p, [{"x": 1}, {"x": 2}, {"x": 3}])
    assert n == 3
    assert sum(1 for _ in p.open("r", encoding="utf-8")) == 3


def test_write_parquet_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "data.parquet"
    df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
    write_parquet(p, df)
    assert p.is_file()
    back = pd.read_parquet(p)
    assert list(back.columns) == ["a", "b"]


def test_write_json_atomic_no_partial_on_failure(tmp_path: Path) -> None:
    p = tmp_path / "fail.json"
    # Inject failure by making os.replace raise; verify no .tmp lingers.
    with patch("bowaka_common.artifacts.writer.os.replace", side_effect=OSError("simulated")):
        with pytest.raises(OSError):
            write_json(p, {"a": 1})
    assert not p.is_file()
    assert not any(name.endswith(".tmp") for name in os.listdir(tmp_path))


def test_write_run_dir_bulk(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    counts = write_run_dir(
        rd,
        json_files={"summary.json": {"ok": True}},
        jsonl_files={"events.jsonl": [{"e": 1}, {"e": 2}]},
        parquet_files={"trades.parquet": pd.DataFrame({"sym": ["AAPL"]})},
    )
    assert counts["summary.json"] == 1
    assert counts["events.jsonl"] == 2
    assert counts["trades.parquet"] == 1
    assert (rd / "summary.json").is_file()
    assert (rd / "events.jsonl").is_file()
    assert (rd / "trades.parquet").is_file()
