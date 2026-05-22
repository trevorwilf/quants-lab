"""The frozen contract carries a top-level ``data:`` block.

Realism remediation 2 Phase 1 (audit §P0-005). The frozen contract
(``reference/actual_bowaka_v2_contract.yaml``) must include the live config's
``data:`` block — ``require_adjusted_daily_bars``, ``require_split_adjustment``,
``max_bar_age_seconds`` and ``max_quote_age_seconds`` — and ``data`` must be a
pinned :data:`reference.CONTRACT_SECTIONS` section.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab import reference


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


def test_data_is_a_contract_section() -> None:
    """``data`` is a pinned contract section and the schema version was bumped."""
    assert "data" in reference.CONTRACT_SECTIONS
    # The schema version must have been bumped past 1 when ``data`` was added.
    assert reference.CONTRACT_SCHEMA_VERSION >= 2


def test_contract_has_data_block_with_four_fields() -> None:
    contract = reference.load_actual_contract()
    assert "data" in contract, "frozen contract is missing the data: block"
    data = contract["data"]
    assert data.get("require_adjusted_daily_bars") is True
    assert data.get("require_split_adjustment") is True
    assert data.get("max_bar_age_seconds") == 90
    assert data.get("max_quote_age_seconds") == 15


def test_contract_schema_version_field_matches_constant() -> None:
    """The contract file's contract_schema_version matches the code constant."""
    contract = reference.load_actual_contract()
    assert contract.get("contract_schema_version") == reference.CONTRACT_SCHEMA_VERSION
