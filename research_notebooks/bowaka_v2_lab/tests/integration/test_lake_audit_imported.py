"""Realism Phase 2 — the supplied lake's research-audit parquet imports cleanly.

The bundled lake ships ``_ingestion/audits/audit_2026-05-21T054116Z_iex.parquet``
(6461 rows). This test proves :func:`build_audit_checks` reads it and produces a
non-empty check set with ``passed_research_audit`` mapped through.
"""
from __future__ import annotations

from bowaka_v2_lab.data.data_quality import build_audit_checks, find_latest_audit
from bowaka_common.marketdata.store import resolve_market_data_root


def test_supplied_lake_audit_produces_non_empty_checks(repo_root):
    lake_root = resolve_market_data_root(create=False)
    audit_path = find_latest_audit(lake_root, feed="iex")
    if audit_path is None:
        # The bundled audit must exist in the shipped lake.
        import pytest

        pytest.skip("no lake audit parquet found; supplied lake sample missing")

    checks = build_audit_checks(audit_path, feed="iex")
    assert checks, "audit parquet must yield a non-empty check set"

    names = {c["name"] for c in checks}
    # Every audit dimension is mapped to a check.
    for expected in (
        "audit_missing_sessions",
        "audit_duplicate_sessions",
        "audit_ohlc_violations",
        "audit_zero_volume_sessions",
        "audit_large_gap_flags",
        "audit_passed_research_audit",
    ):
        assert expected in names, f"missing audit check: {expected}"

    # passed_research_audit is mapped through with a real verdict.
    pra = next(c for c in checks if c["name"] == "audit_passed_research_audit")
    assert pra["status"] in ("pass", "fail")
    assert pra["evidence"]["audited_symbols"] > 0

    # Every check carries the required shape.
    for c in checks:
        assert set(c.keys()) >= {"name", "status", "count", "threshold", "source_file", "evidence"}
        assert c["status"] in ("pass", "fail", "warn")
        assert isinstance(c["count"], int)
        assert c["source_file"].startswith("audit_")


def test_audit_filtered_to_requested_symbols(repo_root):
    """Restricting to a symbol universe keeps only those symbols in the evidence."""
    lake_root = resolve_market_data_root(create=False)
    audit_path = find_latest_audit(lake_root, feed="iex")
    if audit_path is None:
        import pytest

        pytest.skip("no lake audit parquet found")

    checks = build_audit_checks(audit_path, feed="iex", requested_symbols=["A", "AA"])
    assert checks
    pra = next(c for c in checks if c["name"] == "audit_passed_research_audit")
    # Only the two requested symbols were audited.
    assert pra["evidence"]["audited_symbols"] <= 2
