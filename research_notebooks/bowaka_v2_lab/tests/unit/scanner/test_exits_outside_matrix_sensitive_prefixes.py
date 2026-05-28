"""Phase 0 §6 — ``exits.*`` is intentionally outside MATRIX_SENSITIVE_PREFIXES.

Exits run post-scanner, so tuning ``exits.stop_pct`` (or any other
``exits.*`` knob) does not invalidate the precomputed scan matrix.

This is the positive-control complement to
``test_scan_matrix_refuses_matrix_sensitive_search_space.py``: that test
asserts every sensitive prefix raises; this test asserts ``exits.stop_pct``
does NOT raise and is not accidentally added to the sensitive prefix list.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_matrix import (
    MATRIX_SENSITIVE_PREFIXES,
    assert_search_space_compatible_with_matrix,
)


def test_no_matrix_sensitive_prefix_targets_exits_block() -> None:
    """Defense in depth: no entry in MATRIX_SENSITIVE_PREFIXES touches exits."""
    bad = [p for p in MATRIX_SENSITIVE_PREFIXES if p.startswith("exits.")]
    assert bad == [], (
        f"MATRIX_SENSITIVE_PREFIXES contains exits-prefixed entries: {bad!r}. "
        f"Exits run AFTER the scanner emits a candidate, so an exits.* tuning "
        f"knob does not invalidate the precomputed matrix. Move the entry "
        f"out of MATRIX_SENSITIVE_PREFIXES."
    )
    # The list must also not contain ``exits.stop_pct`` exactly.
    assert "exits.stop_pct" not in MATRIX_SENSITIVE_PREFIXES


def test_assert_compatible_does_not_raise_on_stop_pct_override() -> None:
    """Search-space override on ``exits.stop_pct`` must be accepted by the guard."""
    # Should NOT raise — this is the explicit Phase 0 acceptance criterion.
    assert_search_space_compatible_with_matrix(
        {"exits.stop_pct": ("uniform", 0.01, 0.20)}
    )
