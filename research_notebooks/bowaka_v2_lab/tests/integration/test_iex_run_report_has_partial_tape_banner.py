"""IEX run reports carry the partial-tape banner at the top (audit §P1-010).

Realism remediation 2 Phase 10. Any run report whose feed is IEX MUST open
with the partial-tape caveat banner so anyone reading the report cannot miss
the IEX-vs-SIP semantic gap. The same report for SIP / non-IEX feeds must
NOT carry the banner.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bowaka_v2_lab.reports.render_run_report import build_report, render_run_report


def _write_minimum_artifacts(rd: Path, *, feed: str) -> None:
    """Write the bare minimum artifact files for ``build_report`` to render."""
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "summary.json").write_text(json.dumps({
        "run_id": "phase10_iex_banner_test",
        "feed": feed,
        "cost_stress": "base",
        "n_trades": 0,
        "win_rate": 0.0,
        "total_pnl": 0.0,
        "net_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "candidate_events_count": 0,
        "entry_decisions_count": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "broker_reject_count": 0,
        "ambiguous_bar_count": 0,
    }))
    (rd / "run_manifest.json").write_text(json.dumps({
        "run_id": "phase10_iex_banner_test",
        "strategy_version": "0.1.0",
        "created_at": "2026-05-23T00:00:00Z",
        "run_kind": "backtest",
        "feed": feed,
        "simulation": {"mode": "current_code_parity"},
    }))
    (rd / "data_quality_report.json").write_text(json.dumps({
        "schema_version": 2, "notes": "", "checks": [], "regime": "synthetic",
        "feed": feed, "passed": 0, "failed": 0, "warned": 0, "required_failures": [],
    }))
    (rd / "dataset_manifest.json").write_text(json.dumps({
        "provider": "fixture", "feed": feed, "bar_count": 0, "symbols": [],
    }))


def test_iex_run_report_has_partial_tape_banner(tmp_path: Path) -> None:
    """An IEX run report opens with the partial-tape banner."""
    rd = tmp_path / "run_iex"
    _write_minimum_artifacts(rd, feed="iex")
    body = render_run_report(rd, suitability="research_only")
    assert "**IEX caveat:**" in body, "IEX run reports must carry the IEX-caveat banner"
    assert "partial-tape" in body.lower(), "banner must reference partial-tape semantics"
    assert "RVOL_so_far" in body, "banner enumerates RVOL_so_far"
    assert "projected_full_day_rvol" in body, "banner enumerates projected_full_day_rvol"
    assert "range_expansion_so_far" in body, "banner enumerates range_expansion_so_far"
    assert "ADV" in body, "banner enumerates ADV"
    assert "not portable to SIP" in body, "banner spells out non-portability"


def test_non_iex_run_report_has_no_partial_tape_banner(tmp_path: Path) -> None:
    """SIP / other-feed reports must NOT carry the IEX banner."""
    rd = tmp_path / "run_sip"
    _write_minimum_artifacts(rd, feed="sip")
    body = render_run_report(rd, suitability="research_only")
    assert "**IEX caveat:**" not in body, (
        "non-IEX runs must not carry the IEX caveat banner"
    )


def test_iex_report_json_carries_feed_caveat(tmp_path: Path) -> None:
    """The report JSON mirrors the banner — ``feed_caveat`` + ``feed`` + banner flag."""
    rd = tmp_path / "run_iex_json"
    _write_minimum_artifacts(rd, feed="iex")
    _md, doc = build_report(rd, suitability="research_only")
    assert doc.get("feed") == "iex"
    assert doc.get("feed_caveat") == "partial_tape_features", (
        f"expected feed_caveat='partial_tape_features' for IEX, got "
        f"{doc.get('feed_caveat')!r}"
    )
    assert doc.get("iex_partial_tape_banner_present") is True


def test_non_iex_report_json_omits_feed_caveat(tmp_path: Path) -> None:
    """SIP reports do not carry the feed_caveat field."""
    rd = tmp_path / "run_sip_json"
    _write_minimum_artifacts(rd, feed="sip")
    _md, doc = build_report(rd, suitability="research_only")
    assert doc.get("feed") == "sip"
    assert "feed_caveat" not in doc, (
        "SIP reports must not carry feed_caveat (no partial-tape caveat for SIP)"
    )
    assert doc.get("iex_partial_tape_banner_present") is False


def test_iex_banner_appears_before_header_section(tmp_path: Path) -> None:
    """The banner is at the top of the report — before the ``## Header`` section."""
    rd = tmp_path / "run_iex_order"
    _write_minimum_artifacts(rd, feed="iex")
    body = render_run_report(rd, suitability="research_only")
    banner_pos = body.find("**IEX caveat:**")
    header_pos = body.find("## Header")
    assert banner_pos >= 0 and header_pos >= 0
    assert banner_pos < header_pos, (
        "IEX banner must precede the Header section in the rendered report"
    )


def test_iex_banner_does_not_trip_stub_check(tmp_path: Path) -> None:
    """The banner must not introduce a forbidden substring (no ``stub`` etc.)."""
    rd = tmp_path / "run_iex_stub"
    _write_minimum_artifacts(rd, feed="iex")
    body = render_run_report(rd, suitability="research_only")
    lowered = body.lower()
    # The banner is allowed to be present; the forbidden substrings must not.
    assert "stub" not in lowered
    assert "phase 5 fills" not in lowered
    assert "phase n fills" not in lowered
