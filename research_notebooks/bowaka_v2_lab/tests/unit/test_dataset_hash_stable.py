"""Realism Phase 2 — the content-derived dataset hash is stable and reproducible.

Re-running on an identical lake produces an identical ``dataset_hash``; mutating
one minute parquet's size changes it. A small synthetic lake is built in
``tmp_path`` so the test is fast and hermetic.
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


def _build_lake(root, *, minute_rows: int = 60):
    """Build a minimal lake with one symbol's daily + minute bars + manifest."""
    symbol = "AAA"
    session = dt.date(2024, 9, 4)
    ddates = [session - dt.timedelta(days=i) for i in range(20, 0, -1)]
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
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(minute_rows)]
    _write(
        layout.minute_bars_path(root, symbol, 2024, 9),
        pd.DataFrame(
            {
                "symbol": [symbol] * minute_rows,
                "timestamp": mts,
                "open": [100.0] * minute_rows,
                "high": [101.0] * minute_rows,
                "low": [99.0] * minute_rows,
                "close": [100.5] * minute_rows,
                "volume": [5000.0] * minute_rows,
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
                "dataset_hashes": {"lake": "sha256:deadbeef"},
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


def test_dataset_hash_is_reproducible_on_identical_lake(tmp_path):
    lake = tmp_path / "lake"
    _build_lake(lake)
    cfg = _cfg(lake)
    start, end = dt.date(2024, 9, 1), dt.date(2024, 9, 30)

    lin1 = build_dataset_lineage(cfg=cfg, symbols=["AAA"], start=start, end=end, lab_config_hash="cfg1")
    lin2 = build_dataset_lineage(cfg=cfg, symbols=["AAA"], start=start, end=end, lab_config_hash="cfg1")

    assert lin1["regime"] == "lake"
    assert lin1["dataset_hash"] == lin2["dataset_hash"], "hash must be reproducible"
    # SHA-256 hexdigest is 64 chars; no "sha256:" prefix (Windows-path safe).
    assert len(lin1["dataset_hash"]) == 64
    assert ":" not in lin1["dataset_hash"]


def test_mutating_one_minute_parquet_size_changes_the_hash(tmp_path):
    lake_a = tmp_path / "lake_a"
    lake_b = tmp_path / "lake_b"
    _build_lake(lake_a, minute_rows=60)
    _build_lake(lake_b, minute_rows=120)  # larger minute parquet -> different size

    hash_a = build_dataset_lineage(
        cfg=_cfg(lake_a), symbols=["AAA"], start=dt.date(2024, 9, 1),
        end=dt.date(2024, 9, 30), lab_config_hash="cfg1",
    )["dataset_hash"]
    hash_b = build_dataset_lineage(
        cfg=_cfg(lake_b), symbols=["AAA"], start=dt.date(2024, 9, 1),
        end=dt.date(2024, 9, 30), lab_config_hash="cfg1",
    )["dataset_hash"]

    assert hash_a != hash_b, "a different minute parquet size must change the dataset hash"


def test_synthetic_regime_hash_is_stable_and_does_not_crash(tmp_path):
    """A no-lake (synthetic) config still produces a stable, deterministic hash."""
    cfg = {"market_data": {"feed": "iex", "minute_bar_source": "fixture", "daily_bar_source": "fixture"}}
    lin1 = build_dataset_lineage(
        cfg=cfg, symbols=["AAA", "BBB"], start=dt.date(2024, 9, 1),
        end=dt.date(2024, 9, 2), lab_config_hash="cfg1",
    )
    lin2 = build_dataset_lineage(
        cfg=cfg, symbols=["BBB", "AAA"], start=dt.date(2024, 9, 1),
        end=dt.date(2024, 9, 2), lab_config_hash="cfg1",
    )
    assert lin1["regime"] == "synthetic"
    assert lin1["provider"] == "fixture"
    assert lin1["dataset_hash"] == lin2["dataset_hash"]
    assert len(lin1["dataset_hash"]) == 64
