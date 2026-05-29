"""Phase 1 (audit 2026-05-29 §5.4) — config requires split, lake lacks it.

When the config requires split_adjusted daily bars (the live contract) but the
lake has no split_adjusted daily partition on disk, the full-fold preflight
must hard-fail BEFORE any trial with a clear message — not silently read raw.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.optuna.preflight import (
    PreflightError,
    _clear_full_fold_preflight_cache,
    run_full_fold_preflight,
)
from tests.fixtures.adjustment_lake import build_lake


def test_split_required_but_only_raw_partition_raises(tmp_path: Path) -> None:
    _clear_full_fold_preflight_cache()
    lake = tmp_path / "lake"
    # Lake declares split_adjusted in its manifest but only the raw daily
    # partition exists on disk.
    build_lake(
        lake, ["AAAA"],
        daily_start=dt.date(2024, 6, 1), daily_end=dt.date(2024, 9, 1),
        minute_months=[(2024, 8)], adjustment="raw",
        manifest_adjustment="split_adjusted",
    )
    cfg = {
        "market_data": {"feed": "iex", "shared_root": str(lake),
                        "require_split_adjustment": True},
        "simulation": {"mode": "current_code_parity"},
        "universe": {"min_price": 1.0, "max_price": 1_000.0, "min_adv_dollars": 0},
    }
    with pytest.raises(PreflightError) as ei:
        run_full_fold_preflight(
            cfg=cfg, folds=[], symbols=["AAAA"], lake_root=str(lake), feed="iex",
            dataset_hash="d" * 64, config_hash="c" * 64,
            scan_times_per_session=lambda d: [],
            min_quote_coverage_pct=95.0, mode="current_code_parity",
        )
    msg = str(ei.value)
    assert "split_adjusted" in msg
    assert "no split_adjusted daily partition" in msg
    _clear_full_fold_preflight_cache()
