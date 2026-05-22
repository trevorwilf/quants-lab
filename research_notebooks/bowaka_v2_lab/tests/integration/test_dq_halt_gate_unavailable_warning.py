"""Realism remediation 2 Phase 3 — halt-status availability gate (§P0-010).

The strategy's halt gate is enabled by default. When the lake has no
``statuses/`` partitions, halts / LULD pauses cannot be modelled. The check
``halt_data_unavailable_when_required`` then:

- ``warn`` under ``current_code_parity`` (live code fails the halt gate open —
  a documented wart),
- ``fail`` under ``intended_realism`` (fail-closed is the realism contract).
"""
from __future__ import annotations

from bowaka_v2_lab.data.dq_levels import build_quote_status_checks


def test_halt_gate_no_statuses_warn_under_parity() -> None:
    checks = build_quote_status_checks(
        quote_coverage_rows=[],
        status_partitions_available=False,
        halt_gate_enabled=True,
        simulation_mode="current_code_parity",
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["halt_data_unavailable_when_required"]["status"] == "warn"


def test_halt_gate_no_statuses_fail_under_realism() -> None:
    checks = build_quote_status_checks(
        quote_coverage_rows=[],
        status_partitions_available=False,
        halt_gate_enabled=True,
        simulation_mode="intended_realism",
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["halt_data_unavailable_when_required"]["status"] == "fail"
    ev = by_name["halt_data_unavailable_when_required"]["evidence"]
    assert "intended_realism fails closed" in ev["detail"]


def test_halt_gate_with_statuses_passes() -> None:
    checks = build_quote_status_checks(
        quote_coverage_rows=[],
        status_partitions_available=True,
        halt_gate_enabled=True,
        simulation_mode="intended_realism",
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["halt_data_unavailable_when_required"]["status"] == "pass"


def test_halt_gate_disabled_passes_even_without_statuses() -> None:
    """If the strategy's halt gate is disabled the absence of statuses is fine."""
    checks = build_quote_status_checks(
        quote_coverage_rows=[],
        status_partitions_available=False,
        halt_gate_enabled=False,
        simulation_mode="intended_realism",
    )
    by_name = {c["name"]: c for c in checks}
    assert by_name["halt_data_unavailable_when_required"]["status"] == "pass"


def test_quote_distributions_summarise_rows() -> None:
    rows = [
        {"quote_present": True, "quote_age_seconds": 2.0, "spread_bps": 10.0},
        {"quote_present": True, "quote_age_seconds": 5.0, "spread_bps": 20.0},
        {"quote_present": True, "quote_age_seconds": 12.0, "spread_bps": 30.0},
        {"quote_present": False},
    ]
    checks = build_quote_status_checks(
        quote_coverage_rows=rows,
        status_partitions_available=True,
        halt_gate_enabled=True,
        simulation_mode="intended_realism",
    )
    by_name = {c["name"]: c for c in checks}
    age = by_name["quote_age_distribution"]["evidence"]
    spr = by_name["quote_spread_distribution"]["evidence"]
    assert age["n"] == 3 and spr["n"] == 3
    assert age["max"] == 12.0
    assert spr["max"] == 30.0
