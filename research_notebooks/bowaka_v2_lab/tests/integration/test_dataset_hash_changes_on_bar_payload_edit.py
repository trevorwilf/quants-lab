"""Realism remediation 2 Phase 3 — content-addressed dataset hash (§P1-005).

Editing one byte of a bar parquet's payload must change its footer hash and
therefore the dataset hash. The cache (keyed by ``mtime + size``) must NOT mask
the change — the file's mtime / size both move when we overwrite it.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.lineage import (
    _FOOTER_HASH_CACHE,
    content_addressed_dataset_hash,
)


def _build_minimal_lake(root: Path) -> None:
    """A tiny lake with one daily-bar parquet and a manifest."""
    df = pd.DataFrame(
        {
            "symbol": ["AAA"] * 5,
            "timestamp": pd.date_range("2024-09-01", periods=5, tz="UTC"),
            "open": [10.0, 10.1, 10.2, 10.3, 10.4],
            "high": [10.2, 10.3, 10.4, 10.5, 10.6],
            "low": [9.9, 10.0, 10.1, 10.2, 10.3],
            "close": [10.1, 10.2, 10.3, 10.4, 10.5],
            "volume": [1_000.0, 1_100.0, 1_200.0, 1_300.0, 1_400.0],
            "session_date": pd.date_range("2024-09-01", periods=5).date,
        }
    )
    path = layout.daily_bars_path(root, "AAA", feed="iex", adjustment="raw")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    manifest_path = layout.ingestion_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        '{"feed":"iex","adjustment":"raw","dataset_hashes":{"lake":"sha256:test"}}',
        encoding="utf-8",
    )


def test_dataset_hash_changes_when_bar_payload_changes(tmp_path: Path) -> None:
    lake = tmp_path / "lake_a"
    _build_minimal_lake(lake)
    _FOOTER_HASH_CACHE.clear()

    h_before = content_addressed_dataset_hash(
        lake_root=lake, config_hash="cfg", code_manifest_hash="code"
    )["dataset_hash"]

    # Overwrite the bar payload with a different close column.
    path = layout.daily_bars_path(lake, "AAA", feed="iex", adjustment="raw")
    df = pd.read_parquet(path)
    df.loc[df.index[-1], "close"] = 99.99   # genuine payload change
    df.to_parquet(path, index=False)
    # Force the mtime to move so the cache key invalidates even on filesystems
    # with coarse mtime granularity.
    import os, time

    os.utime(path, None)
    time.sleep(0.05)

    h_after = content_addressed_dataset_hash(
        lake_root=lake, config_hash="cfg", code_manifest_hash="code"
    )["dataset_hash"]
    assert h_before != h_after, "payload edit must change the content-addressed hash"


def test_dataset_hash_changes_when_config_hash_changes(tmp_path: Path) -> None:
    lake = tmp_path / "lake_b"
    _build_minimal_lake(lake)
    _FOOTER_HASH_CACHE.clear()

    h1 = content_addressed_dataset_hash(
        lake_root=lake, config_hash="cfgA", code_manifest_hash="codeX"
    )["dataset_hash"]
    h2 = content_addressed_dataset_hash(
        lake_root=lake, config_hash="cfgB", code_manifest_hash="codeX"
    )["dataset_hash"]
    h3 = content_addressed_dataset_hash(
        lake_root=lake, config_hash="cfgA", code_manifest_hash="codeY"
    )["dataset_hash"]
    assert h1 != h2  # config hash flows in
    assert h1 != h3  # code hash flows in
