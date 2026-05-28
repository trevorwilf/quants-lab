"""Shared fixtures for the scan-matrix parity tests (Phase 3 / Phase 4).

The matrix build is the expensive part (tiny lake + matrix partitions), so
it is built ONCE per module via a ``tmp_path_factory``-backed fixture and
reused across the parity assertions in that module.
"""
from __future__ import annotations

import pytest

from tests.fixtures.scan_matrix_parity import (
    MatrixParityFixture,
    build_matrix_parity_fixture,
)


@pytest.fixture(scope="module")
def matrix_parity(tmp_path_factory, lab_root) -> MatrixParityFixture:
    """Module-scoped tiny-lake matrix + matched legacy supplier."""
    tmp_path = tmp_path_factory.mktemp("matrix_parity")
    return build_matrix_parity_fixture(tmp_path, lab_root)
