"""Realism Phase 2 — the dataset hash depends on the lake manifest hash.

Mutating the lake manifest's ``dataset_hashes.lake`` (its own content hash)
changes the run's ``dataset_hash``, even when the bar partitions are unchanged.
"""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.lineage import build_dataset_lineage


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_lake(root, *, lake_manifest_hash: str):
    """Minimal lake: one symbol's daily bars + a manifest carrying ``lake_manifest_hash``."""
    symbol = "AAA"
    session = dt.date(2024, 9, 4)
    ddates = [session - dt.timedelta(days=i) for i in range(10, 0, -1)]
    _write(
        layout.daily_bars_path(root, symbol),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(ddates),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
                "open": [100.0] * len(ddates),
                "high": [101.0] * len(ddates),
                "low": [99.0] * len(ddates),
                "close": [100.0] * len(ddates),
                "volume": [1_000_000] * len(ddates),
                "session_date": ddates,
            }
        ),
    )
    manifest_path = layout.ingestion_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "feed": "iex",
                "adjustment": "raw",
                "dataset_hashes": {"lake": lake_manifest_hash},
            }
        ),
        encoding="utf-8",
    )


def _cfg(lake_root):
    return {
        "market_data": {
            "feed": "iex",
            "minute_bar_source": "alpaca",
            "daily_bar_source": "alpaca",
            "shared_root": str(lake_root),
        }
    }


def test_mutating_lake_manifest_hash_changes_dataset_hash(tmp_path):
    lake_a = tmp_path / "lake_a"
    lake_b = tmp_path / "lake_b"
    # Identical bar partitions; only the lake manifest hash differs.
    _build_lake(lake_a, lake_manifest_hash="sha256:1111111111111111")
    _build_lake(lake_b, lake_manifest_hash="sha256:2222222222222222")

    start, end = dt.date(2024, 9, 1), dt.date(2024, 9, 30)
    lin_a = build_dataset_lineage(
        cfg=_cfg(lake_a), symbols=["AAA"], start=start, end=end, lab_config_hash="cfg1"
    )
    lin_b = build_dataset_lineage(
        cfg=_cfg(lake_b), symbols=["AAA"], start=start, end=end, lab_config_hash="cfg1"
    )

    assert lin_a["regime"] == "lake" and lin_b["regime"] == "lake"
    # The lake manifest hash is a hash component...
    assert lin_a["components"]["lake_manifest_hash"] == "sha256:1111111111111111"
    assert lin_b["components"]["lake_manifest_hash"] == "sha256:2222222222222222"
    # ...so the dataset hash differs even though the bars are identical.
    assert lin_a["dataset_hash"] != lin_b["dataset_hash"]


def test_lab_config_hash_is_a_hash_component(tmp_path):
    """A different lab_config_hash also changes the dataset hash."""
    lake = tmp_path / "lake"
    _build_lake(lake, lake_manifest_hash="sha256:abcabc")
    start, end = dt.date(2024, 9, 1), dt.date(2024, 9, 30)
    lin1 = build_dataset_lineage(
        cfg=_cfg(lake), symbols=["AAA"], start=start, end=end, lab_config_hash="cfgA"
    )
    lin2 = build_dataset_lineage(
        cfg=_cfg(lake), symbols=["AAA"], start=start, end=end, lab_config_hash="cfgB"
    )
    assert lin1["dataset_hash"] != lin2["dataset_hash"]
