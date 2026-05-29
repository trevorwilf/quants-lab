"""Phase 1 (audit 2026-05-29 §5.4) — parity preflight blocks missing minute bars.

The full per-fold preflight now runs for ``current_code_parity`` (not just
``intended_realism``). A fold with NO forming-session minute bars is
un-runnable — the scanner has nothing to act on — so the preflight hard-fails
it BEFORE any trial, in BOTH modes.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.optuna.preflight import (
    FoldWindow,
    PreflightError,
    _clear_full_fold_preflight_cache,
    run_full_fold_preflight,
)
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from tests.fixtures.adjustment_lake import build_lake

_LAB_ROOT = Path(__file__).resolve().parents[2]


def _cfg(lake: Path) -> dict:
    cfg = load_config(_LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code.yml")
    cfg.pop("_source_path", None)
    cfg["market_data"]["shared_root"] = str(lake)
    cfg["universe"] = {**cfg.get("universe", {}), "min_adv_dollars": 0,
                       "min_price": 1.0, "max_price": 1_000.0}
    # isolate the minute-coverage gate: PIT floor of 1 (single fixture symbol)
    cfg["preflight"] = {"min_pit_universe_per_fold": 1}
    return cfg


def test_fold_missing_minute_coverage_blocks_study(tmp_path: Path) -> None:
    _clear_full_fold_preflight_cache()
    lake = tmp_path / "lake"
    # split_adjusted (the contract requires it); minute bars for AUGUST only.
    build_lake(
        lake, ["AAAA"],
        daily_start=dt.date(2024, 5, 1), daily_end=dt.date(2024, 9, 30),
        minute_months=[(2024, 8)], adjustment="split_adjusted",
        manifest_adjustment="split_adjusted",
    )
    cfg = _cfg(lake)
    folds = [
        FoldWindow(fold_id="val_2024-08-01", kind="validation",
                   start=dt.date(2024, 8, 1), end=dt.date(2024, 8, 28)),
        # September has NO minute bars -> must fail.
        FoldWindow(fold_id="val_2024-09-02", kind="validation",
                   start=dt.date(2024, 9, 2), end=dt.date(2024, 9, 27)),
    ]
    with pytest.raises(PreflightError) as ei:
        run_full_fold_preflight(
            cfg=cfg, folds=folds, symbols=["AAAA"], lake_root=str(lake), feed="iex",
            dataset_hash="d" * 64, config_hash="c" * 64,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
            min_quote_coverage_pct=95.0, mode="current_code_parity",
        )
    assert "missing_minute_coverage" in str(ei.value)
    _clear_full_fold_preflight_cache()
