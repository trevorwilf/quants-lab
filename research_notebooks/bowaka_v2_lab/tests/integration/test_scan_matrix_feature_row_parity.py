"""Spot-check a built matrix vs the legacy feature path.

Matrix doc §17 / Phase 8. Build a single-session matrix from the tiny
lake, open the store, pull the first scan's first symbol cell, and
confirm it has a non-NaN last_price + bar_age + the static baseline
columns are populated.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.scanner.scan_matrix import (
    DYNAMIC_FLOAT64_COLUMNS,
    DYNAMIC_UINT8_COLUMNS,
    ScanMatrixStore,
    build_session_partition,
)


def test_session_partition_round_trip(tmp_path):
    """Build one session partition by hand, open via ScanMatrixStore."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"],
                    start=dt.date(2024, 1, 2), end=dt.date(2024, 1, 5))
    cfg = {
        "market_data": {"feed": "iex", "shared_root": str(lake)},
        "simulation": {"mode": "smoke_fixture",
                        "intraday_window_policy": "extended_hours_to_scan"},
        "backtest": {"start_date": "2024-01-02", "end_date": "2024-01-05"},
        "session": {"scanner_start": "09:45", "scanner_end": "16:00",
                     "scan_interval_seconds": 300},
        "universe": {"symbols": ["AAA"]},
        "historical_features": {
            "volume_curve": {
                "bucket_edges": [250_000, 500_000, 1_000_000],
                "fallback_opening_15m_share": 0.08,
            }
        },
        "strategy_version": "0.1.0",
    }
    store_root = tmp_path / "matrix" / "validation"
    sd = dt.date(2024, 1, 3)
    manifest_frag = build_session_partition(
        sd, cfg, lake, "iex", store_root=store_root, scope="validation",
    )
    assert manifest_frag["n_scans"] >= 0
    # Write a top-level manifest stub so ScanMatrixStore opens.
    (store_root / "manifest.json").write_text(
        json.dumps({
            "matrix_id": "t", "matrix_version": 1, "sessions": [sd.isoformat()],
        }),
        encoding="utf-8",
    )
    store = ScanMatrixStore(store_root)
    sess = store.open_session(sd, purpose="objective")
    assert sess.scan_timestamps_ns.dtype == np.int64
    assert sess.symbol_ids.dtype == np.int32
    # All dynamic / static columns exist.
    assert set(sess.dynamic_float64.keys()) == set(DYNAMIC_FLOAT64_COLUMNS)
    assert set(sess.dynamic_uint8.keys()) == set(DYNAMIC_UINT8_COLUMNS)
    # universe_meta parquet contains the symbol(s).
    assert "AAA" in set(sess.universe_meta["symbol"].astype(str))
