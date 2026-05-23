"""Full per-fold preflight blocks the study when any fold lacks coverage.

Realism remediation 2 Phase 8 (audit §P1-006). The cheap preflight probes only
the first validation window's first few sessions; that is not enough to launch
a multi-hour study. The full per-fold preflight runs at study start over EVERY
validation + holdout window; a fold missing required coverage blocks the run.

Cached by ``(dataset_hash, fold_window, config_hash)`` so re-runs pay zero cost.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from bowaka_v2_lab.optuna.preflight import (
    FoldWindow,
    PreflightCheck,
    PreflightError,
    PreflightResult,
    _clear_full_fold_preflight_cache,
    _FULL_FOLD_PREFLIGHT_CACHE,
    run_full_fold_preflight,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Each test starts with an empty per-fold preflight cache."""
    _clear_full_fold_preflight_cache()
    yield
    _clear_full_fold_preflight_cache()


def _make_folds(n: int = 3) -> list[FoldWindow]:
    """N validation folds (one month each) + one holdout fold."""
    base = dt.date(2024, 1, 1)
    folds = []
    for i in range(n):
        s = dt.date(base.year, base.month + i, 1)
        # Last day of that month (approximated to day 28 for safety).
        e = dt.date(s.year, s.month, 28)
        folds.append(FoldWindow(
            fold_id=f"val_{s.isoformat()}", kind="validation", start=s, end=e,
        ))
    folds.append(FoldWindow(
        fold_id="holdout_2024-04-01", kind="holdout",
        start=dt.date(2024, 4, 1), end=dt.date(2024, 4, 28),
    ))
    return folds


def test_full_fold_preflight_raises_on_failing_fold(monkeypatch: Any) -> None:
    """A fold whose preflight returns ``fail`` triggers PreflightError."""

    fold_calls = {}

    def fake_probe_fold(*, cfg, fold, **_kwargs):
        # The second fold "fails" — the rest pass.
        fold_calls[fold.fold_id] = fold_calls.get(fold.fold_id, 0) + 1
        status = "fail" if fold.fold_id.startswith("val_2024-02-") else "pass"
        return PreflightResult(
            passed=(status != "fail"),
            checks=[PreflightCheck(
                name=f"fold:{fold.fold_id}:quote_coverage",
                status=status,
                detail=("quote coverage 30% < 95%" if status == "fail" else "ok"),
                evidence={"kind": fold.kind},
            )],
        )

    monkeypatch.setattr(
        "bowaka_v2_lab.optuna.preflight._probe_fold", fake_probe_fold,
    )
    with pytest.raises(PreflightError, match="full per-fold preflight"):
        run_full_fold_preflight(
            cfg={"market_data": {}, "simulation": {"mode": "intended_realism"}},
            folds=_make_folds(),
            symbols=["AAA"],
            lake_root="/tmp/whatever",
            feed="iex",
            dataset_hash="d" * 64,
            config_hash="c" * 64,
            scan_times_per_session=lambda d: [],
            min_quote_coverage_pct=95.0,
        )
    # Every fold should have been probed (the gate aggregates failures across all folds).
    assert len(fold_calls) == 4


def test_full_fold_preflight_passes_when_every_fold_passes(monkeypatch: Any) -> None:
    """A clean lake with every fold passing returns passed=True."""

    def fake_probe_fold(*, cfg, fold, **_kwargs):
        return PreflightResult(
            passed=True,
            checks=[PreflightCheck(
                name=f"fold:{fold.fold_id}:quote_coverage",
                status="pass", detail="ok", evidence={},
            )],
        )

    monkeypatch.setattr(
        "bowaka_v2_lab.optuna.preflight._probe_fold", fake_probe_fold,
    )
    result = run_full_fold_preflight(
        cfg={"market_data": {}, "simulation": {"mode": "intended_realism"}},
        folds=_make_folds(),
        symbols=["AAA"], lake_root="/tmp/whatever", feed="iex",
        dataset_hash="d" * 64, config_hash="c" * 64,
        scan_times_per_session=lambda d: [],
        min_quote_coverage_pct=95.0,
    )
    assert result.passed is True
    # One check per fold (4 folds = 4 entries in the aggregated result).
    assert len(result.checks) == 4


def test_full_fold_preflight_caches_by_dataset_and_config_hash(monkeypatch: Any) -> None:
    """Same (dataset_hash, fold_id, config_hash) re-uses the cached PreflightResult."""

    call_count = {"n": 0}

    def fake_probe_fold(*, cfg, fold, **_kwargs):
        call_count["n"] += 1
        return PreflightResult(
            passed=True,
            checks=[PreflightCheck(
                name=f"fold:{fold.fold_id}:dq", status="pass", detail="ok", evidence={},
            )],
        )

    monkeypatch.setattr(
        "bowaka_v2_lab.optuna.preflight._probe_fold", fake_probe_fold,
    )
    folds = _make_folds()
    # First call: 4 probes (one per fold).
    run_full_fold_preflight(
        cfg={"market_data": {}, "simulation": {"mode": "intended_realism"}},
        folds=folds, symbols=["AAA"], lake_root="/lake", feed="iex",
        dataset_hash="ds_X", config_hash="cfg_X",
        scan_times_per_session=lambda d: [],
        min_quote_coverage_pct=95.0,
    )
    assert call_count["n"] == 4
    # Re-run with identical inputs — every fold hits the cache.
    run_full_fold_preflight(
        cfg={"market_data": {}, "simulation": {"mode": "intended_realism"}},
        folds=folds, symbols=["AAA"], lake_root="/lake", feed="iex",
        dataset_hash="ds_X", config_hash="cfg_X",
        scan_times_per_session=lambda d: [],
        min_quote_coverage_pct=95.0,
    )
    assert call_count["n"] == 4

    # Cache miss when dataset hash changes (re-probe every fold).
    run_full_fold_preflight(
        cfg={"market_data": {}, "simulation": {"mode": "intended_realism"}},
        folds=folds, symbols=["AAA"], lake_root="/lake", feed="iex",
        dataset_hash="ds_Y", config_hash="cfg_X",
        scan_times_per_session=lambda d: [],
        min_quote_coverage_pct=95.0,
    )
    assert call_count["n"] == 8

    # Cache miss when config hash changes (re-probe every fold).
    run_full_fold_preflight(
        cfg={"market_data": {}, "simulation": {"mode": "intended_realism"}},
        folds=folds, symbols=["AAA"], lake_root="/lake", feed="iex",
        dataset_hash="ds_X", config_hash="cfg_Y",
        scan_times_per_session=lambda d: [],
        min_quote_coverage_pct=95.0,
    )
    assert call_count["n"] == 12
