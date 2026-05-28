"""Phase 2 §4 — every MATRIX_SENSITIVE_PREFIXES key is refused by the guard.

Positive control: ``exits.stop_pct`` is intentionally OUTSIDE the prefix
list and must NOT raise. Tightens Phase 0's
``test_exits_outside_matrix_sensitive_prefixes.py`` by exhaustively
parametrising each prefix in the list.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.scanner.scan_matrix import (
    MATRIX_SENSITIVE_PREFIXES,
    assert_search_space_compatible_with_matrix,
)


def _override_for_prefix(prefix: str):
    """Return a search-space override dict that uses ``prefix`` literally
    (or appends a leaf key for prefixes ending in ``.``)."""
    key = prefix
    if key.endswith("."):
        key = key + "bucket_edges"
    # Use an int spec for keys that are clearly int-typed; uniform otherwise.
    int_hints = ("scanner_start", "scanner_end", "scan_interval_seconds")
    if any(h in key for h in int_hints):
        return {key: ("int", 1, 60)}
    return {key: ("uniform", 0.0, 1.0)}


@pytest.mark.parametrize("prefix", MATRIX_SENSITIVE_PREFIXES)
def test_every_sensitive_prefix_is_refused(prefix: str) -> None:
    """A search-space override on any sensitive prefix must raise."""
    override = _override_for_prefix(prefix)
    with pytest.raises(OptunaStudyInvalidError):
        assert_search_space_compatible_with_matrix(override)


def test_exits_stop_pct_is_accepted() -> None:
    """Positive control: exits.stop_pct is NOT a sensitive prefix."""
    # No raise — Phase 0 acceptance: exits run post-scanner.
    assert_search_space_compatible_with_matrix(
        {"exits.stop_pct": ("uniform", 0.01, 0.20)}
    )
