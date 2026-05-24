"""Source-manifest drift detection (audit 2026-05-23 §P1-002).

If this test fails: regenerate ``reference/actual_bowaka_v2_contract.yaml``
deliberately via ``python -m bowaka_v2_lab.reference`` AFTER reviewing the
diff. Do NOT silently match the new hashes — the manifest is the lab parity
fingerprint.
"""
from __future__ import annotations

import os

import pytest

from bowaka_v2_lab.reference import (
    assert_source_manifest_unchanged,
    contract_available,
    load_actual_contract,
    resolve_source_root,
)


pytestmark = pytest.mark.parity


def test_source_manifest_in_contract():
    """The contract must carry the source_manifest block (audit §P1-002)."""
    if not contract_available():
        pytest.xfail("frozen contract not present (see reference/README)")
    contract = load_actual_contract()
    assert "source_manifest" in contract, (
        "the v3 contract must include source_manifest; "
        "regenerate via `python -m bowaka_v2_lab.reference`"
    )
    assert "source_manifest_hash" in contract


def test_source_manifest_hash_is_rollup_of_manifest():
    """The contract's ``source_manifest_hash`` must equal the canonical-JSON
    sha256 of ``source_manifest`` — guards against the two diverging."""
    if not contract_available():
        pytest.xfail("frozen contract not present")
    from bowaka_v2_lab.reference import _hash_source_manifest

    contract = load_actual_contract()
    manifest = contract.get("source_manifest")
    if not isinstance(manifest, dict):
        pytest.xfail("legacy contract without source_manifest")
    recomputed = _hash_source_manifest(manifest)
    assert recomputed == contract["source_manifest_hash"]


def test_source_manifest_matches_frozen_contract():
    """If this fails, regenerate the contract deliberately via
    ``python -m bowaka_v2_lab.reference`` — do NOT silently match the new
    hashes. Audit 2026-05-23 §P1-002.
    """
    if not contract_available():
        pytest.xfail("frozen contract not present")
    if resolve_source_root() is None:
        pytest.xfail(
            "live source tree not located: set $BOWAKA_V2_SOURCE_ROOT or "
            "populate reference/source_strategy/scripts/ via "
            "mirror_bowaka_v2_source.ps1"
        )
    assert_source_manifest_unchanged()
