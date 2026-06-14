"""Phase 1 (audit 2026-05-29 §5.4) — IEX parity warns (not fails) on missing quotes.

Under ``current_code_parity`` a lake with daily + minute bars but NO quotes
partition PASSES the full-fold preflight, BUT the result records
``missing_historical_quotes`` as an IEX partial-tape limitation (so a reviewer
can never mistake it for a SIP-grade run). Under ``intended_realism`` the same
fixture HARD-FAILS (preserved behaviour).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.optuna.preflight import (
    FoldWindow,
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
    cfg["preflight"] = {"min_pit_universe_per_fold": 1}
    return cfg


def _folds() -> list[FoldWindow]:
    return [FoldWindow(fold_id="val_2024-08-01", kind="validation",
                       start=dt.date(2024, 8, 1), end=dt.date(2024, 8, 28))]


def test_parity_passes_and_records_missing_quotes_limitation(tmp_path: Path) -> None:
    _clear_full_fold_preflight_cache()
    lake = tmp_path / "lake"
    build_lake(
        lake, ["AAAA"],
        daily_start=dt.date(2024, 5, 1), daily_end=dt.date(2024, 9, 30),
        minute_months=[(2024, 8)], adjustment=("raw", "split_adjusted", "all"),
        manifest_adjustment="all",
    )  # no quotes partition written
    cfg = _cfg(lake)
    result = run_full_fold_preflight(
        cfg=cfg, folds=_folds(), symbols=["AAAA"], lake_root=str(lake), feed="iex",
        dataset_hash="d" * 64, config_hash="c" * 64,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        min_quote_coverage_pct=95.0, mode="current_code_parity",
        raise_on_fail=False,
    )
    assert result.passed is True
    assert "missing_historical_quotes" in result.iex_partial_tape_limitations
    _clear_full_fold_preflight_cache()


def test_intended_realism_hard_fails_on_missing_quotes(tmp_path: Path) -> None:
    _clear_full_fold_preflight_cache()
    lake = tmp_path / "lake"
    build_lake(
        lake, ["AAAA"],
        daily_start=dt.date(2024, 5, 1), daily_end=dt.date(2024, 9, 30),
        minute_months=[(2024, 8)], adjustment=("raw", "split_adjusted", "all"),
        manifest_adjustment="all",
    )
    cfg = _cfg(lake)
    cfg["simulation"] = {"mode": "intended_realism"}
    result = run_full_fold_preflight(
        cfg=cfg, folds=_folds(), symbols=["AAAA"], lake_root=str(lake), feed="iex",
        dataset_hash="d2" * 32, config_hash="c2" * 32,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        min_quote_coverage_pct=95.0, mode="intended_realism",
        raise_on_fail=False,
    )
    assert result.passed is False
    _clear_full_fold_preflight_cache()
