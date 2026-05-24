"""``bowaka-v2-lab verify-lake`` CLI (audit 2026-05-23 §P0-004 / §P0-005 / Phase 1).

Validates the verifier exits non-zero under ``--intended-realism`` when a
required parquet partition is missing, and exits zero (with warn-level
checks) when ``--intended-realism`` is not set.
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import pytest


def _write_parquet(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_minimal_lake(lake: Path, *, feed: str = "iex") -> None:
    """Write a minimal lake with one bar partition per timeframe + quotes + statuses + CA + assets + manifest."""
    # daily bars
    _write_parquet(
        lake / "bars" / "vendor=alpaca" / f"feed={feed}" / "timeframe=1d"
        / "adjustment=split_adjusted" / "symbol=AAA" / "part.parquet",
        pd.DataFrame({"symbol": ["AAA"], "timestamp": [pd.Timestamp("2024-01-02")]}),
    )
    # minute bars
    _write_parquet(
        lake / "bars" / "vendor=alpaca" / f"feed={feed}" / "timeframe=1m"
        / "adjustment=raw" / "symbol=AAA" / "year=2024" / "month=01"
        / "part.parquet",
        pd.DataFrame({"symbol": ["AAA"], "timestamp": [pd.Timestamp("2024-01-02 10:00")]}),
    )
    # quotes
    _write_parquet(
        lake / "quotes" / "vendor=alpaca" / f"feed={feed}" / "symbol=AAA"
        / "year=2024" / "month=01" / "part.parquet",
        pd.DataFrame({"symbol": ["AAA"]}),
    )
    # statuses
    _write_parquet(
        lake / "statuses" / "vendor=alpaca" / "symbol=AAA" / "date=2024-01-02"
        / "part.parquet",
        pd.DataFrame({"symbol": ["AAA"]}),
    )
    # corporate actions
    _write_parquet(
        lake / "corporate_actions" / "vendor=alpaca" / "symbol=AAA" / "part.parquet",
        pd.DataFrame({"symbol": ["AAA"]}),
    )
    # assets
    _write_parquet(
        lake / "assets" / "vendor=alpaca" / "snapshot_id=20240101000000" / "assets.parquet",
        pd.DataFrame({"symbol": ["AAA"]}),
    )
    # ingestion manifest with split-adjusted (intended_realism-compatible)
    manifest_dir = lake / "_ingestion"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "manifest.json").write_text(
        json.dumps({"adjustment": "split_adjusted",
                    "feeds": {feed: {"adjustment": "split_adjusted"}}}),
        encoding="utf-8",
    )


def _build_partial_lake(lake: Path, *, feed: str = "iex") -> None:
    """A partial lake: bars present, but no quotes / statuses / CA / assets / manifest."""
    _write_parquet(
        lake / "bars" / "vendor=alpaca" / f"feed={feed}" / "timeframe=1d"
        / "adjustment=raw" / "symbol=AAA" / "part.parquet",
        pd.DataFrame({"symbol": ["AAA"]}),
    )


def _run_cli(args: list[str]) -> tuple[int, dict]:
    from bowaka_v2_lab import cli

    buf = StringIO()
    saved = sys.stdout
    sys.stdout = buf
    try:
        rc = cli.main(args)
    finally:
        sys.stdout = saved
    text = buf.getvalue()
    # The CLI prints exactly one JSON document.
    try:
        doc = json.loads(text)
    except Exception:
        doc = {"_raw": text}
    return rc, doc


def test_complete_lake_passes_intended_realism(tmp_path):
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, feed="iex")
    rc, doc = _run_cli([
        "verify-lake", "--lake", str(lake), "--feed", "iex", "--intended-realism",
    ])
    assert rc == 0, f"expected pass, got rc={rc}, doc={doc}"
    assert doc["passed"] is True
    assert doc["intended_realism"] is True
    assert doc["summary"]["fail"] == 0


def test_partial_lake_fails_intended_realism(tmp_path):
    lake = tmp_path / "lake"
    _build_partial_lake(lake, feed="iex")
    rc, doc = _run_cli([
        "verify-lake", "--lake", str(lake), "--feed", "iex", "--intended-realism",
    ])
    assert rc == 1, f"expected fail, got rc={rc}"
    assert doc["passed"] is False
    assert doc["summary"]["fail"] >= 1
    failed_names = {c["name"] for c in doc["checks"] if c["status"] == "fail"}
    # quotes / statuses / corporate_actions / assets / manifest_adjustment all missing
    assert "quotes_iex" in failed_names
    assert "statuses" in failed_names
    assert "corporate_actions" in failed_names
    assert "assets" in failed_names


def test_partial_lake_warns_without_intended_realism(tmp_path):
    lake = tmp_path / "lake"
    _build_partial_lake(lake, feed="iex")
    rc, doc = _run_cli([
        "verify-lake", "--lake", str(lake), "--feed", "iex",
    ])
    # Without --intended-realism the CLI still emits warn-level checks but
    # exits 0 (failing would block normal research; warnings are surfaced).
    assert rc == 0
    assert doc["intended_realism"] is False
    assert doc["summary"]["warn"] >= 1


def test_raw_manifest_fails_intended_realism(tmp_path):
    """A manifest declaring ``adjustment: raw`` fails under intended_realism."""
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, feed="iex")
    # Overwrite the manifest with raw adjustment.
    (lake / "_ingestion" / "manifest.json").write_text(
        json.dumps({"adjustment": "raw"}),
        encoding="utf-8",
    )
    rc, doc = _run_cli([
        "verify-lake", "--lake", str(lake), "--feed", "iex", "--intended-realism",
    ])
    assert rc == 1
    assert any(
        c["name"] == "manifest_adjustment" and c["status"] == "fail"
        for c in doc["checks"]
    )


def test_one_asset_snapshot_warns_under_intended_realism(tmp_path):
    """A single asset snapshot is warn-only (failing would block research)."""
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, feed="iex")
    rc, doc = _run_cli([
        "verify-lake", "--lake", str(lake), "--feed", "iex", "--intended-realism",
    ])
    assert rc == 0  # warn doesn't flip passed
    assets_check = next(c for c in doc["checks"] if c["name"] == "assets")
    assert assets_check["status"] == "warn"
    assert "1" in assets_check["detail"] or "P1-001" in assets_check["detail"]


def test_complete_lake_with_multiple_snapshots_passes(tmp_path):
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, feed="iex")
    # Add a second snapshot directory.
    _write_parquet(
        lake / "assets" / "vendor=alpaca" / "snapshot_id=20240601000000"
        / "assets.parquet",
        pd.DataFrame({"symbol": ["AAA"]}),
    )
    rc, doc = _run_cli([
        "verify-lake", "--lake", str(lake), "--feed", "iex", "--intended-realism",
    ])
    assert rc == 0
    assets_check = next(c for c in doc["checks"] if c["name"] == "assets")
    assert assets_check["status"] == "pass"
