"""Phase 5 (audit 2026-05-29 §9 Phase 7) — NBBO quote-coverage gate.

intended_realism + sip with no NBBO coverage hard-fails; intended_realism + iex
hard-fails with NBBO_NOT_AVAILABLE_ON_IEX; current_code_parity warns only.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.optuna.preflight import (
    FoldWindow,
    PreflightError,
    check_nbbo_quote_coverage,
)


def _folds():
    return [FoldWindow(fold_id="val", kind="validation",
                       start=dt.date(2024, 8, 1), end=dt.date(2024, 8, 28))]


def test_intended_realism_sip_hard_fails_without_coverage(tmp_path: Path) -> None:
    with pytest.raises(PreflightError) as ei:
        check_nbbo_quote_coverage(
            sim_mode="intended_realism", feed="sip", lake_root=tmp_path,
            universe=["AAA"], fold_windows=_folds(), min_coverage_pct=95.0,
        )
    assert "NBBO" in str(ei.value)


def test_intended_realism_iex_hard_fails_nbbo_not_available(tmp_path: Path) -> None:
    with pytest.raises(PreflightError) as ei:
        check_nbbo_quote_coverage(
            sim_mode="intended_realism", feed="iex", lake_root=tmp_path,
            universe=["AAA"], fold_windows=_folds(), min_coverage_pct=95.0,
        )
    assert "NBBO_NOT_AVAILABLE_ON_IEX" in str(ei.value)


def test_current_code_parity_warns_records_limitation(tmp_path: Path) -> None:
    result = check_nbbo_quote_coverage(
        sim_mode="current_code_parity", feed="iex", lake_root=tmp_path,
        universe=["AAA"], fold_windows=_folds(), min_coverage_pct=95.0,
    )
    assert result.passed is True
    assert "missing_historical_quotes" in result.limitations
