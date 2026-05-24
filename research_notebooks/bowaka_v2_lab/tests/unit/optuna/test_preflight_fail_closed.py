"""Preflight fail-closed semantics under intended_realism (audit 2026-05-23 §P0-003).

Pre-remediation the DQ/quote-coverage probes returned ``status="skipped"`` for
missing inputs and probe exceptions even under ``intended_realism``, so a study
could be launched without the data the contract requires. These tests pin the
new fail-closed semantics: a ``None`` DQ report / quote-coverage value (or a
probe exception) fails the run under ``intended_realism`` and continues to skip
under ``current_code_parity`` / ``smoke_fixture``.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest

from bowaka_v2_lab.optuna.preflight import (
    FoldWindow,
    PreflightError,
    _check_data_quality,
    _check_quote_coverage,
    _check_sip_data,
    _clear_full_fold_preflight_cache,
    _probe_fold,
    run_full_fold_preflight,
    run_preflight,
)


# --------------------------------------------------------------------------
# _check_data_quality
# --------------------------------------------------------------------------
def test_intended_realism_dq_report_none_fails():
    chk = _check_data_quality(
        dq_report=None, sim_mode="intended_realism", allow_smoke=False,
    )
    assert chk.status == "fail"
    assert "data-quality report" in chk.detail


def test_current_code_parity_dq_none_still_skipped():
    chk = _check_data_quality(
        dq_report=None, sim_mode="current_code_parity", allow_smoke=False,
    )
    assert chk.status == "skipped"


def test_smoke_fixture_dq_none_skipped():
    chk = _check_data_quality(
        dq_report=None, sim_mode="smoke_fixture", allow_smoke=True,
    )
    assert chk.status == "skipped"


# --------------------------------------------------------------------------
# _check_quote_coverage
# --------------------------------------------------------------------------
def test_intended_realism_quote_coverage_none_fails():
    chk = _check_quote_coverage(
        quote_coverage_pct=None, min_quote_coverage_pct=95.0,
        sim_mode="intended_realism", allow_smoke=False,
    )
    assert chk.status == "fail"
    assert "historical quote coverage" in chk.detail.lower() or "quote coverage" in chk.detail.lower()


def test_current_code_parity_quote_coverage_none_skipped():
    chk = _check_quote_coverage(
        quote_coverage_pct=None, min_quote_coverage_pct=95.0,
        sim_mode="current_code_parity", allow_smoke=False,
    )
    assert chk.status == "skipped"


def test_smoke_fixture_quote_coverage_none_skipped():
    chk = _check_quote_coverage(
        quote_coverage_pct=None, min_quote_coverage_pct=95.0,
        sim_mode="smoke_fixture", allow_smoke=True,
    )
    assert chk.status == "skipped"


# --------------------------------------------------------------------------
# _check_sip_data
# --------------------------------------------------------------------------
def test_intended_realism_sip_probe_none_fails():
    """SIP probe couldn't be performed under intended_realism → fail."""
    chk = _check_sip_data(
        feed="sip", sim_mode="intended_realism",
        lake_root=None, sip_partitions_present=None,
    )
    assert chk.status == "fail"


def test_current_code_parity_sip_probe_none_skipped():
    chk = _check_sip_data(
        feed="sip", sim_mode="current_code_parity",
        lake_root=None, sip_partitions_present=None,
    )
    assert chk.status == "skipped"


def test_iex_sip_probe_pass_unaffected():
    """A non-SIP feed never triggers the SIP-probe gate."""
    chk = _check_sip_data(
        feed="iex", sim_mode="intended_realism",
        lake_root=None, sip_partitions_present=None,
    )
    assert chk.status == "pass"


# --------------------------------------------------------------------------
# run_preflight end-to-end
# --------------------------------------------------------------------------
def test_run_preflight_intended_realism_no_inputs_raises():
    with pytest.raises(PreflightError):
        run_preflight(
            sim_mode="intended_realism", allow_smoke=False,
            dq_report=None, quote_coverage_pct=None,
            min_quote_coverage_pct=95.0,
        )


def test_run_preflight_current_code_parity_no_inputs_passes():
    res = run_preflight(
        sim_mode="current_code_parity", allow_smoke=False,
        dq_report=None, quote_coverage_pct=None,
        min_quote_coverage_pct=95.0,
        raise_on_fail=False,
    )
    assert res.passed is True
    # Two checks should be ``skipped``; one (simulation_mode) ``pass``.
    statuses = [c.status for c in res.checks]
    assert statuses.count("pass") >= 1
    assert statuses.count("skipped") >= 2


def test_run_preflight_smoke_with_allow_smoke_passes():
    res = run_preflight(
        sim_mode="smoke_fixture", allow_smoke=True,
        dq_report=None, quote_coverage_pct=None,
        min_quote_coverage_pct=95.0,
        raise_on_fail=False,
    )
    assert res.passed is True


# --------------------------------------------------------------------------
# _probe_fold — DQ probe exception path
# --------------------------------------------------------------------------
class _StubLake:
    pass


def test_probe_fold_dq_exception_under_intended_realism_fails(monkeypatch, tmp_path):
    """A DQ probe exception under intended_realism must mark the fold ``fail``."""
    from bowaka_v2_lab.data import data_quality as dq_mod
    from bowaka_v2_lab.data import suppliers as suppliers_mod
    _clear_full_fold_preflight_cache()

    def _raise(*args, **kwargs):
        raise RuntimeError("probe boom")

    # Force the DQ probe inside _probe_fold to raise.
    monkeypatch.setattr(dq_mod, "build_data_quality_report", _raise)

    # Stub the lake suppliers so the DQ probe is reached (the suppliers
    # construction would otherwise also raise on a non-existent lake).
    def _ok_suppliers(*a, **k):
        return (lambda *aa, **kk: None, lambda *aa, **kk: None)
    monkeypatch.setattr(suppliers_mod, "make_lake_suppliers", _ok_suppliers)
    monkeypatch.setattr(suppliers_mod, "make_quote_supplier",
                        lambda *a, **k: (lambda *aa, **kk: None))
    monkeypatch.setattr(suppliers_mod, "resolve_intraday_window_policy",
                        lambda *a, **k: None)

    cfg = {"simulation": {"mode": "intended_realism"},
           "market_data": {"feed": "iex", "shared_root": str(tmp_path)}}
    fold = FoldWindow(
        fold_id="val_2024-02-01", kind="validation",
        start=dt.date(2024, 2, 1), end=dt.date(2024, 3, 1),
    )
    result = _probe_fold(
        cfg=cfg, fold=fold, symbols=["AAA"], lake_root=str(tmp_path), feed="iex",
        scan_times_per_session=lambda d: ["10:00"],
        min_quote_coverage_pct=95.0,
    )
    assert result.passed is False
    assert any(c.status == "fail" for c in result.checks)


def test_probe_fold_dq_exception_under_parity_skipped(monkeypatch, tmp_path):
    """Same exception under current_code_parity is still skipped."""
    from bowaka_v2_lab.data import data_quality as dq_mod
    from bowaka_v2_lab.data import suppliers as suppliers_mod
    _clear_full_fold_preflight_cache()

    def _raise(*args, **kwargs):
        raise RuntimeError("probe boom")
    monkeypatch.setattr(dq_mod, "build_data_quality_report", _raise)

    def _ok_suppliers(*a, **k):
        return (lambda *aa, **kk: None, lambda *aa, **kk: None)
    monkeypatch.setattr(suppliers_mod, "make_lake_suppliers", _ok_suppliers)
    monkeypatch.setattr(suppliers_mod, "make_quote_supplier",
                        lambda *a, **k: (lambda *aa, **kk: None))
    monkeypatch.setattr(suppliers_mod, "resolve_intraday_window_policy",
                        lambda *a, **k: None)

    cfg = {"simulation": {"mode": "current_code_parity"},
           "market_data": {"feed": "iex", "shared_root": str(tmp_path)}}
    fold = FoldWindow(
        fold_id="val_2024-02-01", kind="validation",
        start=dt.date(2024, 2, 1), end=dt.date(2024, 3, 1),
    )
    result = _probe_fold(
        cfg=cfg, fold=fold, symbols=["AAA"], lake_root=str(tmp_path), feed="iex",
        scan_times_per_session=lambda d: ["10:00"],
        min_quote_coverage_pct=95.0,
    )
    assert result.passed is True
    assert any(c.status == "skipped" for c in result.checks)
