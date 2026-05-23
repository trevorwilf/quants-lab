"""SIP-feed intended_realism must fail on a SIP-less lake (audit §11 Phase 9).

Realism remediation 2 Phase 10. The lake has no SIP partitions today; a
``feed: sip`` ``intended_realism`` study must refuse to start with a
``sip_data_absent`` failure that points at ``docs/data_lake_layout.md``.
``feed: iex`` runs must NOT touch the SIP gate (no regression).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.data.data_quality import build_sip_data_check
from bowaka_v2_lab.optuna.preflight import (
    PreflightError,
    _check_sip_data,
    run_preflight,
)


def test_sip_data_check_fails_intended_realism_on_empty_lake(tmp_path):
    """The standalone SIP check fails closed for intended_realism + missing SIP."""
    check = _check_sip_data(
        feed="sip",
        sim_mode="intended_realism",
        lake_root=tmp_path,  # empty directory — no SIP partitions
    )
    assert check.status == "fail", f"expected fail, got {check.status}"
    assert check.name == "sip_data_absent"
    assert "docs/data_lake_layout.md" in check.detail


def test_sip_data_check_warns_current_code_parity_on_empty_lake(tmp_path):
    """Same gate is a warning under current_code_parity (not a refusal)."""
    check = _check_sip_data(
        feed="sip",
        sim_mode="current_code_parity",
        lake_root=tmp_path,
    )
    assert check.status == "warn"
    assert check.name == "sip_data_absent"
    # Even as a warning, the doc pointer is still surfaced.
    assert "docs/data_lake_layout.md" in check.detail


def test_sip_data_check_passes_when_partitions_exist(tmp_path):
    """SIP-present lake passes the gate."""
    # Drop a placeholder SIP daily parquet — existence probe is content-agnostic.
    from bowaka_common.marketdata.layout import sip_daily_bars_path

    p = sip_daily_bars_path(tmp_path, "AAA")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"PAR1\x00\x00\x00\x00")
    check = _check_sip_data(
        feed="sip",
        sim_mode="intended_realism",
        lake_root=tmp_path,
    )
    assert check.status == "pass", f"expected pass, got {check.status}: {check.detail}"
    assert check.name == "sip_data_present"


def test_iex_feed_skips_sip_gate(tmp_path):
    """IEX feed runs never invoke the SIP gate — no regression."""
    check = _check_sip_data(
        feed="iex",
        sim_mode="intended_realism",
        lake_root=tmp_path,  # SIP-less lake
    )
    assert check.status == "pass"
    assert check.name == "sip_data_present"  # NOT sip_data_absent
    # Description records that SIP gate is not applicable.
    assert "SIP" in check.detail or "sip" in check.detail


def test_run_preflight_raises_on_intended_realism_sip_missing(tmp_path):
    """End-to-end: full preflight raises PreflightError when SIP is missing."""
    with pytest.raises(PreflightError, match="sip_data_absent"):
        run_preflight(
            sim_mode="intended_realism",
            allow_smoke=False,
            feed="sip",
            lake_root=tmp_path,
            raise_on_fail=True,
        )


def test_run_preflight_iex_does_not_raise_on_empty_lake(tmp_path):
    """IEX preflight against the same empty lake must NOT raise on the SIP gate."""
    # An IEX run never invokes the SIP check; the preflight passes here
    # (other gates can still warn — we only want to confirm no SIP refusal).
    result = run_preflight(
        sim_mode="current_code_parity",
        allow_smoke=False,
        feed="iex",
        lake_root=tmp_path,
        raise_on_fail=False,
    )
    sip_checks = [c for c in result.checks if c.name in ("sip_data_present", "sip_data_absent")]
    assert sip_checks, "expected a SIP check (with pass status) in preflight output"
    assert all(c.status == "pass" for c in sip_checks), (
        f"IEX preflight should pass the SIP gate, got: {sip_checks}"
    )


def test_build_sip_data_check_fail_on_missing_sip_under_intended_realism():
    """The DQ stack's SIP check fails closed for ``feed: sip`` + missing SIP."""
    check = build_sip_data_check(feed="sip", sip_partitions_present=False)
    assert check["status"] == "fail"
    assert check["name"] == "sip_data_absent"
    assert "docs/data_lake_layout.md" in check["evidence"].get("detail", "") + check["evidence"].get("remediation_pointer", "")


def test_build_sip_data_check_pass_for_iex_feed():
    """The DQ stack's SIP check passes (non-applicable) for IEX feeds."""
    check = build_sip_data_check(feed="iex", sip_partitions_present=False)
    assert check["status"] == "pass"
    assert check["name"] == "sip_data_present"


def test_dq_required_check_names_include_sip_data_absent():
    """``sip_data_absent`` is in _REQUIRED_CHECK_NAMES so it gates intended_realism."""
    from bowaka_v2_lab.data.data_quality import _REQUIRED_CHECK_NAMES

    assert "sip_data_absent" in _REQUIRED_CHECK_NAMES, (
        "sip_data_absent must be a required check so intended_realism fails closed"
    )


def test_dq_report_emits_sip_data_absent_on_sip_feed_against_empty_lake(tmp_path):
    """The full DQ report emits ``sip_data_absent: fail`` for ``feed: sip`` + empty lake."""
    from bowaka_v2_lab.data.data_quality import build_data_quality_report

    # Build a minimal lake-like layout: ingestion dir + manifest (so the lineage
    # reports regime=lake), then run the DQ report.
    (tmp_path / "_ingestion").mkdir(parents=True, exist_ok=True)
    (tmp_path / "_ingestion" / "manifest.json").write_text(
        '{"adjustment": "raw", "split_adjustment_applied": false}',
        encoding="utf-8",
    )
    cfg = {
        "market_data": {
            "feed": "sip",
            "require_adjusted_daily_bars": True,
            "require_split_adjustment": True,
        },
        "simulation": {"mode": "intended_realism", "quote_fallback_policy": "require_real"},
        "exits": {"max_hold_days": 3},
        "execution": {"halt_gate": {"enabled": False}, "max_quote_age_seconds": 15},
    }
    lineage = {
        "regime": "lake",
        "lake_root": str(tmp_path),
        "adjustment": "raw",
        "lake_manifest": {"adjustment": "raw", "split_adjustment_applied": False},
    }

    def no_daily_bars(sym, ts):
        return None

    def no_minute_bars(sym, ts):
        return None

    def no_scan_times(d):
        return []

    report = build_data_quality_report(
        cfg=cfg, lineage=lineage, requested_symbols=["AAA"],
        sessions=[dt.date(2024, 9, 3)],
        daily_bars_supplier=no_daily_bars,
        minute_bars_supplier=no_minute_bars,
        scan_times_per_session=no_scan_times,
    )
    sip_checks = [c for c in report["checks"] if c["name"] in ("sip_data_present", "sip_data_absent")]
    assert sip_checks, "expected a SIP check in the DQ report"
    assert any(
        c["name"] == "sip_data_absent" and c["status"] == "fail"
        for c in sip_checks
    ), f"expected sip_data_absent: fail in report; got: {sip_checks}"
    # And the failure rolls up into required_failures.
    assert "sip_data_absent" in report.get("required_failures", []), (
        "sip_data_absent must appear in required_failures for an intended_realism run"
    )
