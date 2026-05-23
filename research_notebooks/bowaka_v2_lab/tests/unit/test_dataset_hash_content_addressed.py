"""Walk-forward dataset hash is content-addressed (audit §P1-005).

Realism remediation 2 Phase 8. Replaces the pre-Phase-8 ``[symbols, feed, dates]``
digest with :func:`bowaka_v2_lab.data.lineage.content_addressed_dataset_hash`,
which SHA-256s the lake manifest + every bars/quotes/CA parquet's footer hash +
adjustment policy + config hash + code hash. Two folds over identical inputs
produce the same hash; one parquet byte edit changes it.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_v2_lab.data.lineage import (
    _FOOTER_HASH_CACHE,
    content_addressed_dataset_hash,
)
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake


def _hash(lake: Path, *, config_hash: str = "cfg", code_hash: str = "code") -> str:
    """Helper — return just the dataset_hash string."""
    return content_addressed_dataset_hash(
        lake_root=lake, config_hash=config_hash, code_manifest_hash=code_hash,
    )["dataset_hash"]


def test_two_folds_over_identical_inputs_hash_identically(tmp_path: Path) -> None:
    """Two hashes over the same inputs (lake + config + code) agree."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 2, 1))
    # Clear the process-local footer cache so neither call benefits from a
    # warm cache — proves byte-stability, not just cache-stability.
    _FOOTER_HASH_CACHE.clear()
    a = _hash(lake)
    _FOOTER_HASH_CACHE.clear()
    b = _hash(lake)
    assert a == b
    assert len(a) == 64  # SHA-256 hex


def test_hash_changes_on_parquet_byte_edit(tmp_path: Path) -> None:
    """Editing one parquet's content changes the dataset hash (content-addressed).

    The test rewrites one minute-bar parquet's ``close`` column (bump by 1.0)
    using pandas → arrow to preserve the original column dtypes (so the schema
    stays compatible with the rest of the lake). The footer hash captures the
    column statistics, so the dataset hash MUST change.
    """
    import pandas as pd

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 2, 1))
    h_before = _hash(lake)

    minute_parquet = next(
        (lake / "bars").rglob("timeframe=1m/**/*.parquet"), None,
    )
    assert minute_parquet is not None, "tiny lake must have a minute-bar parquet"

    # Read via pandas (preserves the column types build_tiny_lake wrote) and
    # bump the close. Write back with the same engine/path; row-group stats
    # (min/max of close) change, so the footer hash changes.
    df = pd.read_parquet(minute_parquet)
    df["close"] = df["close"].astype(float) + 1.0
    df.to_parquet(minute_parquet, index=False)

    # The cache is keyed by (mtime_ns, size) — the file just changed but force-
    # clear so we never read a stale entry.
    _FOOTER_HASH_CACHE.clear()
    h_after = _hash(lake)
    assert h_before != h_after, (
        f"editing a minute-bar parquet should change the dataset hash; "
        f"before={h_before} after={h_after}"
    )


def test_hash_changes_on_config_hash(tmp_path: Path) -> None:
    """A different config hash produces a different dataset hash."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 2, 1))
    a = _hash(lake, config_hash="cfg_A")
    b = _hash(lake, config_hash="cfg_B")
    assert a != b


def test_hash_changes_on_code_hash(tmp_path: Path) -> None:
    """A different code-manifest hash produces a different dataset hash."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 2, 1))
    a = _hash(lake, code_hash="code_A")
    b = _hash(lake, code_hash="code_B")
    assert a != b


def test_hash_exposes_components_for_forensics(tmp_path: Path) -> None:
    """The component dict carries the lake manifest, parquet paths/footers, etc."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 2, 1))
    result = content_addressed_dataset_hash(
        lake_root=lake, config_hash="cfg", code_manifest_hash="code",
    )
    components = result["components"]
    # The components dict carries every input that feeds the hash so a forensic
    # investigator can re-derive (or diff) the hash without re-running the lake.
    assert "manifest_canonical" in components
    assert "parquet_partition_paths" in components
    assert "parquet_footer_hashes" in components
    assert "adjustment_policy" in components
    assert "config_hash" in components
    assert "code_manifest_hash" in components
    # And the parquet inventory is non-empty for a populated lake.
    assert components["parquet_partition_paths"], "no parquet partitions found"
